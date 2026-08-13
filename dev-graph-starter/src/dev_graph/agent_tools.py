"""Tool definitions for the Coder agent's tool-use loop.

All tools operate within a sandboxed workspace directory. Every path is
validated to stay under the workspace root — no traversal out of it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "read_file",
        "description": "Read a text file from the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path relative to workspace root."}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write full contents to a file in the workspace. Overwrites any existing file. Parent directories are created if missing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "List files (recursively) under a directory relative to the workspace. Returns newline-separated relative paths.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "default": "."}},
        },
    },
    {
        "name": "run_bash",
        "description": "Run a shell command in the workspace. Use for grep, tests, small utilities. Timeout: 120s.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]

_IGNORE = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
_MAX_READ_BYTES = 200_000
_MAX_LIST_ENTRIES = 500


def _safe(workspace: Path, rel: str) -> Path:
    p = (workspace / rel).resolve()
    ws = workspace.resolve()
    if not (p == ws or ws in p.parents):
        raise ValueError(f"path escapes workspace: {rel}")
    return p


def execute(tool_name: str, args: dict, workspace: Path) -> str:
    try:
        if tool_name == "read_file":
            p = _safe(workspace, args["path"])
            if not p.exists():
                return f"error: file not found: {args['path']}"
            data = p.read_bytes()[:_MAX_READ_BYTES]
            return data.decode("utf-8", errors="replace")

        if tool_name == "write_file":
            p = _safe(workspace, args["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"])
            return f"ok: wrote {len(args['content'])} bytes to {args['path']}"

        if tool_name == "list_files":
            base = _safe(workspace, args.get("path", "."))
            if not base.exists():
                return f"error: not found: {args.get('path', '.')}"
            entries: list[str] = []
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                if any(part in _IGNORE for part in path.parts):
                    continue
                entries.append(str(path.relative_to(workspace)))
                if len(entries) >= _MAX_LIST_ENTRIES:
                    entries.append(f"... (truncated at {_MAX_LIST_ENTRIES})")
                    break
            entries.sort()
            return "\n".join(entries) if entries else "(empty)"

        if tool_name == "run_bash":
            r = subprocess.run(
                args["command"],
                cwd=workspace,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return f"exit={r.returncode}\n--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"

        return f"error: unknown tool: {tool_name}"

    except subprocess.TimeoutExpired:
        return "error: command timed out (120s)"
    except Exception as e:
        return f"tool error: {type(e).__name__}: {e}"
