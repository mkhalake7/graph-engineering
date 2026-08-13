# Copilot Instructions — Recommendation Backend

Always-on system context. Every Copilot Chat interaction in this workspace
loads this file.

## What this repo does

This is the backend for a document recommendation system. It has two
distinct runtime paths:

### Write path — enrichment pipeline

1. An upstream AWS Glue job aggregates readership + subscription data and
   writes a **base user profile** snapshot to S3.
2. A backend **enrichment worker** reads the base profile from S3, fetches
   recent-read doc details from the docs-team OpenSearch index, calls an
   **LLM enrichment prompt** (produces interests, topics, personas), and
   writes an **enriched user profile** to a distinct OpenSearch index.

### Read path — /recommend API

1. `POST /recommend { user_id, anchor_doc_id, candidate_docs }` fetches the
   enriched user profile, anchor doc, and candidate docs from OpenSearch in
   parallel.
2. The ML team's recommendation library scores.
3. An **LLM reranker prompt** re-orders the top-N.
4. Returns the response.

## Ownership boundaries

- The Glue job may be owned by this team or by an upstream data team —
  confirm before proposing changes.
- The **docs OpenSearch index** is owned by another team. Read-only from
  our side. Do not propose mapping changes to it.
- The **enriched user profile OpenSearch index** is ours.
- The **ML recommendation library** is a black-box dependency from the ML
  team.

## Component vocabulary (use these exact names)

- `glue_job` — upstream batch, writes base profile to S3
- `enrichment_worker` — S3 → LLM → OpenSearch (write path)
- `recommend_api` — /recommend endpoint (read path)
- `enrichment_prompt` — LLM prompt for user profile enrichment
- `reranker_prompt` — LLM prompt for reranker
- `user_profile_index` — OpenSearch mapping for enriched profiles
- `opensearch_query` — kNN / filter queries

## Non-negotiable guardrails

- **Never modify** the docs OpenSearch mapping. Read-only.
- **Never merge** an LLM prompt change without running the offline eval
  suite. Prompt changes reach every user on next enrichment.
- **Never propose** breaking changes to the `/recommend` response shape
  without an explicit spec that flags it.
- **Prefer editing existing files** to creating new ones.
- **Match existing code style** — no sweeping formatter changes.
- **No new comments** unless the WHY is non-obvious.
- **No error handling** for scenarios that cannot happen.

## When you get an ambiguous request

Ask a specific clarifying question. Do not invent requirements. Do not
proceed on assumptions about the affected component — confirm which of
the vocabulary above it touches.

## Discover before you write — and adapt when you discover

Every mode reads the code before proposing or making changes. Use what
you find to refine the plan — do not follow a stale mental model.

**Read first, always.** Before proposing a spec, before writing a line
of code, before returning a verdict — read the affected files. Use
`codebase` search and `usages` to find call sites, existing patterns,
and prior art.

**Identify local conventions and match them exactly.** Before writing:
- Naming: how are functions, classes, files named in this repo?
- Typing: Pydantic version, TypedDict vs dataclass, plain dicts?
- Testing: pytest fixtures? conftest? factory patterns? real vs mocked
  OpenSearch?
- Imports: absolute vs relative? `from x import y` vs `import x`?
- Error handling: exceptions vs Result types vs None returns?
- Logging: which library? which log levels for what?
- Config: env vars, dotenv, pydantic settings?

Match the file you're editing, not general best practices. If two files
disagree, prefer the pattern used in the nearer neighbors of your change.

**Adapt on the go.** If during exploration or coding you discover
something that changes the plan, do NOT plow ahead. Stop and report:

- The change is already partially done → propose a narrower spec.
- The infrastructure you assumed exists is missing → block on that.
- Fixing the requested thing requires touching a component the spec
  did not flag → flag it, get approval, then continue.
- A local convention contradicts what the spec implied → follow the
  convention and note the deviation.
- A test would be trivial to write in a nearby existing file, avoiding
  a new file → do that.

The graph's superpower over a single prompt is exactly this: pausing
when the world doesn't match the plan.
