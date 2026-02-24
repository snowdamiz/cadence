#!/usr/bin/env python3
"""Read and normalize Cadence workflow state from .cadence/cadence.json."""

import argparse
import copy
import json
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read and normalize Cadence workflow state.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def cadence_paths(project_root: Path) -> tuple[Path, Path]:
    cadence_dir = project_root / ".cadence"
    cadence_json_path = cadence_dir / "cadence.json"
    return cadence_dir, cadence_json_path


def load_state(project_root: Path):
    cadence_dir, cadence_json_path = cadence_paths(project_root)
    cadence_exists = cadence_dir.exists()

    if not cadence_json_path.exists():
        data = default_data()
        # When `.cadence` exists without cadence.json, initialize recovery state
        # with scaffold pending so route guards can re-enter scaffold safely.
        data = reconcile_workflow_state(data, cadence_dir_exists=False)
        if cadence_exists:
            save_state(project_root, data)
        return data

    try:
        with cadence_json_path.open("r", encoding="utf-8") as file:
            original_data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    data = reconcile_workflow_state(copy.deepcopy(original_data), cadence_dir_exists=cadence_exists)
    if data != original_data:
        save_state(project_root, data)
    return data


def save_state(project_root: Path, data):
    cadence_dir, cadence_json_path = cadence_paths(project_root)
    cadence_dir.mkdir(parents=True, exist_ok=True)
    with cadence_json_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def build_response(data, project_root: Path, project_root_source: str):
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
        "project_root": str(project_root),
        "project_root_source": project_root_source,
    }


def main():
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, project_root_source = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=False,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

    write_project_root_hint(SCRIPT_DIR, project_root)
    data = load_state(project_root)
    response = build_response(data, project_root, project_root_source)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
