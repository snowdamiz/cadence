#!/usr/bin/env python3
"""Run Cadence prerequisite gate and persist pass state."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint


SCRIPT_DIR = Path(__file__).resolve().parent
RESOLVE_SCRIPT = SCRIPT_DIR / "resolve-project-scripts-dir.py"
ROUTE_GUARD_SCRIPT = SCRIPT_DIR / "assert-workflow-route.py"


def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Cadence prerequisite gate and persist pass state.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    parser.add_argument(
        "--scripts-dir",
        default="",
        help="Optional pre-resolved cadence scripts directory. Skips scripts-dir resolution when provided.",
    )
    return parser.parse_args()


def assert_expected_route(project_root: Path):
    result = run_command(
        [
            sys.executable,
            str(ROUTE_GUARD_SCRIPT),
            "--skill-name",
            "prerequisite-gate",
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "WORKFLOW_ROUTE_CHECK_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def resolve_scripts_dir(project_root: Path):
    result = run_command(
        [
            sys.executable,
            str(RESOLVE_SCRIPT),
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "MISSING_CADENCE_SCRIPTS_DIR"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    scripts_dir = result.stdout.strip()
    if not scripts_dir:
        print("MISSING_CADENCE_SCRIPTS_DIR", file=sys.stderr)
        raise SystemExit(1)

    return scripts_dir


def read_prerequisite_state(scripts_dir, project_root: Path):
    script_path = Path(scripts_dir) / "handle-prerequisite-state.py"
    result = run_command(
        [
            sys.executable,
            str(script_path),
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "PREREQUISITE_STATE_READ_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout.strip()


def write_prerequisite_state(scripts_dir, pass_state, project_root: Path):
    script_path = Path(scripts_dir) / "handle-prerequisite-state.py"
    result = run_command(
        [
            sys.executable,
            str(script_path),
            pass_state,
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "PREREQUISITE_STATE_WRITE_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main():
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    explicit_scripts_dir = args.scripts_dir.strip()
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
    assert_expected_route(project_root)
    if explicit_scripts_dir:
        scripts_path = Path(explicit_scripts_dir).expanduser()
        if not scripts_path.is_absolute():
            scripts_path = (project_root / scripts_path).resolve()
        else:
            scripts_path = scripts_path.resolve()
        if not scripts_path.is_dir():
            print("INVALID_CADENCE_SCRIPTS_DIR", file=sys.stderr)
            raise SystemExit(1)
        scripts_dir = str(scripts_path)
    else:
        scripts_dir = resolve_scripts_dir(project_root)
    state = read_prerequisite_state(scripts_dir, project_root)

    if state == "true":
        print(json.dumps({"status": "ok", "prerequisites_pass": True, "source": "cache"}))
        return

    if shutil.which("python3") is None:
        print("MISSING_PYTHON3", file=sys.stderr)
        raise SystemExit(1)

    write_prerequisite_state(scripts_dir, "1", project_root)
    print(json.dumps({"status": "ok", "prerequisites_pass": True, "source": "fresh-check"}))


if __name__ == "__main__":
    main()
