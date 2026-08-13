# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Two shippable kits plus two HTML research docs — all describing **the same graph-engineered dev workflow** for building a recommendation backend, expressed in two different execution environments.

- `dev-graph-starter/` — runnable LangGraph Python pipeline (Phase 1 linear graph, SQLite checkpointer, two human interrupts, tool-use Coder loop). Requires an Anthropic API key.
- `dev-graph-copilot-edition/` — same graph shape distilled into VS Code Copilot Chat custom chat modes + prompt files. Human drives every step; no API keys.
- `index.html`, `recommendation-dev-graph.html` — the design/research docs the kits implement.

The two kits are **mirrors of one concept**. Concept-level changes (roles, vocabulary, system architecture) need to be reflected in both.

## The target system the kits build

Both kits are designed for a document recommendation backend with two runtime paths:

- **Write path**: Glue job → S3 base user profile → backend **enrichment worker** (reads S3, fetches recent-read docs from an OpenSearch docs index, calls an LLM enrichment prompt) → OpenSearch **user profile index** (distinct from the docs index).
- **Read path**: `/recommend` API → parallel fetch from OpenSearch (enriched profile + anchor doc + candidates) → ML team's recommendation library → LLM reranker → response.

Details in `recommendation-dev-graph.html`.

## Development commands

Only `dev-graph-starter/` has runnable code and tests. Everything else is HTML/Markdown.

```bash
cd dev-graph-starter

# Setup — requires Python 3.11+. This machine uses uv to manage 3.13.
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

# Smoke tests (offline — no network, no LLM calls)
.venv/bin/pytest tests/ -v

# Single test
.venv/bin/pytest tests/test_smoke.py::test_state_spec_roundtrip -v

# Lint
.venv/bin/ruff check src/ scripts/ tests/

# Build a git bundle for transport (in either kit's root)
./bundle.sh
```

## Cross-kit consistency — the load-bearing rule

The `affected_components` enum is the shared vocabulary that binds both kits and the design doc. **Source of truth: `dev-graph-starter/src/dev_graph/state.py` (`AffectedComponent` Literal)**. If you add, rename, or remove a value, update every mirror:

- `dev-graph-starter/prompts/spec_architect.md`
- `dev-graph-starter/prompts/coder.md` (component-specific reminders)
- `dev-graph-copilot-edition/.github/copilot-instructions.md` (Component vocabulary section)
- `dev-graph-copilot-edition/.github/chatmodes/spec-architect.chatmode.md`
- `dev-graph-copilot-edition/.github/chatmodes/coder.chatmode.md`
- `dev-graph-copilot-edition/.github/prompts/review-spec.prompt.md` (checklist item 4)
- `recommendation-dev-graph.html` (state schema section + routing example)

The **write-path/read-path system context** (Glue → S3 → enrichment worker → OpenSearch; `/recommend` API → ML lib → reranker) appears in the same set of files. Keep the four-file group in sync: design doc, copilot-instructions, spec-architect chatmode, coder chatmode.

Each **node role** (Spec Architect, Coder, Grader, LLM Prompt Engineer) has two implementations of the same logical prompt:

- Runtime kit: `dev-graph-starter/prompts/<role>.md`
- Copilot kit: `dev-graph-copilot-edition/.github/chatmodes/<role>.chatmode.md` (adds VS Code frontmatter with a `tools:` array, and a stronger emphasis on adaptive/pause behavior)

When editing a role, treat both as one prompt in two dialects.

## The PAUSE contract (Copilot edition)

The Copilot chat modes require read-before-write, match-local-conventions, and emit a `PAUSE:` block instead of proceeding when reality contradicts the spec (six specific triggers). This behavior is specified in **four files that must stay aligned**:

- `dev-graph-copilot-edition/.github/copilot-instructions.md` — "Discover before you write — and adapt when you discover" section
- `dev-graph-copilot-edition/.github/chatmodes/coder.chatmode.md` — "Adapt on the go — pause when reality contradicts the Spec"
- `dev-graph-copilot-edition/.github/chatmodes/spec-architect.chatmode.md` — "Ground the spec in the actual code"
- `dev-graph-copilot-edition/HOW-TO-VSCODE.html` — section 08

Weakening the language in one file without the others creates behavior drift.

## Model routing convention

Defined once in `dev-graph-starter/src/dev_graph/llm/client.py` (`DEFAULT_MODELS`). Same routing is recommended (as guidance, not enforced) in the Copilot edition's HTML doc:

- Judgment (Spec Architect, Grader, LLM Prompt Engineer) → Opus-class
- Coding (Coder) → Sonnet-class
- Cheap read-only (Repo Explorer) → Haiku-class

## Test philosophy

The smoke tests in `dev-graph-starter/tests/test_smoke.py` are strictly offline: no network, no LLM calls, no writes outside `tmp_path`. They verify state-schema roundtrip, graph compilation with the SQLite checkpointer, the Coder's file-tool sandbox actually blocks path traversal (`agent_tools._safe`), and keyword extraction correctness.

If you add nodes, add a compile-time wiring test — do not add tests that call live LLMs.

## State reducer pattern

`DevState` in `dev-graph-starter/src/dev_graph/state.py` uses `Annotated[list[X], operator.add]` for the `artifacts` and `trace` fields. This is required so parallel nodes append to these lists instead of clobbering. Preserve this pattern for any new list-typed state field intended to survive fan-out.

## Bundle-then-transport workflow

Both kits ship as git bundles built by `bundle.sh`. The intended flow is **build on one machine, transport `.bundle` file, clone on another**. Bundles are gitignored in this top-level repo (they are build artifacts). Do not commit `*.bundle` files.
