# Dev-Graph Starter — Phase 1

A LangGraph-based dev-workflow graph for building the recommendation backend.

Phase 1 = a linear pipeline with two human gates (spec approval, PR approval),
a single Coder agent (tool-use loop over a git worktree of your target repo),
and a deterministic integration runner. Later phases add specialization,
parallel fan-out, an LLM grader, and prompt eval — see the design doc
`recommendation-dev-graph.html` for the full picture.

```
  intake → repo_explorer → spec_architect → [HUMAN: spec] → coder
             → integration_runner → [HUMAN: PR] → pr_publisher
```

## What's in the box

```
dev-graph-starter/
├── README.md                      this file
├── pyproject.toml                 dependencies & packaging
├── .env.template                  copy to .env at the office
├── .gitignore
├── bundle.sh                      creates a git bundle for transport
├── prompts/
│   ├── spec_architect.md          system prompt for the Spec Architect (Opus)
│   ├── coder.md                   system prompt for the Coder agent (Sonnet)
│   └── grader.md                  placeholder for Phase 3
├── scripts/
│   ├── run_task.py                CLI: start a run
│   └── resume.py                  CLI: resume a paused run
├── src/dev_graph/
│   ├── state.py                   Pydantic + TypedDict state schema
│   ├── graph.py                   LangGraph wiring
│   ├── checkpointer.py            SQLite durable state
│   ├── agent_tools.py             read_file / write_file / list_files / run_bash
│   ├── llm/client.py              Anthropic SDK wrapper
│   └── nodes/                     one file per node
│       ├── intake.py
│       ├── repo_explorer.py
│       ├── spec_architect.py      calls Claude Opus, produces a Spec
│       ├── human_gate.py          spec_gate + pr_gate (interrupts)
│       ├── coder.py               tool-use loop over a git worktree
│       ├── integration_runner.py  runs pytest + ruff in the worktree
│       └── pr_publisher.py        git commit/push + `gh pr create`
└── tests/test_smoke.py            offline smoke tests
```

## Transport to your office machine

From this machine:

```bash
cd dev-graph-starter
./bundle.sh
# → produces dev-graph-starter.bundle (single file, git history preserved)
```

Move `dev-graph-starter.bundle` to the office (private GitHub, USB, or
whatever transfer method your policy allows).

On the office machine:

```bash
mkdir dev-graph-starter && cd dev-graph-starter
git clone /path/to/dev-graph-starter.bundle .
```

Or if git bundle isn't practical, just zip the directory and unzip at the
office — no git history but everything else works.

## Setup on the office machine

Requirements:
- Python **3.11+**
- `git` on PATH (worktrees are used for isolation per task)
- `gh` CLI, authenticated (`gh auth login`) — only for the PR Publisher
- An Anthropic API key with access to the models below

```bash
cd dev-graph-starter
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.template .env
# Edit .env — set ANTHROPIC_API_KEY and DEV_GRAPH_WORKSPACE
```

`DEV_GRAPH_WORKSPACE` must be an absolute path to your **real recommendation
backend repo** (a git working tree). The Coder node creates a git worktree
per task under `~/.dev_graph/worktrees/` so parallel tasks do not collide
and your working directory is never touched directly.

## Run a task

Start a run:

```bash
python scripts/run_task.py \
  --task "Add preferred_topics field to enriched user profile"
```

The graph runs Intake → Repo Explorer → Spec Architect, then **PAUSES** at
the human spec gate. It prints the proposed Spec as JSON and a `thread_id`.

Approve:

```bash
python scripts/resume.py <thread_id> --approve --feedback "looks good"
```

Reject with feedback (loops back to Spec Architect):

```bash
python scripts/resume.py <thread_id> --reject \
  --feedback "AC5 needs precision >= 0.80"
```

Approve with edits (override specific Spec fields):

```bash
python scripts/resume.py <thread_id> --approve \
  --spec-edits '{"risk": "high"}'
```

After spec approval the Coder runs (tool-use loop against a git worktree of
your workspace), then the Integration Runner runs pytest + ruff, then it
PAUSES at the human PR gate. Approve to publish the PR via `gh`.

## Model routing

Defaults in `src/dev_graph/llm/client.py`:

| Node            | Model                  |
|-----------------|------------------------|
| Spec Architect  | `claude-opus-4-7`      |
| Coder           | `claude-sonnet-4-6`    |
| (Grader — P3)   | `claude-opus-4-7`      |

Change these once at the office to whatever models your team is licensed for.

## Phase roadmap

- **Phase 1 (this kit)** — linear pipeline, single Coder, two human gates.
  Prove the checkpointer works, humans get sensible interrupts, PRs are clean.
- **Phase 2** — split Coder into specialists: Glue Job Coder, Enrichment
  Worker Coder, API Coder, OpenSearch Coder, LLM Prompt Engineer. Add a
  Planner node and parallel fan-out.
- **Phase 3** — add Grader (LLM verifier) + Prompt Eval Runner + bounded
  retry cycles. Start collecting traces for hill-climbing.

## Safety notes

- The Coder writes only inside a git worktree under `~/.dev_graph/worktrees/`.
  Your main working tree is never modified.
- The Coder cannot escape the workspace: every path is validated.
- `run_bash` has a 120s timeout and runs in the worktree.
- The PR Publisher never force-pushes and never edits main/master.
- Human gates are HARD stops. The graph will not resume without an explicit
  `resume.py` call.

## Anti-patterns to avoid

See `../recommendation-dev-graph.html` section 10 (the design doc).
