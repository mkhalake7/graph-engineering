"""Repo Explorer — read-only scan of the workspace to build compact context.

Extracts likely keywords from the task text and grabs file paths whose name or
contents match. Kept intentionally simple: pure stdlib, no ripgrep dependency.
Downstream nodes (Spec Architect, Coder) can look deeper on their own.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

from dev_graph.state import DevState, TraceEntry

_IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".mypy_cache", ".pytest_cache"}
_MAX_FILE_BYTES = 500_000
_MAX_MATCHES = 40

_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "to", "and", "or", "but", "for", "with",
    "by", "at", "add", "fix", "update", "change", "new", "this", "that", "from",
    "into", "when", "how", "make", "use", "using", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "can", "could", "may", "might", "must",
}


def run(state: DevState) -> dict:
    start = time.time()
    workspace = Path(os.environ.get("DEV_GRAPH_WORKSPACE", ".")).resolve()

    keywords = _extract_keywords(state["task_text"])
    matches: list[str] = []
    if workspace.exists():
        for path in workspace.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _IGNORE_DIRS for part in path.parts):
                continue
            try:
                if path.stat().st_size > _MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            rel = path.relative_to(workspace)
            rel_str = str(rel)
            # Name match is cheap — try it first.
            hit = any(k.lower() in rel_str.lower() for k in keywords)
            if not hit:
                try:
                    text = path.read_text(errors="ignore")
                except Exception:
                    continue
                hit = any(k.lower() in text.lower() for k in keywords)
            if hit:
                matches.append(rel_str)
                if len(matches) >= _MAX_MATCHES:
                    break

    ctx = {
        "workspace": str(workspace),
        "keywords": keywords,
        "candidate_files": matches,
    }
    duration = int((time.time() - start) * 1000)
    return {
        "repo_context": ctx,
        "trace": [TraceEntry(node="repo_explorer", duration_ms=duration,
                             summary=f"{len(matches)} candidate files, {len(keywords)} keywords")],
    }


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text)
    seen: set[str] = set()
    kws: list[str] = []
    for w in words:
        wl = w.lower()
        if wl in _STOPWORDS or wl in seen:
            continue
        seen.add(wl)
        kws.append(w)
    return kws[:15]
