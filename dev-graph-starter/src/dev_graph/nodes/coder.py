"""Coder — Claude Sonnet tool-use loop against a git worktree of the workspace.

Isolation:
- A per-task git worktree is created under DEV_GRAPH_WORKTREES (default:
  ~/.dev_graph/worktrees/<task_id>), branched from the workspace HEAD.
- The Coder can only read/write inside that worktree.
- Your main working tree is never modified.

Requires the workspace to be a git repo. If it is not, the node raises with a
clear message.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

from dev_graph import agent_tools
from dev_graph.llm.client import client, model
from dev_graph.state import Artifact, DevState, TraceEntry

_PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "coder.md"
_MAX_TURNS = 25
_MAX_TOKENS_PER_TURN = 8000


def run(state: DevState) -> dict:
    start = time.time()
    workspace = _ensure_worktree(state["task_id"])
    system = _PROMPT_PATH.read_text()
    spec = state["spec"]

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": _build_user_message(state, spec)}
    ]
    artifacts: list[Artifact] = []
    written: set[str] = set()
    turn = 0

    for turn in range(_MAX_TURNS):
        resp = client().messages.create(
            model=model("sonnet"),
            max_tokens=_MAX_TOKENS_PER_TURN,
            system=system,
            tools=agent_tools.TOOL_SCHEMAS,
            messages=messages,
        )
        # Append the assistant message with its full content blocks.
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            break

        # Execute any tool calls in this turn.
        tool_results: list[dict[str, Any]] = []
        for block in resp.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            result = agent_tools.execute(block.name, dict(block.input), workspace)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
            if block.name == "write_file":
                path = block.input.get("path", "")
                if path and path not in written:
                    written.add(path)
                    artifacts.append(Artifact(
                        path=path,
                        kind=_guess_kind(path),
                        author_node="coder",
                        summary=f"turn {turn}: wrote {path}",
                    ))

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            # No tool calls and not end_turn — model produced only text. Stop.
            break

    duration = int((time.time() - start) * 1000)
    return {
        "artifacts": artifacts,
        "workspace_path": str(workspace),
        "trace": [TraceEntry(
            node="coder",
            duration_ms=duration,
            summary=f"{len(artifacts)} files written, {turn + 1} turn(s)",
        )],
    }


def _build_user_message(state: DevState, spec) -> str:
    ac = "\n".join(f"  - {a}" for a in spec.acceptance_criteria)
    return (
        f"# Task\n{state['task_text']}\n\n"
        f"# Spec\n"
        f"Summary: {spec.summary}\n"
        f"Acceptance criteria:\n{ac}\n"
        f"Affected components: {', '.join(spec.affected_components)}\n"
        f"Risk: {spec.risk}\n"
        f"Notes: {spec.notes or '(none)'}\n\n"
        f"# Workspace\n"
        f"You are inside a git worktree at the workspace root. Use the tools "
        f"(read_file, write_file, list_files, run_bash) to make the minimum "
        f"changes required to satisfy the spec. When you are done, respond with "
        f"a short summary and stop."
    )


def _ensure_worktree(task_id: str) -> Path:
    base = Path(os.environ.get("DEV_GRAPH_WORKSPACE", ".")).resolve()
    if not base.exists():
        raise RuntimeError(f"DEV_GRAPH_WORKSPACE does not exist: {base}")

    worktrees_dir = Path(os.environ.get(
        "DEV_GRAPH_WORKTREES",
        str(Path.home() / ".dev_graph" / "worktrees"),
    )).expanduser().resolve()
    worktrees_dir.mkdir(parents=True, exist_ok=True)
    wt = worktrees_dir / task_id

    if wt.exists():
        return wt

    # Confirm the base is a git repo before trying to create a worktree.
    r = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=base, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"DEV_GRAPH_WORKSPACE is not a git repo: {base}\n"
            f"Initialize it with `git init` or point DEV_GRAPH_WORKSPACE at your real repo."
        )

    subprocess.run(
        ["git", "worktree", "add", "-B", f"devgraph/{task_id}", str(wt), "HEAD"],
        cwd=base, check=True, capture_output=True, text=True,
    )
    return wt


def _guess_kind(path: str) -> str:
    p = path.lower()
    if p.endswith(".md") and "prompt" in p:
        return "prompt"
    if p.endswith(".json") and "mapping" in p:
        return "mapping"
    if "test" in p and p.endswith((".py", ".ts", ".js")):
        return "test"
    if "migration" in p or "migrations/" in p:
        return "migration"
    if p.endswith((".md", ".rst", ".txt")):
        return "doc"
    return "code"
