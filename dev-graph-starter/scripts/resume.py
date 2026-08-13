"""CLI: resume a paused dev-graph run with human approval/rejection.

Examples:
    python scripts/resume.py task-abc123 --approve
    python scripts/resume.py task-abc123 --reject --feedback "AC5 too weak"
    python scripts/resume.py task-abc123 --approve --spec-edits '{"risk":"high"}'
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv
from langgraph.types import Command


def main() -> None:
    load_dotenv()

    ap = argparse.ArgumentParser(description="Resume a paused dev-graph run.")
    ap.add_argument("thread_id")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--approve", action="store_true")
    grp.add_argument("--reject", action="store_true")
    ap.add_argument("--feedback", default="", help="Free-text feedback to the previous node.")
    ap.add_argument("--spec-edits", default=None,
                    help='JSON string of Spec fields to override, e.g. \'{"risk":"high"}\'')
    args = ap.parse_args()

    from dev_graph.graph import build_graph

    resume_value: dict = {
        "approve": bool(args.approve),
        "feedback": args.feedback,
    }
    if args.spec_edits:
        try:
            resume_value["spec_edits"] = json.loads(args.spec_edits)
        except json.JSONDecodeError as e:
            print(f"[dev-graph] --spec-edits is not valid JSON: {e}", file=sys.stderr)
            sys.exit(2)

    app = build_graph()
    config = {"configurable": {"thread_id": args.thread_id}}

    print(f"[dev-graph] resuming thread_id={args.thread_id} approve={args.approve}")

    try:
        for event in app.stream(Command(resume=resume_value), config, stream_mode="values"):
            _print_latest_trace(event)
    except Exception as e:
        print(f"[dev-graph] error: {type(e).__name__}: {e}", file=sys.stderr)
        raise

    state = app.get_state(config)
    if state.next:
        print(f"\n[dev-graph] PAUSED at: {state.next}")
        _print_pending_interrupt(state)
        print(f"[dev-graph] resume with: python scripts/resume.py {args.thread_id} --approve")
    else:
        print("\n[dev-graph] DONE.")
        pr = (state.values or {}).get("pr_url")
        if pr:
            print(f"PR: {pr}")


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


if __name__ == "__main__":
    main()
