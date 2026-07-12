#!/usr/bin/env python3
"""Install Job OK as a local skill for supported agents."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys


SKILL_NAME = "job-ok"
EXCLUDED_NAMES = {
    ".git",
    ".DS_Store",
    "__pycache__",
    "job-search-cases",
}


def ignore_names(_directory: str, names: list[str]) -> list[str]:
    ignored: list[str] = []
    for name in names:
        if name in EXCLUDED_NAMES or name.endswith(".pyc"):
            ignored.append(name)
    return ignored


def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


def target_path(project: bool) -> pathlib.Path:
    if project:
        return pathlib.Path.cwd() / ".agents" / "skills" / SKILL_NAME
    return pathlib.Path.home() / ".codex" / "skills" / SKILL_NAME


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", action="store_true", help="Install into the current project's .agents/skills directory")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing installation")
    args = parser.parse_args()

    source = repo_root()
    target = target_path(args.project)

    if not (source / "SKILL.md").exists():
        print(f"SKILL.md not found at {source}", file=sys.stderr)
        return 2

    if target.exists():
        if not args.force:
            print(f"Target already exists: {target}")
            print("Use --force to overwrite it.")
            return 1
        shutil.rmtree(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=ignore_names)
    print(f"Installed Job OK to {target}")
    print("Restart your agent or open a new session, then use: $job-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
