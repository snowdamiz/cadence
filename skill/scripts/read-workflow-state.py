#!/usr/bin/env python3
"""Read and normalize Cadence workflow state from .cadence/cadence.json."""

import copy
import json
import sys
from pathlib import Path

from workflow_state import default_data, reconcile_workflow_state


CADENCE_DIR = Path(".cadence")
CADENCE_JSON_PATH = CADENCE_DIR / "cadence.json"


def load_state():
    cadence_exists = CADENCE_DIR.exists()

    if not CADENCE_JSON_PATH.exists():
        data = default_data()
        data = reconcile_workflow_state(data, cadence_dir_exists=cadence_exists)
        if cadence_exists:
            save_state(data)
        return data

    try:
        with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
            original_data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    data = reconcile_workflow_state(copy.deepcopy(original_data), cadence_dir_exists=cadence_exists)
    if data != original_data:
        save_state(data)
    return data


def save_state(data):
    CADENCE_DIR.mkdir(parents=True, exist_ok=True)
    with CADENCE_JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def build_response(data):
    workflow = data.get("workflow", {})
    next_item = workflow.get("next_item", {})
    route = workflow.get("next_route", {"skill_name": "", "skill_path": "", "reason": ""})

    next_item_id = str(next_item.get("id", "complete"))
    next_item_kind = str(next_item.get("kind", "item"))
    next_item_title = str(next_item.get("title", next_item_id))

    if next_item_id == "complete":
        message = "All tracked workflow items are complete."
    elif route.get("skill_name") and route.get("skill_path"):
        message = (
            f"Next workflow item is {next_item_kind} '{next_item_title}'. "
            f"Route to {route['skill_name']}."
        )
    else:
        message = f"Next workflow item is {next_item_kind} '{next_item_title}'."

    return {
        "status": "ok",
        "workflow": workflow,
        "next_item": next_item,
        "next_phase": str(workflow.get("next_phase", next_item_id)),
        "route": route,
        "message": message,
    }


def main():
    data = load_state()
    response = build_response(data)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
