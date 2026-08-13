#!/usr/bin/env python3
"""Install the Copilot edition into a target repository.

Copies:
  .github/copilot-instructions.md
  .github/chatmodes/*.chatmode.md
  .github/prompts/*.prompt.md
  WORKFLOW.md

Merge-safety: refuses to overwrite an existing copilot-instructions.md unless
--force is passed (that file is often team-owned and merging by hand matters).
Individual chatmode/prompt files are skipped if they already exist, unless
--force.

Usage:
  python scripts/install-into-repo.py --target /path/to/your/repo
  python scripts/install-into-repo.py --target . --dry-run
  python scripts/install-into-repo.py --target . --force

Pure stdlib. Python 3.11+.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]

# (source relative to KIT_ROOT, destination relative to target, kind)
FILES = [
    (Path(".github/copilot-instructions.md"),  Path(".github/copilot-instructions.md"),  "instructions"),
    (Path("WORKFLOW.md"),                       Path("WORKFLOW.md"),                       "runbook"),
]
DIRS = [
    (Path(".github/chatmodes"), Path(".github/chatmodes"), "*.chatmode.md", "chatmode"),
    (Path(".github/prompts"),   Path(".github/prompts"),   "*.prompt.md",   "prompt"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Install Copilot edition into a target repo.")
    ap.add_argument("--target", required=True, help="Path to target repository root.")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be copied; don't write.")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files without asking.")
    args = ap.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        _fail(f"target does not exist: {target}")
    if not target.is_dir():
        _fail(f"target is not a directory: {target}")

    _check_git(target)

    _log(f"kit source: {KIT_ROOT}")
    _log(f"target:     {target}")
    _log(f"mode:       {'dry-run' if args.dry_run else 'apply'}{' (force)' if args.force else ''}")
    print()

    copied: list[str] = []
    skipped: list[str] = []
    blocked: list[str] = []

    for src_rel, dst_rel, kind in FILES:
        src = KIT_ROOT / src_rel
        dst = target / dst_rel
        if not src.exists():
            _fail(f"kit missing expected file: {src_rel}")
        if dst.exists() and not args.force:
            if kind == "instructions":
                blocked.append(str(dst_rel))
                _log(f"BLOCKED  {dst_rel}  (exists — use --force or merge by hand)")
            else:
                skipped.append(str(dst_rel))
                _log(f"skipped  {dst_rel}  (exists)")
            continue
        _copy_file(src, dst, dry=args.dry_run)
        copied.append(str(dst_rel))
        _log(f"{'would copy' if args.dry_run else 'copied  '}  {dst_rel}")

    for src_dir_rel, dst_dir_rel, pattern, kind in DIRS:
        src_dir = KIT_ROOT / src_dir_rel
        if not src_dir.exists():
            _fail(f"kit missing expected directory: {src_dir_rel}")
        for src_file in sorted(src_dir.glob(pattern)):
            rel = src_file.relative_to(KIT_ROOT)
            dst_file = target / dst_dir_rel / src_file.name
            if dst_file.exists() and not args.force:
                skipped.append(str(rel))
                _log(f"skipped  {rel}  (exists)")
                continue
            _copy_file(src_file, dst_file, dry=args.dry_run)
            copied.append(str(rel))
            _log(f"{'would copy' if args.dry_run else 'copied  '}  {rel}")

    print()
    print(f"summary: {len(copied)} copied, {len(skipped)} skipped, {len(blocked)} blocked")

    if blocked and not args.dry_run:
        print("\nBlocked files (need manual merge or --force):")
        for f in blocked:
            print(f"  - {f}")
        return 2

    if not args.dry_run:
        print("\nNext step: reload VS Code and verify modes appear in the chat mode picker.")
    return 0


def _copy_file(src: Path, dst: Path, dry: bool) -> None:
    if dry:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _check_git(target: Path) -> None:
    r = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        _log(f"warning: target is not a git repo — proceeding anyway.")
        print()


def _log(msg: str) -> None:
    print(f"[install] {msg}")


def _fail(msg: str) -> None:
    print(f"[install] error: {msg}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
