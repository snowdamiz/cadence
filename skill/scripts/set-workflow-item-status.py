#!/usr/bin/env python3
"""Set status for any workflow item in .cadence/cadence.json."""

import argparse
import json
import sys
from pathlib import Path

from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status


CADENCE_DIR = Path(".cadence")
CADENCE_JSON_PATH = CADENCE_DIR / "cadence.json"
VALID_STATUSES = ["pending", "in_progress", "complete", "blocked", "skipped"]


def load_data():
    if not CADENCE_JSON_PATH.exists():
        return default_data()
    try:
        with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)


def save_data(data):
    CADENCE_DIR.mkdir(parents=True, exist_ok=True)
    with CADENCE_JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Set workflow item status in .cadence/cadence.json.")
    parser.add_argument("--id", required=True, help="Workflow item id to update")
    parser.add_argument(
        "--status",
        required=True,
        choices=VALID_STATUSES,
        help="New item status",
    )
    parser.add_argument(
        "--print-workflow",
        action="store_true",
        help="Include full workflow object in the output JSON",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    data = load_data()
    cadence_exists = CADENCE_DIR.exists()

    data = reconcile_workflow_state(data, cadence_dir_exists=cadence_exists)
    data, found = set_workflow_item_status(
        data,
        item_id=args.id,
        status=args.status,
        cadence_dir_exists=cadence_exists,
    )
    if not found:
        print(f"WORKFLOW_ITEM_NOT_FOUND: {args.id}", file=sys.stderr)
        return 2

    save_data(data)

    workflow = data.get("workflow", {})
    result = {
        "status": "ok",
        "item_id": args.id,
        "item_status": args.status,
        "next_phase": workflow.get("next_phase", "complete"),
        "completion_percent": workflow.get("completion_percent", 0),
    }
    if args.print_workflow:
        result["workflow"] = workflow
    else:
        result["summary"] = workflow.get("summary", {})

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
