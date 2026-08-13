"""Phase 1 dev graph — linear pipeline with two human interrupts.

    intake -> repo_explorer -> spec_architect -> [HUMAN: spec] -> coder
              -> integration_runner -> [HUMAN: PR] -> pr_publisher
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from dev_graph.checkpointer import get_checkpointer
from dev_graph.nodes.coder import run as coder
from dev_graph.nodes.human_gate import pr_gate, spec_gate
from dev_graph.nodes.intake import run as intake
from dev_graph.nodes.integration_runner import run as integration_runner
from dev_graph.nodes.pr_publisher import run as pr_publisher
from dev_graph.nodes.repo_explorer import run as repo_explorer
from dev_graph.nodes.spec_architect import run as spec_architect
from dev_graph.state import DevState


def build_graph():
    g = StateGraph(DevState)

    g.add_node("intake", intake)
    g.add_node("repo_explorer", repo_explorer)
    g.add_node("spec_architect", spec_architect)
    g.add_node("human_spec_gate", spec_gate)
    g.add_node("coder", coder)
    g.add_node("integration_runner", integration_runner)
    g.add_node("human_pr_gate", pr_gate)
    g.add_node("pr_publisher", pr_publisher)

    g.add_edge(START, "intake")
    g.add_edge("intake", "repo_explorer")
    g.add_edge("repo_explorer", "spec_architect")
    g.add_edge("spec_architect", "human_spec_gate")

    g.add_conditional_edges(
        "human_spec_gate",
        _after_spec,
        {"coder": "coder", "spec_architect": "spec_architect"},
    )

    g.add_edge("coder", "integration_runner")

    g.add_conditional_edges(
        "integration_runner",
        _after_tests,
        {"human_pr_gate": "human_pr_gate", "coder": "coder"},
    )

    g.add_conditional_edges(
        "human_pr_gate",
        _after_pr_gate,
        {"pr_publisher": "pr_publisher", "coder": "coder"},
    )

    g.add_edge("pr_publisher", END)

    return g.compile(checkpointer=get_checkpointer())


def _after_spec(state: DevState) -> str:
    return "coder" if state.get("spec_approved") else "spec_architect"


def _after_tests(state: DevState) -> str:
    return "human_pr_gate" if state.get("test_results", {}).get("passed") else "coder"


def _after_pr_gate(state: DevState) -> str:
    return "pr_publisher" if state.get("pr_approved") else "coder"
