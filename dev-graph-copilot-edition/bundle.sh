#!/usr/bin/env bash
# Create a git bundle of the Copilot edition for transport to the office.
# Usage: ./bundle.sh
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .git ]; then
  echo "[bundle] initializing local git repo..."
  git init -q
  git add -A
  git -c user.email="devgraph@local" -c user.name="devgraph" \
      commit -q -m "initial import: dev-graph-copilot-edition"
else
  echo "[bundle] using existing git repo"
  if [ -n "$(git status --porcelain)" ]; then
    echo "[bundle] committing uncommitted changes..."
    git add -A
    git -c user.email="devgraph@local" -c user.name="devgraph" \
        commit -q -m "bundle: snapshot before transport"
  fi
fi

OUT="dev-graph-copilot-edition.bundle"
git bundle create "$OUT" --all
echo ""
echo "[bundle] wrote: $(pwd)/$OUT ($(du -h "$OUT" | cut -f1))"
echo ""
echo "On the office machine:"
echo "  mkdir dev-graph-copilot-edition && cd dev-graph-copilot-edition"
echo "  git clone /path/to/$OUT ."
echo "  # then copy .github/ into your recommendation-backend repo"
