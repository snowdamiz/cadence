#!/usr/bin/env python3
"""Run Cadence scaffold gate in one deterministic command."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint


SCRIPT_DIR = Path(__file__).resolve().parent
SCAFFOLD_SCRIPT = SCRIPT_DIR / "scaffold-project.sh"
INIT_SCRIPT = SCRIPT_DIR / "init-cadence-scripts-dir.py"
ROUTE_GUARD_SCRIPT = SCRIPT_DIR / "assert-workflow-route.py"


def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Cadence scaffold gate in one deterministic command.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root where scaffold should be applied.",
    )
    return parser.parse_args()


def assert_expected_route(project_root: Path):
    result = run_command(
        [
            sys.executable,
            str(ROUTE_GUARD_SCRIPT),
            "--skill-name",
            "scaffold",
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "WORKFLOW_ROUTE_CHECK_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def run_scaffold(project_root: Path):
    result = subprocess.run(
        ["bash", str(SCAFFOLD_SCRIPT)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "SCAFFOLD_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    return result.stdout.strip() or "scaffold-created"


def initialize_scripts_dir(project_root: Path):
    result = run_command(
        [
            sys.executable,
            str(INIT_SCRIPT),
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "INIT_CADENCE_SCRIPTS_DIR_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def verify_expected_state(project_root: Path):
    cadence_json_path = project_root / ".cadence" / "cadence.json"
    if not cadence_json_path.exists():
        print("CADENCE_JSON_MISSING", file=sys.stderr)
        raise SystemExit(1)

    try:
        with cadence_json_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    scripts_dir = str(data.get("state", {}).get("cadence-scripts-dir", "")).strip()
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
            require_cadence=False,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

    write_project_root_hint(SCRIPT_DIR, project_root)
    assert_expected_route(project_root)
    scaffold_status = run_scaffold(project_root)
    initialize_scripts_dir(project_root)
    scripts_dir = verify_expected_state(project_root)
    print(
        json.dumps(
            {
                "status": "ok",
                "scaffold_status": scaffold_status,
                "cadence_scripts_dir": scripts_dir,
                "project_root": str(project_root),
            }
        )
    )


if __name__ == "__main__":
    main()
