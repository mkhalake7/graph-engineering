"""Integration Runner — deterministic verifier.

Runs pytest + ruff in the Coder's worktree. Missing tools are treated as
'skipped' (not failures). Pytest exit code 5 (no tests collected) is also
treated as OK.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from dev_graph.state import DevState, TraceEntry

_TIMEOUT = 300


def run(state: DevState) -> dict:
    start = time.time()
    ws = Path(state.get("workspace_path") or ".").resolve()
    passed = True
    parts: list[str] = []

    checks = [
        ("pytest", ["pytest", "-x", "-q"]),
        ("ruff", ["ruff", "check", "."]),
    ]

    for name, cmd in checks:
        try:
            r = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=_TIMEOUT)
        except FileNotFoundError:
            parts.append(f"--- {name} (skipped: not installed) ---")
            continue
        except subprocess.TimeoutExpired:
            parts.append(f"--- {name} (TIMEOUT after {_TIMEOUT}s) ---")
            passed = False
            continue

        # pytest exit 5 = no tests collected — treat as OK.
        if name == "pytest" and r.returncode == 5:
            parts.append(f"--- {name} (no tests collected — ok) ---")
            continue

        parts.append(
            f"--- {name} (exit={r.returncode}) ---\n"
            f"{_truncate(r.stdout)}\n"
            f"{_truncate(r.stderr)}"
        )
        if r.returncode != 0:
            passed = False

    duration = int((time.time() - start) * 1000)
    return {
        "test_results": {"passed": passed, "output": "\n".join(parts)},
        "trace": [TraceEntry(
            node="integration_runner",
            duration_ms=duration,
            summary="PASS" if passed else "FAIL",
        )],
    }


def _truncate(s: str, limit: int = 4000) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n... (truncated, {len(s) - limit} more chars)"
