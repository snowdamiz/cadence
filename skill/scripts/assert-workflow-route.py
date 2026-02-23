#!/usr/bin/env python3
"""Assert that a requested skill matches the current workflow route."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from workflow_state import default_data, reconcile_workflow_state


CADENCE_DIR = Path(".cadence")
CADENCE_JSON_PATH = CADENCE_DIR / "cadence.json"


def load_state() -> dict:
    cadence_exists = CADENCE_DIR.exists()

    if not CADENCE_JSON_PATH.exists():
        data = default_data()
        return reconcile_workflow_state(data, cadence_dir_exists=cadence_exists)

    try:
        with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
            original_data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    return reconcile_workflow_state(copy.deepcopy(original_data), cadence_dir_exists=cadence_exists)


def parse_args(argv: list[str]) -> tuple[str, bool]:
    if not argv or len(argv) > 3:
        print("Usage: assert-workflow-route.py --skill-name <name> [--allow-complete]", file=sys.stderr)
        raise SystemExit(2)

    skill_name = ""
    allow_complete = False
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token == "--skill-name":
            if idx + 1 >= len(argv):
                print("MISSING_SKILL_NAME", file=sys.stderr)
                raise SystemExit(2)
            skill_name = str(argv[idx + 1]).strip()
            idx += 2
            continue
        if token == "--allow-complete":
            allow_complete = True
            idx += 1
            continue

        print(f"UNKNOWN_ARGUMENT: {token}", file=sys.stderr)
        raise SystemExit(2)

    if not skill_name:
        print("MISSING_SKILL_NAME", file=sys.stderr)
        raise SystemExit(2)

    return skill_name, allow_complete


def main() -> int:
    requested_skill, allow_complete = parse_args(sys.argv[1:])
    data = load_state()

    workflow = data.get("workflow", {})
    next_item = workflow.get("next_item", {})
    next_route = workflow.get("next_route", {})

    next_item_id = str(next_item.get("id", "complete")).strip() or "complete"
    next_item_title = str(next_item.get("title", next_item_id)).strip() or next_item_id
    expected_skill = str(next_route.get("skill_name", "")).strip()

    if next_item_id == "complete" and not allow_complete:
        print("WORKFLOW_ALREADY_COMPLETE", file=sys.stderr)
        return 2

    if next_item_id != "complete" and expected_skill != requested_skill:
        expected = expected_skill or "none"
        print(
            (
                "WORKFLOW_ROUTE_MISMATCH: "
                f"expected={expected} "
                f"requested={requested_skill} "
                f"next_item={next_item_id}"
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "requested_skill": requested_skill,
                "expected_skill": expected_skill,
                "next_item_id": next_item_id,
                "next_item_title": next_item_title,
                "workflow_complete": next_item_id == "complete",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
