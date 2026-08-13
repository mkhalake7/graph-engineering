# Worked Example — Add `preferred_topics` to Enrichment

A concrete walkthrough of the full workflow for one feature. Follow along
in Copilot Chat if you like — pretend the recommendation-backend repo is
open.

---

## Step 1 — Intake

Task written in `.dev-graph/tasks/preferred-topics.md`:

> Add a new `preferred_topics` field to the enriched user profile,
> populated by the LLM enrichment from the last 30 days of readership,
> stored as a keyword field in the OpenSearch user-profile index.

---

## Step 2 — Repo Explorer (Ask mode)

> `@workspace` help me find the files relevant to: add a new preferred_topics
> field to the enriched user profile. List the affected files, existing
> patterns, and any tests. Don't propose changes yet.

Copilot's response (paraphrased) — pasted into the trace log:

```
Files likely affected:
- prompts/enrichment.md              (LLM enrichment system prompt)
- workers/enrichment_worker.py       (S3 → LLM → OpenSearch)
- opensearch/mappings/user_profile.json
- evals/enrichment_eval_set.jsonl
- tests/test_enrichment_worker.py

Existing patterns:
- Enriched fields are stored as flat keyword or list-of-keyword fields
- New enriched fields are added to both the prompt schema and the mapping
- Backfill is handled by re-running the worker over existing profiles
```

---

## Step 3 — Spec Architect

Switched Copilot to **Spec Architect** mode. Ran `/new-task`, pasted task
and repo context.

Response:

```json
{
  "summary": "Add preferred_topics to enriched user profile via LLM enrichment",
  "acceptance_criteria": [
    "AC1: preferred_topics is a list[str] with length <= 20 in the enriched profile document",
    "AC2: enrichment_prompt asks the LLM to derive preferred_topics from the last 30 days of read doc titles + tags",
    "AC3: opensearch/mappings/user_profile.json adds preferred_topics as a keyword field",
    "AC4: no existing enriched fields are modified in shape or semantics",
    "AC5: offline eval suite shows precision >= 0.75 on the labeled preferred_topics set",
    "AC6: worker includes a backfill plan for existing enriched profiles (documented in PR body)"
  ],
  "affected_components": [
    "enrichment_worker",
    "enrichment_prompt",
    "user_profile_index"
  ],
  "risk": "high",
  "notes": "Prompt change reaches every user on next enrichment run. Backfill is required — existing profiles will not have preferred_topics until re-enriched."
}
```

---

## Step 4 — Human gate: spec review

Ran `/review-spec` with the JSON above.

Copilot's checklist output (paraphrased):

```
1. Summary reads like a PR title — PASS
2. Every AC verifiable — PASS
3. AC count is 3–6 — MARGINAL (6, at the ceiling — acceptable)
4. affected_components from enum — PASS
5. Risk matches reality — PASS (high, prompt change reaches all users)
6. Missing components — UNSURE: does the recommend_api need to change to
   surface preferred_topics anywhere in the response? If yes, that's a
   separate AC.
7. Notes address open questions — PASS

Recommendation: APPROVE-WITH-EDITS
- Bump AC5 precision to 0.80 (industry norm for a new enriched field)
- Add AC7: "recommend_api response shape is unchanged" — explicit non-goal
```

Decision: approved with those two edits. Approved spec pasted into trace
log under `## Spec (approved)`.

---

## Step 5 — Coder (Agent mode)

Switched to **Coder** mode. Ran `/coder-input`, pasted approved spec.

Coder edited three files:
1. `prompts/enrichment.md` — added preferred_topics section with two
   few-shot examples and JSON schema entry
2. `opensearch/mappings/user_profile.json` — added `preferred_topics`
   keyword field
3. `workers/enrichment_worker.py` — extended the enrichment call to
   include preferred_topics and the write path to persist it

Coder's stop message:

```
Done. Summary:
- AC1: preferred_topics is list[str], max 20 — enforced in
  workers/enrichment_worker.py:142 (slice) and prompt schema
- AC2: prompt asks for topics from last 30 days — prompts/enrichment.md line 47
- AC3: mapping updated — opensearch/mappings/user_profile.json line 22
- AC4: existing fields untouched — verified by diff
- AC5: NOT verified — needs eval run
- AC6: backfill plan — see PR body follow-up
- AC7: recommend_api unchanged — no edits to api/ subtree

Follow-ups for Grader:
- Run: python evals/run.py --prompt prompts/enrichment.md --set preferred_topics
- Compare to baseline; ship only if >= 0.80
```

Ran tests locally:

```bash
pytest tests/test_enrichment_worker.py -x -q     # 4 passed
ruff check workers/ prompts/                      # clean
```

Ran the eval suite:

```
baseline precision: 0.72
candidate precision: 0.83
```

Regressed on nothing surprising — good delta.

---

## Step 6 — Grader

Switched to **Grader** mode (fresh chat — did not carry over Coder's
reasoning).

Pasted the approved spec, the diff, the test output, and the eval numbers.

Response:

```json
{
  "verdict": "pass",
  "feedback": "All ACs satisfied. Eval delta is healthy (0.72 → 0.83, above the 0.80 bar).",
  "criteria_status": {
    "AC1": "pass",
    "AC2": "pass",
    "AC3": "pass",
    "AC4": "pass",
    "AC5": "pass",
    "AC6": "pass",
    "AC7": "pass"
  },
  "notes": "Reindex is not required (additive keyword field, OpenSearch handles gracefully), but the backfill IS needed so existing profiles get preferred_topics. Confirm the runbook for backfill is linked from the PR body."
}
```

---

## Step 7 — Human gate: PR review

Looked at the diff one more time in the VS Code Source Control panel.
Agreed with every hunk. No edits needed.

---

## Step 8 — PR Publisher

Ran `/pr-body` with the trace log. Generated body:

```markdown
## Summary
Add preferred_topics to enriched user profile via LLM enrichment

## Acceptance criteria
- [ ] AC1: preferred_topics is list[str] with length <= 20
- [ ] AC2: enrichment_prompt derives preferred_topics from last 30d of reads
- [ ] AC3: user_profile mapping adds preferred_topics as keyword
- [ ] AC4: no existing enriched fields modified
- [ ] AC5: eval precision >= 0.80 on labeled set
- [ ] AC6: backfill plan for existing enriched profiles
- [ ] AC7: recommend_api response shape unchanged

## Affected components
enrichment_worker, enrichment_prompt, user_profile_index

## What changed
- prompts/enrichment.md — added preferred_topics section + 2 few-shot examples
- opensearch/mappings/user_profile.json — added keyword field
- workers/enrichment_worker.py — extended enrichment call and write path

## Verification
- Tests: pytest tests/test_enrichment_worker.py — 4 passed
- Grader: pass — all 7 ACs satisfied
- Eval delta: baseline 0.72 → candidate 0.83 (above 0.80 bar)

## Follow-ups
- [ ] Kick off backfill job for existing enriched profiles (see runbook)
- [ ] Monitor eval precision on next weekly refresh
```

Committed, pushed, opened PR. Done.

---

## What this example demonstrates

- **Every human gate mattered.** Step 4 caught a missing AC (recommend_api
  non-goal) that would have been ambiguous in review.
- **The Grader is independent.** Fresh chat, no Coder priming — its
  criteria_status is honest, not sympathetic.
- **The trace log IS the audit.** In three weeks, when someone asks "why
  did preferred_topics get added?", the whole reasoning chain is one file.
- **The workflow is slow — but it's slower than you think in a good way.**
  Rushing past Step 4 saves 10 minutes and costs a rollback. Every time.
