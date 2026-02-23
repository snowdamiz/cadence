#!/usr/bin/env python3
"""Read or update prerequisite pass state in .cadence/cadence.json."""

import json
import sys
from pathlib import Path

from workflow_state import default_data, reconcile_workflow_state


CADENCE_JSON_PATH = Path(".cadence") / "cadence.json"


def load_data():
    if not CADENCE_JSON_PATH.exists():
        return default_data()
    with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return reconcile_workflow_state(data, cadence_dir_exists=CADENCE_JSON_PATH.parent.exists())


def save_data(data):
    CADENCE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CADENCE_JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def main():
    if len(sys.argv) > 2:
        print("Usage: handle-prerequisite-state.py [0|1]", file=sys.stderr)
        return 2

    if len(sys.argv) == 2 and sys.argv[1] not in {"0", "1"}:
        print("Usage: handle-prerequisite-state.py [0|1]", file=sys.stderr)
        return 2

    data = load_data()

    if len(sys.argv) == 1:
        print("true" if bool(data.get("prerequisites-pass", False)) else "false")
        return 0

    data["prerequisites-pass"] = sys.argv[1] == "1"
    data = reconcile_workflow_state(data, cadence_dir_exists=CADENCE_JSON_PATH.parent.exists())
    save_data(data)
    print("true" if data["prerequisites-pass"] else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
