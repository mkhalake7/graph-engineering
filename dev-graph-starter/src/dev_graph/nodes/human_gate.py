"""Human-in-the-loop interrupts.

`spec_gate` pauses the graph after the Spec Architect. The engineer approves,
rejects (with feedback that loops back to the architect), or approves with
inline Spec field edits.

`pr_gate` pauses after the Integration Runner passes. The engineer reviews the
artifacts + test output and approves the PR to be published, or rejects to
loop the Coder for another attempt.

Both use LangGraph's `interrupt()` — the checkpointer freezes state and the
graph resumes only via a `Command(resume=...)` payload.
"""

from __future__ import annotations

from langgraph.types import interrupt

from dev_graph.state import DevState, Spec, TraceEntry


def spec_gate(state: DevState) -> dict:
    spec = state["spec"]
    payload = {
        "kind": "spec_review",
        "task_id": state.get("task_id"),
        "spec": spec.model_dump() if hasattr(spec, "model_dump") else spec,
    }
    decision = interrupt(payload)
    # Expected decision shape:
    #   {"approve": bool, "feedback": str, "spec_edits": Optional[dict]}
    approved = bool(decision.get("approve"))
    out: dict = {
        "spec_approved": approved,
        "spec_feedback": decision.get("feedback", ""),
        "trace": [TraceEntry(
            node="human_spec_gate",
            summary=("approved" if approved else "rejected") + (
                f": {decision.get('feedback', '')[:60]}" if decision.get("feedback") else ""
            ),
        )],
    }
    if approved and decision.get("spec_edits"):
        merged = spec.model_dump()
        merged.update(decision["spec_edits"])
        out["spec"] = Spec(**merged)
    return out


def pr_gate(state: DevState) -> dict:
    artifacts = state.get("artifacts", [])
    payload = {
        "kind": "pr_review",
        "task_id": state.get("task_id"),
        "artifacts": [a.model_dump() if hasattr(a, "model_dump") else a for a in artifacts],
        "test_results": state.get("test_results", {}),
    }
    decision = interrupt(payload)
    approved = bool(decision.get("approve"))
    return {
        "pr_approved": approved,
        "pr_feedback": decision.get("feedback", ""),
        "trace": [TraceEntry(
            node="human_pr_gate",
            summary="approved" if approved else "changes requested",
        )],
    }
