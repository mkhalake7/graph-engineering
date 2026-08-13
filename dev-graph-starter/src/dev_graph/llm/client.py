"""Thin wrapper around the Anthropic SDK.

Lazily constructs a single client. Reads ANTHROPIC_API_KEY from the environment.
`model("sonnet" | "opus" | "haiku")` maps short names to the current model IDs.
"""

from __future__ import annotations

import os
from functools import lru_cache

from anthropic import Anthropic

DEFAULT_MODELS = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
}


@lru_cache(maxsize=1)
def client() -> Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.template to .env and fill it in, "
            "or export the variable in your shell."
        )
    return Anthropic(api_key=key)


def model(name: str) -> str:
    """Accepts a short name ('sonnet') or a full model id — returns the full id."""
    return DEFAULT_MODELS.get(name, name)
