# Workflow — the Graph as a Checklist

This is the runbook you follow for every engineering task on the
recommendation backend. It mirrors the automated graph in
`../dev-graph-starter/`, but driven by you inside VS Code Copilot Chat.

```
intake → repo_explorer → spec_architect → [HUMAN: spec] → coder
        → integration_runner → [HUMAN: PR] → pr_publisher
```

Every arrow is a manual step below.

---

## Before you start

- You're in VS Code, in the recommendation-backend repo.
- A Copilot Chat panel is open.
- The `.github/chatmodes/` and `.github/prompts/` files are loaded (see README).
- You've picked models for each mode in the mode picker.
- Create a fresh branch: `git checkout -b devgraph/<short-task-id>`

Record the `task_id` you'll use throughout — e.g. `preferred-topics-2026-08`.

---

## Step 1 — Intake (you)

Write your task in one plain-English sentence. Example:

> Add a new `preferred_topics` field to the enriched user profile,
> populated by the LLM enrichment from the last 30 days of readership,
> and store it in the OpenSearch user-profile index.

Save this at the top of `.dev-graph/tasks/<task_id>.md` (create the folder;
it's git-ignored). This is your **trace log** for the run.

---

## Step 2 — Repo Explorer (Copilot in Ask mode)

Switch Copilot to **Ask** mode (built-in). Type:

> `@workspace` help me find the files relevant to: <paste task>
>
> List the affected files, existing patterns, and any tests. Don't propose
> changes yet.

Read the response. Copy the file list into your trace log under a
`## Repo context` section.

---

## Step 3 — Spec Architect (Copilot in Spec Architect mode)

Switch Copilot to the **Spec Architect** mode.

Run the `/new-task` prompt from the palette. When it asks for the task,
paste your task text. When it asks for repo context, paste the file list
from Step 2.

Copilot returns a JSON spec in a fenced ```json``` block.

Copy the JSON into your trace log under `## Spec (proposed)`.

---

## Step 4 — Human gate: spec review (you)

You are the human gate. Options:

**Approve:** the spec is correct. Copy it into `## Spec (approved)` in your
trace log. Continue to Step 5.

**Reject / edit:** open a new turn in the same chat and say what's wrong.
Ask for a revised spec. Copilot returns a new JSON block. Iterate until
you're happy.

**Rules of thumb before you approve:**
- Every AC is verifiable by a test, a metric, or a code review.
- `affected_components` matches your understanding of the write/read paths.
- `risk` is `high` if this touches prod prompts, OpenSearch mappings, or the
  API response shape. Do not let it default to `low` for user-visible
  changes.

You can invoke `/review-spec` to get a checklist to run through.

---

## Step 5 — Coder (Copilot in Coder mode, Agent enabled)

Switch Copilot to the **Coder** mode. Confirm Agent mode is on (the mode
enables `editFiles` and `runCommands` — Copilot will edit files and run
commands on your workspace).

Run the `/coder-input` prompt. When it asks for the spec, paste the
approved spec JSON.

Copilot iterates: reads relevant files, proposes edits, applies them.
Review each edit inline (this is why we don't need a separate spec-editor
in this edition — you accept/reject each hunk).

When Copilot says it's done, run tests yourself:

```bash
pytest -x -q     # or your project's test command
ruff check .
mypy .
```

Fix any failures by re-invoking the Coder mode with the error output.

---

## Step 6 — Grader (Copilot in Grader mode)

Switch Copilot to the **Grader** mode.

Get your diff:

```bash
git diff HEAD > /tmp/current-diff.patch
```

Paste into chat:

1. The approved spec (JSON)
2. The diff (fenced ```diff``` block, or `#file:/tmp/current-diff.patch`)
3. Your test output

Copilot returns:

```json
{
  "verdict": "pass" | "fail",
  "feedback": "...",
  "criteria_status": {"AC1": "pass", "AC2": "fail", ...}
}
```

If **fail** — read the feedback, go back to Step 5 with the Coder mode and
address it.

If **pass** — copy the verdict into `## Grader (verdict)` in your trace log.

---

## Step 7 — Human gate: PR review (you)

Look at the actual diff one more time. This is your last chance.

Do you agree with every hunk? If not, edit in your IDE directly — you are
the final authority.

---

## Step 8 — PR Publisher (you, with Copilot help)

Run the `/pr-body` prompt (any mode is fine — Ask mode is enough). Paste
your trace log. Copilot returns a well-formatted PR body.

Then:

```bash
git add -A
git commit -m "devgraph: <spec summary>"
git push -u origin devgraph/<task_id>
gh pr create --title "..." --body "$(cat /tmp/pr-body.md)"
```

Or use the VS Code Source Control panel to commit and the GitHub Pull
Requests extension to open the PR — paste the generated body there.

---

## Adaptive behavior — pausing when the code contradicts the plan

Every mode is instructed to **read before writing** and **pause when
reality contradicts the plan**. That means during any step you may see
Copilot stop and surface a "PAUSE:" block instead of forging ahead.

When that happens:

- **Read the finding.** It's usually one of: the change is already
  partially done, missing infrastructure, a local convention that
  contradicts the spec, or scope creep the spec didn't authorize.
- **Answer the specific question.** Copilot will not resume until you
  do. Say either "adapt the plan and continue" (and describe how) or
  "revise the spec first — going back to Spec Architect".
- **Update your trace log** with the pause + your answer. That's the
  audit for why the plan changed mid-flight.

This is the graph's core advantage over a single prompt: pausing when
the world doesn't match what you assumed at the start.

## Failure modes to watch for

| Symptom | Where in the workflow it lives | Fix |
|---|---|---|
| Vague acceptance criteria | Step 4 (Spec review) | Reject the spec and demand specific ACs |
| Coder edits unrelated files | Step 5 (Coder) | Reject those hunks; re-invoke with "minimum change only" |
| Grader rubber-stamps everything | Step 6 (Grader) | Use a different model than the Coder; tighten the Grader prompt |
| Prompts changed without eval | anywhere | Do not merge. Run the eval suite manually first |
| Trace log is empty | you skipped it | Fill it in. The trace is what makes this auditable |

## Anti-patterns

- **Skipping Step 4 because "the spec looks fine".** The habit of pausing
  is the habit that catches bad ideas. Do not skip.
- **Letting the Coder mode also grade.** Same model, same blind spots.
- **Copy-pasting without a trace.** In a week you won't remember why you
  made the change. The trace log IS the audit.
- **Running Steps 5 and 6 in the same chat thread.** The Grader will be
  primed by the Coder's reasoning. Use a fresh chat.
