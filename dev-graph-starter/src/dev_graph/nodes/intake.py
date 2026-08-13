"""Intake — normalize the incoming task into a canonical form."""

from __future__ import annotations

from dev_graph.state import DevState, TraceEntry


def run(state: DevState) -> dict:
    text = (state.get("task_text") or "").strip()
    if not text:
        raise ValueError("intake: task_text is empty")
    return {
        "task_text": text,
        "trace": [TraceEntry(node="intake", summary=f"normalized ({len(text)} chars)")],
    }
