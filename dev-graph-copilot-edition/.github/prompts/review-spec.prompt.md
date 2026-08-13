---
description: 'Human gate helper — checklist for approving/rejecting a Spec.'
mode: 'ask'
---

I'm about to approve or reject the following Spec. Walk me through the
Spec Review checklist and flag anything that fails.

## Spec

${input:spec:Paste the JSON spec}

---

## Checklist

For each item below, answer PASS / FAIL / UNSURE with a one-line reason.

1. **Summary reads like a PR title** (imperative, specific, <70 chars).
2. **Every AC is verifiable** by a test, a metric, or code review — no vague
   "code is clean" ACs.
3. **AC count is 3–6** (fewer = under-specified, more = probably two tasks
   in one).
4. **`affected_components` values are from the enum** (glue_job,
   enrichment_worker, recommend_api, enrichment_prompt, reranker_prompt,
   user_profile_index, opensearch_query).
5. **Risk level matches reality.** `high` if it touches prod prompts,
   OpenSearch mappings, or /recommend response shape. Do not let a
   user-visible change default to `low`.
6. **Missing components?** Given the task, does the affected_components list
   miss anything? (e.g. a prompt change usually needs an eval, a mapping
   change usually needs a backfill.)
7. **Notes address open questions.** Ambiguity acknowledged, not hidden.

At the end, give me:

- **Recommendation:** APPROVE / REJECT / APPROVE-WITH-EDITS
- **If REJECT:** the exact feedback text I should send back to Spec Architect
- **If APPROVE-WITH-EDITS:** the specific JSON edits I should make before
  handing to the Coder
