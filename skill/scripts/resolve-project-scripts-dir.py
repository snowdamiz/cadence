#!/usr/bin/env python3
"""Resolve Cadence helper scripts dir for the current project.

Behavior:
- If state.cadence-scripts-dir exists in .cadence/cadence.json and points to
  an existing directory, use it.
- If missing or stale but .cadence exists, regenerate project path state by
  running init-cadence-scripts-dir.py from this skill's scripts directory.
- Print the resolved scripts directory to stdout.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint


SCRIPT_DIR = Path(__file__).resolve().parent
INIT_SCRIPT_PATH = SCRIPT_DIR / "init-cadence-scripts-dir.py"


def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve Cadence helper scripts dir for a project.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def initialize_scripts_dir(project_root: Path):
    result = run_command(
        [
            sys.executable,
            str(INIT_SCRIPT_PATH),
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "FAILED_TO_INIT_CADENCE_SCRIPTS_DIR"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def read_scripts_dir_from_cadence_json(project_root: Path):
    cadence_json_path = project_root / ".cadence" / "cadence.json"
    if not cadence_json_path.exists():
        return ""

    try:
        with cadence_json_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    return str(data.get("state", {}).get("cadence-scripts-dir", "")).strip()


def ensure_scripts_dir(project_root: Path):
    cadence_dir = project_root / ".cadence"
    if not cadence_dir.exists():
        print("MISSING_CADENCE_DIR", file=sys.stderr)
        raise SystemExit(1)

    scripts_dir = read_scripts_dir_from_cadence_json(project_root)
    if scripts_dir and Path(scripts_dir).is_dir():
        return scripts_dir

    initialize_scripts_dir(project_root)

    scripts_dir = read_scripts_dir_from_cadence_json(project_root)
    if not scripts_dir:
        print("MISSING_CADENCE_SCRIPTS_DIR", file=sys.stderr)
        raise SystemExit(1)

    if not Path(scripts_dir).is_dir():
        print("INVALID_CADENCE_SCRIPTS_DIR", file=sys.stderr)
        raise SystemExit(1)

    return scripts_dir


def main():
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, _ = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=True,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

    write_project_root_hint(SCRIPT_DIR, project_root)
    scripts_dir = ensure_scripts_dir(project_root)
    print(scripts_dir)


if __name__ == "__main__":
    main()
