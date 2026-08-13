"""SQLite-backed checkpointer for durable graph state across human interrupts."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def _db_path() -> Path:
    override = os.environ.get("DEV_GRAPH_CHECKPOINT_DB")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".dev_graph" / "checkpoints.sqlite"


def get_checkpointer() -> SqliteSaver:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver
