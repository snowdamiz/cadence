#!/usr/bin/env python3
"""Resolve Cadence helper scripts dir for the current project.

Behavior:
- If .cadence/get-cadence-scripts-dir.py exists, use it.
- If missing but .cadence exists, regenerate project path state by running
  init-cadence-scripts-dir.py from this skill's scripts directory.
- Print the resolved scripts directory to stdout.
"""

import subprocess
import sys
from pathlib import Path


CADENCE_DIR = Path(".cadence")
GETTER_PATH = CADENCE_DIR / "get-cadence-scripts-dir.py"
SCRIPT_DIR = Path(__file__).resolve().parent
INIT_SCRIPT_PATH = SCRIPT_DIR / "init-cadence-scripts-dir.py"


def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def ensure_getter():
    if GETTER_PATH.exists():
        return

    if not CADENCE_DIR.exists():
        print("MISSING_CADENCE_DIR", file=sys.stderr)
        raise SystemExit(1)

    result = run_command([sys.executable, str(INIT_SCRIPT_PATH)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "FAILED_TO_INIT_CADENCE_SCRIPTS_DIR"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def load_scripts_dir():
    result = run_command([sys.executable, str(GETTER_PATH)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "MISSING_CADENCE_SCRIPTS_DIR"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    scripts_dir = result.stdout.strip()
    if not scripts_dir:
        print("MISSING_CADENCE_SCRIPTS_DIR", file=sys.stderr)
        raise SystemExit(1)

    print(scripts_dir)


def main():
    ensure_getter()
    load_scripts_dir()


if __name__ == "__main__":
    main()
