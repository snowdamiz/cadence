#!/usr/bin/env python3
"""Resolve Cadence helper scripts dir for the current project.

Behavior:
- If state.cadence-scripts-dir exists in .cadence/cadence.json and points to
  an existing directory, use it.
- If missing or stale but .cadence exists, regenerate project path state by
  running init-cadence-scripts-dir.py from this skill's scripts directory.
- Print the resolved scripts directory to stdout.
"""

import json
import subprocess
import sys
from pathlib import Path


CADENCE_DIR = Path(".cadence")
CADENCE_JSON_PATH = CADENCE_DIR / "cadence.json"
SCRIPT_DIR = Path(__file__).resolve().parent
INIT_SCRIPT_PATH = SCRIPT_DIR / "init-cadence-scripts-dir.py"


def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def initialize_scripts_dir():
    result = run_command([sys.executable, str(INIT_SCRIPT_PATH)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "FAILED_TO_INIT_CADENCE_SCRIPTS_DIR"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def read_scripts_dir_from_cadence_json():
    if not CADENCE_JSON_PATH.exists():
        return ""

    try:
        with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    return str(data.get("state", {}).get("cadence-scripts-dir", "")).strip()


def ensure_scripts_dir():
    if not CADENCE_DIR.exists():
        print("MISSING_CADENCE_DIR", file=sys.stderr)
        raise SystemExit(1)

    scripts_dir = read_scripts_dir_from_cadence_json()
    if scripts_dir and Path(scripts_dir).is_dir():
        return scripts_dir

    initialize_scripts_dir()

    scripts_dir = read_scripts_dir_from_cadence_json()
    if not scripts_dir:
        print("MISSING_CADENCE_SCRIPTS_DIR", file=sys.stderr)
        raise SystemExit(1)

    if not Path(scripts_dir).is_dir():
        print("INVALID_CADENCE_SCRIPTS_DIR", file=sys.stderr)
        raise SystemExit(1)

    return scripts_dir


def main():
    scripts_dir = ensure_scripts_dir()
    print(scripts_dir)


if __name__ == "__main__":
    main()
