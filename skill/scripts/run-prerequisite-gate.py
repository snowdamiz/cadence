#!/usr/bin/env python3
"""Run Cadence prerequisite gate and persist pass state."""

import json
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RESOLVE_SCRIPT = SCRIPT_DIR / "resolve-project-scripts-dir.py"


def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def resolve_scripts_dir():
    result = run_command([sys.executable, str(RESOLVE_SCRIPT)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "MISSING_CADENCE_SCRIPTS_DIR"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    scripts_dir = result.stdout.strip()
    if not scripts_dir:
        print("MISSING_CADENCE_SCRIPTS_DIR", file=sys.stderr)
        raise SystemExit(1)

    return scripts_dir


def read_prerequisite_state(scripts_dir):
    script_path = Path(scripts_dir) / "handle-prerequisite-state.py"
    result = run_command([sys.executable, str(script_path)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "PREREQUISITE_STATE_READ_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout.strip()


def write_prerequisite_state(scripts_dir, pass_state):
    script_path = Path(scripts_dir) / "handle-prerequisite-state.py"
    result = run_command([sys.executable, str(script_path), pass_state])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "PREREQUISITE_STATE_WRITE_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main():
    scripts_dir = resolve_scripts_dir()
    state = read_prerequisite_state(scripts_dir)

    if state == "true":
        print(json.dumps({"status": "ok", "prerequisites_pass": True, "source": "cache"}))
        return

    if shutil.which("python3") is None:
        print("MISSING_PYTHON3", file=sys.stderr)
        raise SystemExit(1)

    write_prerequisite_state(scripts_dir, "1")
    print(json.dumps({"status": "ok", "prerequisites_pass": True, "source": "fresh-check"}))


if __name__ == "__main__":
    main()
