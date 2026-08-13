#!/usr/bin/env python3
"""Validate chat mode and prompt files.

Checks:
  - Each .chatmode.md has --- frontmatter with a description field
  - Each .prompt.md has --- frontmatter with a description field
  - .prompt.md files with a `mode:` field reference an existing chat mode
    (built-in: ask, edit, agent — or a custom mode present in this repo)
  - No duplicate mode names, no duplicate prompt names
  - Body is non-empty after the frontmatter
  - copilot-instructions.md exists and is non-empty

Exit code 0 on success, 1 on any errors. Prints a per-file report.

Usage:
  python scripts/validate-chatmodes.py                    # scans kit .github/
  python scripts/validate-chatmodes.py --dir path/to/.github

Pure stdlib. Python 3.11+.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]
BUILTIN_MODES = {"ask", "edit", "agent"}

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
FIELD_RE = re.compile(r"^(\w+)\s*:\s*(.*)$")


class Report:
    def __init__(self) -> None:
        self.errors: list[tuple[Path, str]] = []
        self.warnings: list[tuple[Path, str]] = []
        self.ok: list[Path] = []

    def error(self, path: Path, msg: str) -> None:
        self.errors.append((path, msg))

    def warn(self, path: Path, msg: str) -> None:
        self.warnings.append((path, msg))

    def pass_(self, path: Path) -> None:
        self.ok.append(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Copilot chat modes and prompts.")
    ap.add_argument("--dir", default=str(KIT_ROOT / ".github"),
                    help="Path to the .github directory to validate (default: kit's own).")
    args = ap.parse_args()

    github = Path(args.dir).expanduser().resolve()
    if not github.exists():
        print(f"error: .github directory not found: {github}", file=sys.stderr)
        return 1

    report = Report()
    mode_names: dict[str, Path] = {}
    prompt_names: dict[str, Path] = {}

    # copilot-instructions.md
    instructions = github / "copilot-instructions.md"
    if not instructions.exists():
        report.error(instructions, "missing copilot-instructions.md")
    elif not instructions.read_text().strip():
        report.error(instructions, "copilot-instructions.md is empty")
    else:
        report.pass_(instructions)

    # chatmodes
    chatmodes_dir = github / "chatmodes"
    if not chatmodes_dir.exists():
        report.warn(github, "no chatmodes/ directory (expected .github/chatmodes/)")
    else:
        for cm in sorted(chatmodes_dir.glob("*.chatmode.md")):
            _validate_chatmode(cm, report, mode_names)

    # prompts
    prompts_dir = github / "prompts"
    if not prompts_dir.exists():
        report.warn(github, "no prompts/ directory (expected .github/prompts/)")
    else:
        for p in sorted(prompts_dir.glob("*.prompt.md")):
            _validate_prompt(p, report, prompt_names, mode_names)

    _print_report(report)
    return 1 if report.errors else 0


def _validate_chatmode(path: Path, report: Report, seen: dict[str, Path]) -> None:
    fm, body = _split_frontmatter(path, report)
    if fm is None:
        return

    if "description" not in fm:
        report.error(path, "missing required frontmatter field: description")

    if not body.strip():
        report.error(path, "chatmode body is empty (nothing to system-prompt with)")

    name = path.name.removesuffix(".chatmode.md")
    if name in seen:
        report.error(path, f"duplicate chat mode name '{name}' (also defined in {seen[name].name})")
    else:
        seen[name] = path

    if not report.errors or report.errors[-1][0] != path:
        report.pass_(path)


def _validate_prompt(
    path: Path,
    report: Report,
    seen: dict[str, Path],
    modes: dict[str, Path],
) -> None:
    fm, body = _split_frontmatter(path, report)
    if fm is None:
        return

    if "description" not in fm:
        report.error(path, "missing required frontmatter field: description")

    if not body.strip():
        report.error(path, "prompt body is empty")

    mode = fm.get("mode", "").strip().strip("'\"")
    if mode and mode.lower() not in BUILTIN_MODES:
        # Custom mode reference — case-insensitive lookup against chatmode filenames.
        available = {n.lower() for n in modes}
        # Chat modes are looked up by their display description in the picker,
        # but the file-based binding uses the filename slug. Accept either
        # slug-form ('spec-architect') or Title-form ('Spec Architect').
        slug_forms = {m.replace(" ", "-").lower() for m in modes}
        slug_forms |= available
        if mode.replace(" ", "-").lower() not in slug_forms:
            report.warn(path, f"mode: '{mode}' does not match any chat mode in this repo "
                              f"(built-ins: {sorted(BUILTIN_MODES)}, custom: {sorted(modes)})")

    name = path.name.removesuffix(".prompt.md")
    if name in seen:
        report.error(path, f"duplicate prompt name '{name}' (also defined in {seen[name].name})")
    else:
        seen[name] = path

    if not report.errors or report.errors[-1][0] != path:
        report.pass_(path)


def _split_frontmatter(path: Path, report: Report) -> tuple[dict[str, str] | None, str]:
    text = path.read_text()
    m = FM_RE.match(text)
    if not m:
        report.error(path, "missing --- frontmatter block at top of file")
        return None, ""
    raw_fm, body = m.group(1), m.group(2)
    fm: dict[str, str] = {}
    for line in raw_fm.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        fm_m = FIELD_RE.match(line)
        if fm_m:
            key, value = fm_m.group(1), fm_m.group(2).strip()
            fm[key] = value
    return fm, body


def _print_report(report: Report) -> None:
    for path in report.ok:
        print(f"OK    {path.name}")
    for path, msg in report.warnings:
        print(f"WARN  {path.name}: {msg}")
    for path, msg in report.errors:
        print(f"FAIL  {path.name}: {msg}")
    print()
    print(f"summary: {len(report.ok)} ok, {len(report.warnings)} warning(s), {len(report.errors)} error(s)")


if __name__ == "__main__":
    sys.exit(main())
