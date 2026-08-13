"""Typed state that flows through every node in the dev graph.

TypedDict is used at the outer boundary (LangGraph requires it) with `Annotated`
reducers so that list fields (artifacts, trace) accumulate across nodes instead
of overwriting each other. Nested values are Pydantic models — that gives us
validation at the Spec Architect / Coder boundaries where it matters most.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

AffectedComponent = Literal[
    "glue_job",             # upstream batch, writes base profile to S3
    "enrichment_worker",    # S3 -> LLM -> OpenSearch (write path)
    "recommend_api",        # /recommend endpoint (read path)
    "enrichment_prompt",    # LLM prompt for user profile enrichment
    "reranker_prompt",      # LLM prompt for the reranker
    "user_profile_index",   # OpenSearch mapping for enriched profiles
    "opensearch_query",     # kNN / filter queries
]


class Spec(BaseModel):
    summary: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    affected_components: list[AffectedComponent] = Field(default_factory=list)
    risk: Literal["low", "medium", "high"] = "low"
    notes: str = ""


class Artifact(BaseModel):
    path: str
    kind: Literal["code", "prompt", "test", "mapping", "migration", "doc"]
    author_node: str
    summary: str = ""


class TraceEntry(BaseModel):
    node: str
    duration_ms: int = 0
    summary: str = ""


class DevState(TypedDict, total=False):
    # --- inputs ---
    task_id: str
    task_text: str
    trigger: Literal["ticket", "slack", "cron", "cli"]

    # --- produced by early nodes ---
    repo_context: dict
    spec: Spec
    spec_approved: bool
    spec_feedback: str

    # --- coder output ---
    artifacts: Annotated[list[Artifact], add]
    workspace_path: str  # git worktree the coder wrote into

    # --- verification ---
    test_results: dict   # {"passed": bool, "output": str}

    # --- PR gate + publisher ---
    pr_url: str
    pr_approved: bool
    pr_feedback: str

    # --- observability ---
    trace: Annotated[list[TraceEntry], add]
