#!/usr/bin/env python3
"""Read-only project overview for Cadence roadmap and progress."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state


SCRIPT_DIR = Path(__file__).resolve().parent
CADENCE_JSON_REL = Path(".cadence") / "cadence.json"
VALID_STATUSES = {"pending", "in_progress", "complete", "blocked", "skipped"}
ROADMAP_KINDS = ("milestone", "phase", "wave", "task")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read Cadence project overview and roadmap progress.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _status(value: Any) -> str:
    status = _text(value).lower()
    if status not in VALID_STATUSES:
        return "pending"
    return status


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def cadence_paths(project_root: Path) -> tuple[Path, Path]:
    cadence_dir = project_root / ".cadence"
    cadence_json = cadence_dir / "cadence.json"
    return cadence_dir, cadence_json


def load_state(project_root: Path) -> dict[str, Any]:
    cadence_dir, cadence_json = cadence_paths(project_root)
    cadence_exists = cadence_dir.exists()

    if not cadence_json.exists():
        return reconcile_workflow_state(default_data(), cadence_dir_exists=cadence_exists)

    try:
        payload = json.loads(cadence_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(payload, dict):
        payload = default_data()
    return reconcile_workflow_state(copy.deepcopy(payload), cadence_dir_exists=cadence_exists)


def init_level_summary() -> dict[str, dict[str, int | str]]:
    return {
        kind: {
            "level": kind,
            "total": 0,
            "complete": 0,
            "in_progress": 0,
            "pending": 0,
            "blocked": 0,
            "skipped": 0,
        }
        for kind in ROADMAP_KINDS
    }


def collect_workflow_roadmap(plan: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    level_summary = init_level_summary()
    node_lookup: dict[str, dict[str, Any]] = {}

    def walk(
        items: Any,
        *,
        context: dict[str, str],
        path_ids: list[str],
        path_titles: list[str],
    ) -> None:
        for raw in _list(items):
            if not isinstance(raw, dict):
                continue

            item_id = _text(raw.get("id"))
            title = _text(raw.get("title")) or item_id
            kind = _text(raw.get("kind")).lower() or "task"
            status = _status(raw.get("status"))
            route = raw.get("route")
            route = route if isinstance(route, dict) else {}
            children = _list(raw.get("children"))

            next_context = dict(context)
            if kind in ROADMAP_KINDS:
                next_context[kind] = title
                level_row = level_summary.get(kind)
                if isinstance(level_row, dict):
                    level_row["total"] = int(level_row["total"]) + 1
                    level_row[status] = int(level_row.get(status, 0)) + 1

            next_path_ids = [*path_ids, item_id]
            next_path_titles = [*path_titles, title]
            node_lookup[item_id] = {
                "id": item_id,
                "title": title,
                "kind": kind,
                "status": status,
                "path_ids": next_path_ids,
                "path_titles": next_path_titles,
            }

            if children:
                walk(
                    children,
                    context=next_context,
                    path_ids=next_path_ids,
                    path_titles=next_path_titles,
                )
                continue

            rows.append(
                {
                    "milestone": _text(next_context.get("milestone")),
                    "phase": _text(next_context.get("phase")),
                    "wave": _text(next_context.get("wave")),
                    "task": _text(next_context.get("task")) or title,
                    "task_id": item_id,
                    "status": status,
                    "route_skill_name": _text(route.get("skill_name")),
                    "route_skill_path": _text(route.get("skill_path")),
                    "is_current": False,
                }
            )

    walk(plan, context={}, path_ids=[], path_titles=[])
    ordered_summary = [level_summary[kind] for kind in ROADMAP_KINDS]
    return rows, ordered_summary, node_lookup


def compute_current_position(
    *,
    workflow: dict[str, Any],
    node_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    next_item = workflow.get("next_item")
    next_item = next_item if isinstance(next_item, dict) else {}
    next_route = workflow.get("next_route")
    next_route = next_route if isinstance(next_route, dict) else {}
    next_item_id = _text(next_item.get("id", "complete"))

    if next_item_id == "complete":
        return {
            "milestone": "",
            "phase": "",
            "wave": "",
            "task": "Workflow Complete",
            "task_id": "complete",
            "status": "complete",
            "path_titles": [],
            "route_skill_name": "",
            "route_skill_path": "",
            "route_reason": "",
        }

    path_ids = next_item.get("path_ids")
    path_ids = path_ids if isinstance(path_ids, list) else []
    kind_titles: dict[str, str] = {}
    for raw_path_id in path_ids:
        path_id = _text(raw_path_id)
        node = node_lookup.get(path_id)
        if not isinstance(node, dict):
            continue
        kind = _text(node.get("kind")).lower()
        if kind in ROADMAP_KINDS:
            kind_titles[kind] = _text(node.get("title"))

    return {
        "milestone": _text(kind_titles.get("milestone")),
        "phase": _text(kind_titles.get("phase")),
        "wave": _text(kind_titles.get("wave")),
        "task": _text(kind_titles.get("task")) or _text(next_item.get("title")) or next_item_id,
        "task_id": next_item_id,
        "status": _status(next_item.get("status")),
        "path_titles": next_item.get("path_titles") if isinstance(next_item.get("path_titles"), list) else [],
        "route_skill_name": _text(next_route.get("skill_name")),
        "route_skill_path": _text(next_route.get("skill_path")),
        "route_reason": _text(next_route.get("reason")),
    }


def planning_outline_rows(planning: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    milestones = planning.get("milestones")
    milestones = milestones if isinstance(milestones, list) else []
    rows: list[dict[str, Any]] = []
    phase_total = 0
    for raw_milestone in milestones:
        if not isinstance(raw_milestone, dict):
            continue
        milestone_id = _text(raw_milestone.get("milestone_id"))
        milestone_title = _text(raw_milestone.get("title")) or milestone_id
        phases = raw_milestone.get("phases")
        phases = phases if isinstance(phases, list) else []
        phase_titles: list[str] = []
        for raw_phase in phases:
            if not isinstance(raw_phase, dict):
                continue
            phase_id = _text(raw_phase.get("phase_id"))
            phase_title = _text(raw_phase.get("title")) or phase_id
            if phase_title:
                phase_titles.append(phase_title)
        phase_total += len(phases)
        rows.append(
            {
                "milestone_id": milestone_id,
                "milestone_title": milestone_title,
                "phase_count": len(phases),
                "phase_names": "; ".join(phase_titles),
            }
        )
    return rows, phase_total


def build_response(data: dict[str, Any], *, project_root: Path, project_root_source: str) -> dict[str, Any]:
    state = data.get("state")
    state = state if isinstance(state, dict) else {}
    ideation = data.get("ideation")
    ideation = ideation if isinstance(ideation, dict) else {}
    planning = data.get("planning")
    planning = planning if isinstance(planning, dict) else {}
    workflow = data.get("workflow")
    workflow = workflow if isinstance(workflow, dict) else {}

    plan = workflow.get("plan")
    rows, level_summary, node_lookup = collect_workflow_roadmap(plan)
    current_position = compute_current_position(workflow=workflow, node_lookup=node_lookup)
    current_task_id = _text(current_position.get("task_id"))
    if current_task_id and current_task_id != "complete":
        for row in rows:
            if _text(row.get("task_id")) == current_task_id:
                row["is_current"] = True

    planning_outline, planning_phase_count = planning_outline_rows(planning)
    planning_assumptions = planning.get("assumptions")
    planning_assumptions = planning_assumptions if isinstance(planning_assumptions, list) else []

    summary = workflow.get("summary")
    summary = summary if isinstance(summary, dict) else {}

    project_summary = {
        "project_mode": _text(state.get("project-mode", "unknown")) or "unknown",
        "repo_enabled": bool(state.get("repo-enabled", False)),
        "ideation_completed": bool(state.get("ideation-completed", False)),
        "research_completed": bool(state.get("research-completed", False)),
        "planning_status": _text(planning.get("status", "pending")) or "pending",
        "planning_detail_level": _text(planning.get("detail_level")) or "none",
        "planning_summary": _text(planning.get("summary")),
        "objective": _text(ideation.get("objective")),
        "core_outcome": _text(ideation.get("core_outcome")),
    }

    return {
        "status": "ok",
        "action": "overview",
        "project_root": str(project_root),
        "project_root_source": project_root_source,
        "project_summary": project_summary,
        "workflow_summary": {
            "completion_percent": int(summary.get("completion_percent", 0) or 0),
            "total_actionable_items": int(summary.get("total_actionable_items", 0) or 0),
            "completed_actionable_items": int(summary.get("completed_actionable_items", 0) or 0),
            "pending_actionable_items": int(summary.get("pending_actionable_items", 0) or 0),
            "in_progress_actionable_items": int(summary.get("in_progress_actionable_items", 0) or 0),
            "blocked_actionable_items": int(summary.get("blocked_actionable_items", 0) or 0),
        },
        "current_position": current_position,
        "roadmap_level_summary": level_summary,
        "roadmap_rows": rows,
        "planning_summary": {
            "status": _text(planning.get("status", "pending")) or "pending",
            "detail_level": _text(planning.get("detail_level")),
            "milestone_count": len(planning_outline),
            "phase_count": planning_phase_count,
            "assumption_count": len(planning_assumptions),
            "decomposition_pending": bool(planning.get("decomposition_pending", True)),
        },
        "planning_outline": planning_outline,
    }


def main() -> int:
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
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)
    data = load_state(project_root)
    response = build_response(data, project_root=project_root, project_root_source=project_root_source)
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
