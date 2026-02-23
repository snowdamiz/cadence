#!/usr/bin/env python3
"""Run Cadence scaffold gate in one deterministic command."""

import json
import subprocess
import sys
from pathlib import Path


CADENCE_JSON_PATH = Path(".cadence") / "cadence.json"
SCRIPT_DIR = Path(__file__).resolve().parent
SCAFFOLD_SCRIPT = SCRIPT_DIR / "scaffold-project.sh"
INIT_SCRIPT = SCRIPT_DIR / "init-cadence-scripts-dir.py"


def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def run_scaffold():
    result = run_command(["bash", str(SCAFFOLD_SCRIPT)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "SCAFFOLD_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    return result.stdout.strip() or "scaffold-created"


def initialize_scripts_dir():
    result = run_command([sys.executable, str(INIT_SCRIPT)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or "INIT_CADENCE_SCRIPTS_DIR_FAILED"
        print(stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def verify_expected_state():
    if not CADENCE_JSON_PATH.exists():
        print("CADENCE_JSON_MISSING", file=sys.stderr)
        raise SystemExit(1)

    try:
        with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
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
    scaffold_status = run_scaffold()
    initialize_scripts_dir()
    scripts_dir = verify_expected_state()
    print(
        json.dumps(
            {
                "status": "ok",
                "scaffold_status": scaffold_status,
                "cadence_scripts_dir": scripts_dir,
            }
        )
    )


if __name__ == "__main__":
    main()
