#!/usr/bin/env bash
# Create a git bundle of this starter kit for transport to the office.
# Run from inside dev-graph-starter/.
#
#   ./bundle.sh
#
# Produces dev-graph-starter.bundle in the current directory.
# Move that file to your office machine, then:
#
#   mkdir dev-graph-starter && cd dev-graph-starter
#   git clone /path/to/dev-graph-starter.bundle .
#   python -m venv .venv && source .venv/bin/activate
#   pip install -e ".[dev]"
#   cp .env.template .env    # then edit
#
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .git ]; then
  echo "[bundle] initializing local git repo..."
  git init -q
  git add -A
  git -c user.email="devgraph@local" -c user.name="devgraph" \
      commit -q -m "initial import: dev-graph-starter Phase 1"
else
  echo "[bundle] using existing git repo"
  if [ -n "$(git status --porcelain)" ]; then
    echo "[bundle] committing uncommitted changes..."
    git add -A
    git -c user.email="devgraph@local" -c user.name="devgraph" \
        commit -q -m "bundle: snapshot before transport"
  fi
fi

OUT="dev-graph-starter.bundle"
git bundle create "$OUT" --all
echo ""
echo "[bundle] wrote: $(pwd)/$OUT ($(du -h "$OUT" | cut -f1))"
echo ""
echo "On the office machine:"
echo "  mkdir dev-graph-starter && cd dev-graph-starter"
echo "  git clone /path/to/$OUT ."
