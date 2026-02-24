#!/usr/bin/env python3
"""Assert that a requested skill matches the current workflow route."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state


SCRIPT_DIR = Path(__file__).resolve().parent


def load_state(project_root: Path, requested_skill: str) -> dict:
    cadence_dir = project_root / ".cadence"
    cadence_json_path = cadence_dir / "cadence.json"
    cadence_exists = cadence_dir.exists()

    if not cadence_json_path.exists():
        if requested_skill != "scaffold":
            print(
                f"MISSING_CADENCE_STATE: project_root={project_root}",
                file=sys.stderr,
            )
            raise SystemExit(2)
        data = default_data()
        # When `.cadence` exists but cadence.json is missing, recover through the
        # scaffold route instead of treating scaffold as already complete.
        return reconcile_workflow_state(data, cadence_dir_exists=False)

    try:
        with cadence_json_path.open("r", encoding="utf-8") as file:
            original_data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc} path={cadence_json_path}", file=sys.stderr)
        raise SystemExit(1)

    return reconcile_workflow_state(copy.deepcopy(original_data), cadence_dir_exists=cadence_exists)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assert that a requested Cadence skill matches the workflow route.",
    )
    parser.add_argument("--skill-name", required=True, help="Requested subskill name.")
    parser.add_argument(
        "--allow-complete",
        action="store_true",
        help="Allow success when workflow is already complete.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested_skill = str(args.skill_name).strip()
    allow_complete = bool(args.allow_complete)
    explicit_project_root = args.project_root.strip() or None

    try:
        project_root, root_source = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=False,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    write_project_root_hint(SCRIPT_DIR, project_root)
    data = load_state(project_root, requested_skill)

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
                f"next_item={next_item_id} "
                f"project_root={project_root}"
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
                "project_root": str(project_root),
                "project_root_source": root_source,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
