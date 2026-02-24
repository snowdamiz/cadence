#!/usr/bin/env python3
"""Read and print the ideation payload from .cadence/cadence.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read ideation payload from cadence.json.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def cadence_json_path(project_root: Path) -> Path:
    return project_root / ".cadence" / "cadence.json"


def load_ideation(project_root: Path) -> dict:
    state_path = cadence_json_path(project_root)
    if not state_path.exists():
        return {}

    try:
        with state_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_CADENCE_JSON: {exc} path={state_path}") from exc

    ideation = data.get("ideation", {})
    if isinstance(ideation, dict):
        return ideation
    return {}


def main() -> int:
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, _ = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=False,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)
    try:
        ideation = load_ideation(project_root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(ideation, indent=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
