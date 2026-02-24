#!/usr/bin/env python3
"""Set status for any workflow item in .cadence/cadence.json."""

import argparse
import json
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status


SCRIPT_DIR = Path(__file__).resolve().parent
VALID_STATUSES = ["pending", "in_progress", "complete", "blocked", "skipped"]


def cadence_paths(project_root: Path) -> tuple[Path, Path]:
    cadence_dir = project_root / ".cadence"
    cadence_json_path = cadence_dir / "cadence.json"
    return cadence_dir, cadence_json_path


def load_data(project_root: Path):
    cadence_dir, cadence_json_path = cadence_paths(project_root)
    if not cadence_json_path.exists():
        return default_data()
    try:
        with cadence_json_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc} path={cadence_json_path}", file=sys.stderr)
        raise SystemExit(1)


def save_data(project_root: Path, data):
    cadence_dir, cadence_json_path = cadence_paths(project_root)
    cadence_dir.mkdir(parents=True, exist_ok=True)
    with cadence_json_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Set workflow item status in .cadence/cadence.json.")
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
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
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, _ = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=False,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)
    data = load_data(project_root)
    cadence_exists = (project_root / ".cadence").exists()

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

    save_data(project_root, data)

    workflow = data.get("workflow", {})
    result = {
        "status": "ok",
        "project_root": str(project_root),
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
