#!/usr/bin/env python3
"""Persist Cadence helper scripts directory in .cadence/cadence.json."""

import json
from pathlib import Path

from workflow_state import default_data, reconcile_workflow_state


CADENCE_DIR = Path(".cadence")
CADENCE_JSON_PATH = CADENCE_DIR / "cadence.json"


def load_data():
    if not CADENCE_JSON_PATH.exists():
        return default_data()
    with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return reconcile_workflow_state(data, cadence_dir_exists=CADENCE_DIR.exists())


def save_data(data):
    CADENCE_DIR.mkdir(parents=True, exist_ok=True)
    with CADENCE_JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def main():
    if not CADENCE_DIR.exists():
        print("MISSING_CADENCE_DIR")
        return 1

    scripts_dir = str(Path(__file__).resolve().parent)

    data = load_data()
    state = data.setdefault("state", {})
    state["cadence-scripts-dir"] = scripts_dir
    data = reconcile_workflow_state(data, cadence_dir_exists=CADENCE_DIR.exists())
    save_data(data)

    print(json.dumps({"status": "ok", "cadence_scripts_dir": scripts_dir}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
