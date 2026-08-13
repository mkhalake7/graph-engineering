# Dev-Graph — Copilot Edition

Graph engineering distilled into a set of **VS Code GitHub Copilot Chat**
custom chat modes, prompt files, and a workflow runbook. Use when you have
Copilot Chat but no programmatic model access.

## What you lose vs. the automated kit
- Automation (you drive each step by hand)
- Durable checkpoints and retry loops
- Parallel fan-out across specialists

## What you keep — the parts that actually matter
- **Structured specs before code** — the Spec Architect mode makes you write
  acceptance criteria first, every time.
- **Human gates** — naturally, because you are in every loop.
- **Specialist system prompts** — one saved mode per role, so the model plays
  a consistent character across the entire team.
- **Reusable prompts** — invoked by name from the prompts palette.
- **Methodology discipline** — the graph becomes a checklist you follow,
  not code that runs.

## What's in the box

```
dev-graph-copilot-edition/
├── README.md                              this file
├── WORKFLOW.md                            step-by-step runbook (the graph as a checklist)
├── bundle.sh                              build a transport bundle
├── .gitignore
├── .github/
│   ├── copilot-instructions.md            always-on system context (auto-loaded)
│   ├── chatmodes/
│   │   ├── spec-architect.chatmode.md     Opus-class · read-only · JSON spec output
│   │   ├── coder.chatmode.md              agent-mode coding against a spec
│   │   ├── grader.chatmode.md             verifies a diff against the spec
│   │   └── llm-prompt-engineer.chatmode.md  edits prompts/*.md, tightens eval
│   └── prompts/
│       ├── new-task.prompt.md             /new-task — kicks off the spec
│       ├── review-spec.prompt.md          /review-spec — human gate helper
│       ├── coder-input.prompt.md          /coder-input — hands off spec to Coder
│       └── pr-body.prompt.md              /pr-body — assembles PR description
├── examples/
│   └── preferred-topics.md                worked example of the full flow
└── scripts/
    ├── install-into-repo.py               copy .github/ + WORKFLOW.md into a target repo
    └── validate-chatmodes.py              lint the chatmode & prompt files
```

The two Python scripts under `scripts/` are optional conveniences (pure stdlib, no dependencies) — everything else works without them.

## Setup on the office machine

### 1. Merge into your recommendation-backend repo

The `.github/` folder is designed to live inside your target repo so Copilot
picks it up automatically for that workspace.

**Easiest:** use the installer script from this kit.

```bash
python scripts/install-into-repo.py --target /path/to/your/recommendation-backend
# preview first with --dry-run; use --force to overwrite existing files
```

The installer refuses to overwrite an existing `copilot-instructions.md`
without `--force`, since that file is often team-owned. Individual chatmode
and prompt files are skipped if they already exist.

**Manual alternative:**

```bash
# from your recommendation-backend repo root:
cp -R /path/to/dev-graph-copilot-edition/.github .
cp /path/to/dev-graph-copilot-edition/WORKFLOW.md .
cp /path/to/dev-graph-copilot-edition/examples/preferred-topics.md examples/
```

Commit these onto a branch and share with your team so everyone gets the same
modes and prompts.

### 2. Reload VS Code

`Cmd+Shift+P` → **Developer: Reload Window**

### 3. Verify the modes and prompts are loaded

Open a Copilot Chat panel. In the mode picker (top-left of the chat panel),
you should now see:

- **Spec Architect**
- **Coder**
- **Grader**
- **LLM Prompt Engineer**

Open the command palette (`Cmd+Shift+P`) → type "Chat: Run Prompt". You should
see these under the palette:

- `/new-task`
- `/review-spec`
- `/coder-input`
- `/pr-body`

### 4. Pick your models

For each mode, use the model picker inside the chat panel to select a strong
model for judgment tasks (Spec Architect, Grader → Claude Opus / GPT-5) and a
capable model for coding (Coder → Claude Sonnet / GPT-5). You pick once per
mode and Copilot remembers it.

## The workflow, in one paragraph

Open a Copilot Chat panel. Switch to **Spec Architect** mode. Run `/new-task`
and paste your task text. Copilot returns a JSON spec. Review it — if wrong,
send corrections in the same thread until it's right. Copy the approved spec
into a comment on your ticket (this is your "human gate" record). Switch to
**Coder** mode (agent-enabled). Run `/coder-input` with the approved spec.
Copilot edits your files. When Copilot says it's done, switch to **Grader**
mode and paste the spec + your git diff — Copilot returns pass/fail with
reasoning. If pass, run `/pr-body` to generate the PR description, then
`git add`, commit, push, `gh pr create` (or use the Source Control panel).

Full step-by-step in **WORKFLOW.md**.

### 5. Validate (optional)

If you ever hand-edit a chatmode or prompt file, sanity-check it:

```bash
python scripts/validate-chatmodes.py
# or point at an installed copy:
python scripts/validate-chatmodes.py --dir /path/to/your/repo/.github
```

Checks frontmatter validity, required fields (`description`), duplicate
names, and that any `mode:` reference in a prompt matches a real chat mode.

## Transport

Same pattern as the runtime kit:

```bash
./bundle.sh
# → dev-graph-copilot-edition.bundle (single file)
```

Move the bundle to your office machine, then:

```bash
mkdir dev-graph-copilot-edition && cd dev-graph-copilot-edition
git clone /path/to/dev-graph-copilot-edition.bundle .
```

## When to upgrade to the runtime kit

The moment you get programmatic model access (Anthropic API key, Azure OpenAI,
GitHub Models with an API token, or Claude Code CLI at the office), the
runtime kit in `../dev-graph-starter/` becomes usable. The specialist prompts
here are the same conceptual prompts as there — the migration is mostly
mechanical.
