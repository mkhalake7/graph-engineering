"""Offline smoke tests. No network, no LLM calls. Run with `pytest -q`."""

from __future__ import annotations

import os


def test_state_spec_roundtrip():
    from dev_graph.state import Spec
    s = Spec(
        summary="Add preferred_topics",
        acceptance_criteria=["AC1", "AC2"],
        affected_components=["enrichment_worker", "enrichment_prompt"],
        risk="medium",
    )
    assert s.risk == "medium"
    assert s.affected_components == ["enrichment_worker", "enrichment_prompt"]


def test_graph_builds():
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-placeholder")
    from dev_graph.graph import build_graph
    app = build_graph()
    assert app is not None


def test_agent_tools_reject_path_traversal(tmp_path):
    from dev_graph.agent_tools import execute
    ws = tmp_path
    (ws / "ok.txt").write_text("hi")

    # Reading a normal file works.
    out = execute("read_file", {"path": "ok.txt"}, ws)
    assert out == "hi"

    # Traversal is rejected.
    out = execute("read_file", {"path": "../etc/passwd"}, ws)
    assert out.startswith("tool error") or "escapes workspace" in out


def test_repo_explorer_extracts_keywords():
    from dev_graph.nodes.repo_explorer import _extract_keywords
    kws = _extract_keywords("Add preferred_topics field to enrichment worker")
    # Stopwords filtered, order preserved, deduped.
    assert "preferred_topics" in kws
    assert "enrichment" in kws
    assert "worker" in kws
    assert "the" not in kws
    assert "to" not in kws
