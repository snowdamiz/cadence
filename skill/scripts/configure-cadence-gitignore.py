#!/usr/bin/env python3
"""Update project .gitignore policy for .cadence visibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TARGET_PATTERNS = {".cadence", ".cadence/"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure whether .cadence should be tracked or ignored by git.",
    )
    parser.add_argument(
        "--mode",
        choices=["track", "ignore"],
        required=True,
        help="track removes .cadence ignore entries; ignore adds .cadence/ entry",
    )
    parser.add_argument(
        "--gitignore-path",
        default=".gitignore",
        help="Path to .gitignore file",
    )
    return parser.parse_args()


def normalize_lines(text: str) -> list[str]:
    return text.splitlines()


def apply_mode(lines: list[str], mode: str) -> list[str]:
    filtered = [line for line in lines if line.strip() not in TARGET_PATTERNS]
    if mode == "ignore":
        filtered.append(".cadence/")
    return filtered


def render_lines(lines: list[str]) -> str:
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    gitignore_path = Path(args.gitignore_path)

    original_text = ""
    if gitignore_path.exists():
        original_text = gitignore_path.read_text(encoding="utf-8")

    original_lines = normalize_lines(original_text)
    updated_lines = apply_mode(original_lines, args.mode)
    updated_text = render_lines(updated_lines)
    changed = updated_text != original_text

    if changed:
        gitignore_path.write_text(updated_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "mode": args.mode,
                "path": str(gitignore_path),
                "changed": changed,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
