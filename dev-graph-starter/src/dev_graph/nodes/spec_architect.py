"""Spec Architect — turns the task + repo context into a concrete Spec.

Calls Claude Opus and expects a JSON object matching the Spec schema.
If the previous attempt was rejected, includes the feedback in the prompt.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from dev_graph.llm.client import client, model
from dev_graph.state import DevState, Spec, TraceEntry

_PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "spec_architect.md"


def run(state: DevState) -> dict:
    start = time.time()
    system = _PROMPT_PATH.read_text()
    user = (
        f"# Task\n{state['task_text']}\n\n"
        f"# Repo context\n{json.dumps(state.get('repo_context', {}), indent=2)}\n\n"
        f"# Feedback from previous attempt (if any)\n"
        f"{state.get('spec_feedback', '(none)')}\n"
    )
    resp = client().messages.create(
        model=model("opus"),
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = _first_text(resp)
    payload = _extract_json(text)
    spec = Spec(**payload)
    duration = int((time.time() - start) * 1000)
    return {
        "spec": spec,
        "spec_approved": False,
        "trace": [TraceEntry(node="spec_architect", duration_ms=duration,
                             summary=spec.summary[:80])],
    }


def _first_text(resp) -> str:
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


def _extract_json(s: str) -> dict:
    # Prefer a fenced ```json ... ``` block.
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # Fallback: find the first balanced { ... } object.
    start = s.find("{")
    if start == -1:
        raise ValueError(f"no JSON found in Spec Architect response:\n{s[:500]}")
    depth = 0
    for i, ch in enumerate(s[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(s[start:i + 1])
    raise ValueError(f"unbalanced JSON in Spec Architect response:\n{s[:500]}")
