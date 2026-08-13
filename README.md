# graph-engineering

Research, design, and two shippable kits for applying **graph engineering**
to a real recommendation-backend project — organizing multiple specialist
AI agents (or workflow steps) as an explicit state machine instead of a
single agentic loop.

## What's in this repo

### Research docs (open in a browser)

- **`index.html`** — deep dive on the three paradigms: prompt engineering
  vs loop engineering vs graph engineering. Where each fits, tradeoffs,
  when to reach for which.
- **`recommendation-dev-graph.html`** — the applied design: a
  graph-engineered dev workflow for building a recommendation backend
  service, with the exact write-path (Glue → S3 → enrichment worker →
  OpenSearch) and read-path (`/recommend` API) topology, node catalog,
  state schema, routing rules, and a worked example.

### `dev-graph-starter/` — the runtime kit

A LangGraph-based Phase 1 dev-workflow graph. Runnable Python. Requires an
Anthropic API key. Nodes: Intake, Repo Explorer, Spec Architect (Opus),
Coder (Sonnet, tool-use loop over a git worktree), Integration Runner,
PR Publisher, plus two human interrupts (spec approval, PR approval).
Durable SQLite checkpointer. See `dev-graph-starter/README.md`.

### `dev-graph-copilot-edition/` — the Copilot Chat kit

Same graph shape, distilled into VS Code GitHub Copilot Chat custom
chat modes, prompt files, and a workflow runbook. Human drives every
step. No API keys needed — works with whatever models your Copilot
subscription exposes. Includes an HTML setup guide
(`HOW-TO-VSCODE.html`). See `dev-graph-copilot-edition/README.md`.

## Which kit to use

| Situation | Kit |
|---|---|
| You have programmatic API access (Anthropic key, Azure OpenAI, etc.) | `dev-graph-starter/` |
| You only have VS Code Copilot Chat | `dev-graph-copilot-edition/` |
| You want the concepts before the code | Open `index.html` and `recommendation-dev-graph.html` |

## The system these kits build

Both kits are designed to build and maintain a **document recommendation
backend service** with two paths:

**Write path** — an upstream Glue job produces a base user profile to S3;
the backend enrichment worker reads it, fetches recent-read docs from an
OpenSearch documents index, calls an LLM enrichment prompt, and writes an
enriched user profile to a distinct OpenSearch index.

**Read path** — `/recommend` takes `user_id`, `anchor_doc_id`, and
candidate docs; fetches enriched profile + docs from OpenSearch; passes
to the ML team's recommendation library; LLM re-ranks the top-N.

Full architecture is in `recommendation-dev-graph.html`.

## Getting started

- **Read** `index.html` first if you're new to the paradigms.
- **Read** `recommendation-dev-graph.html` for the applied design.
- **Ship** the runtime kit or Copilot edition — each has its own README.
