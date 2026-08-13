"""CLI: start a new dev-graph run.

The graph runs until the first human interrupt (spec_gate), saves state via
the SQLite checkpointer, and prints the interrupt payload + a resume hint.

Examples:
    python scripts/run_task.py --task "Add preferred_topics to enrichment"
    python scripts/run_task.py --task "..." --task-id my-feature-001
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    ap = argparse.ArgumentParser(description="Start a dev-graph run.")
    ap.add_argument("--task", required=True, help="Task description in plain English.")
    ap.add_argument("--task-id", default=None, help="Stable id; defaults to a random one.")
    ap.add_argument("--trigger", default="cli",
                    choices=["ticket", "slack", "cron", "cli"])
    args = ap.parse_args()

    # Deferred import so `--help` works without the env var set.
    from dev_graph.graph import build_graph

    task_id = args.task_id or f"task-{uuid.uuid4().hex[:8]}"
    thread_id = task_id

    app = build_graph()
    initial = {
        "task_id": task_id,
        "task_text": args.task,
        "trigger": args.trigger,
        "artifacts": [],
        "trace": [],
    }
    config = {"configurable": {"thread_id": thread_id}}

    print(f"[dev-graph] starting task_id={task_id} thread_id={thread_id}")
    try:
        for event in app.stream(initial, config, stream_mode="values"):
            _print_latest_trace(event)
    except Exception as e:
        print(f"[dev-graph] error: {type(e).__name__}: {e}", file=sys.stderr)
        raise

    state = app.get_state(config)
    if state.next:
        print(f"\n[dev-graph] PAUSED at: {state.next}")
        _print_pending_interrupt(state)
        print(
            f"[dev-graph] resume with:\n"
            f"  python scripts/resume.py {thread_id} --approve\n"
            f"  python scripts/resume.py {thread_id} --reject --feedback \"...\"\n"
            f"  python scripts/resume.py {thread_id} --approve --spec-edits '{{\"risk\":\"high\"}}'"
        )
    else:
        print("\n[dev-graph] DONE.")
        _print_final(state)


def _print_latest_trace(event: dict) -> None:
    trace = event.get("trace") or []
    if not trace:
        return
    latest = trace[-1]
    node = getattr(latest, "node", None) or (latest.get("node") if isinstance(latest, dict) else "?")
    summary = getattr(latest, "summary", "") or (latest.get("summary", "") if isinstance(latest, dict) else "")
    ms = getattr(latest, "duration_ms", 0) or (latest.get("duration_ms", 0) if isinstance(latest, dict) else 0)
    print(f"  · {node} ({ms}ms) — {summary}")


def _print_pending_interrupt(state) -> None:
    for task in state.tasks:
        for intr in task.interrupts:
            print("\n[interrupt payload]")
            print(json.dumps(intr.value, indent=2, default=str))


def _print_final(state) -> None:
    values = state.values or {}
    pr = values.get("pr_url")
    if pr:
        print(f"PR: {pr}")


if __name__ == "__main__":
    main()
