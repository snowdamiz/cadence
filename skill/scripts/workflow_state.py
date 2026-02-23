#!/usr/bin/env python3
"""Utilities for normalizing and routing Cadence workflow state.

This module is intentionally data-driven so workflow plans can scale to an arbitrary
number of milestones, phases, waves, and tasks.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


WORKFLOW_SCHEMA_VERSION = 2
VALID_STATUSES = {"pending", "in_progress", "complete", "blocked", "skipped"}
COMPLETED_STATUSES = {"complete", "skipped"}

ROUTE_KEYS = {"skill_name", "skill_path", "reason"}
DEFAULT_ROUTE_BY_ITEM_ID = {
    "task-scaffold": {
        "skill_name": "scaffold",
        "skill_path": "skills/scaffold/SKILL.md",
        "reason": "Project scaffolding has not completed yet.",
    },
    "task-prerequisite-gate": {
        "skill_name": "prerequisite-gate",
        "skill_path": "skills/prerequisite-gate/SKILL.md",
        "reason": "Prerequisite gate has not passed yet.",
    },
    "task-ideation": {
        "skill_name": "ideator",
        "skill_path": "skills/ideator/SKILL.md",
        "reason": "Ideation has not been completed yet.",
    },
}

DERIVED_WORKFLOW_KEYS = {
    "schema_version",
    "plan",
    "summary",
    "next_item",
    "active_item",
    "next_route",
    "phase_order",
    "phases",
    "completed_phases",
    "active_phase",
    "next_phase",
    "completion_percent",
}


def default_workflow_plan() -> list[dict[str, Any]]:
    """Return the default workflow hierarchy.

    The structure is nested by milestone -> phase -> wave -> task, but this shape can be
    extended or replaced by adding additional entries in `workflow.plan`.
    """

    return [
        {
            "id": "milestone-foundation",
            "kind": "milestone",
            "title": "Foundation",
            "children": [
                {
                    "id": "phase-project-setup",
                    "kind": "phase",
                    "title": "Project Setup",
                    "children": [
                        {
                            "id": "wave-initialize-cadence",
                            "kind": "wave",
                            "title": "Initialize Cadence",
                            "children": [
                                {
                                    "id": "task-scaffold",
                                    "kind": "task",
                                    "title": "Scaffold project",
                                    "route": DEFAULT_ROUTE_BY_ITEM_ID["task-scaffold"],
                                },
                                {
                                    "id": "task-prerequisite-gate",
                                    "kind": "task",
                                    "title": "Run prerequisite gate",
                                    "route": DEFAULT_ROUTE_BY_ITEM_ID["task-prerequisite-gate"],
                                },
                                {
                                    "id": "task-ideation",
                                    "kind": "task",
                                    "title": "Complete ideation",
                                    "route": DEFAULT_ROUTE_BY_ITEM_ID["task-ideation"],
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    ]


def default_data() -> dict[str, Any]:
    data: dict[str, Any] = {
        "prerequisites-pass": False,
        "state": {
            "ideation-completed": False,
            "cadence-scripts-dir": "",
            "repo-enabled": False,
        },
        "project-details": {},
        "ideation": {},
        "workflow": {
            "schema_version": WORKFLOW_SCHEMA_VERSION,
            "plan": default_workflow_plan(),
        },
    }
    return reconcile_workflow_state(data, cadence_dir_exists=False)


def _coerce_status(value: Any) -> str:
    status = str(value).strip().lower()
    if status not in VALID_STATUSES:
        return "pending"
    return status


def _is_complete_status(status: str) -> bool:
    return status in COMPLETED_STATUSES


def _normalize_route(item_id: str, route_value: Any) -> dict[str, str]:
    base = deepcopy(DEFAULT_ROUTE_BY_ITEM_ID.get(item_id, {}))
    if not isinstance(route_value, dict):
        return base

    for key in ROUTE_KEYS:
        raw = route_value.get(key)
        text = str(raw).strip() if raw is not None else ""
        if text:
            base[key] = text

    return base


def _normalize_item(raw_item: Any, fallback_id: str) -> dict[str, Any]:
    item = dict(raw_item) if isinstance(raw_item, dict) else {}

    item_id = str(item.get("id", "")).strip() or fallback_id
    children_raw = item.get("children")
    children_raw = children_raw if isinstance(children_raw, list) else []
    children = [
        _normalize_item(child, f"{item_id}-child-{index + 1}") for index, child in enumerate(children_raw)
    ]

    kind_raw = str(item.get("kind", "")).strip().lower()
    if kind_raw:
        kind = kind_raw
    else:
        kind = "task" if not children else "phase"

    title = str(item.get("title", "")).strip() or item_id
    status = _coerce_status(item.get("status", "pending"))
    route = _normalize_route(item_id, item.get("route"))

    normalized = dict(item)
    normalized["id"] = item_id
    normalized["kind"] = kind
    normalized["title"] = title
    normalized["status"] = status
    normalized["children"] = children
    if route:
        normalized["route"] = route
    else:
        normalized.pop("route", None)
    return normalized


def _normalize_plan(plan: Any) -> list[dict[str, Any]]:
    if not isinstance(plan, list):
        plan = default_workflow_plan()
    return [_normalize_item(item, f"item-{index + 1}") for index, item in enumerate(plan)]


def _set_item_status(items: list[dict[str, Any]], item_id: str, status: str) -> bool:
    found = False
    for item in items:
        if item.get("id") == item_id:
            item["status"] = status
            found = True
        children = item.get("children", [])
        if isinstance(children, list) and _set_item_status(children, item_id, status):
            found = True
    return found


def _find_item_by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    for item in items:
        if item.get("id") == item_id:
            return item
        children = item.get("children", [])
        if isinstance(children, list):
            nested = _find_item_by_id(children, item_id)
            if nested is not None:
                return nested
    return None


def _roll_up_status(item: dict[str, Any]) -> str:
    children = item.get("children", [])
    if not isinstance(children, list) or not children:
        status = _coerce_status(item.get("status", "pending"))
        item["status"] = status
        return status

    child_statuses = [_roll_up_status(child) for child in children]
    if all(_is_complete_status(status) for status in child_statuses):
        status = "complete"
    elif all(status == "pending" for status in child_statuses):
        status = "pending"
    elif any(status == "in_progress" for status in child_statuses):
        status = "in_progress"
    elif any(_is_complete_status(status) for status in child_statuses):
        status = "in_progress"
    elif any(status == "blocked" for status in child_statuses):
        status = "blocked"
    else:
        status = "pending"

    item["status"] = status
    return status


def _roll_up_plan(plan: list[dict[str, Any]]) -> None:
    for item in plan:
        _roll_up_status(item)


def _collect_nodes(
    items: list[dict[str, Any]],
    *,
    parent_path_ids: list[str] | None = None,
    parent_path_titles: list[str] | None = None,
) -> list[dict[str, Any]]:
    if parent_path_ids is None:
        parent_path_ids = []
    if parent_path_titles is None:
        parent_path_titles = []

    nodes: list[dict[str, Any]] = []
    for item in items:
        item_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip() or item_id
        kind = str(item.get("kind", "")).strip() or "task"
        status = _coerce_status(item.get("status", "pending"))
        children = item.get("children", [])
        children = children if isinstance(children, list) else []

        path_ids = [*parent_path_ids, item_id]
        path_titles = [*parent_path_titles, title]
        is_actionable = len(children) == 0

        nodes.append(
            {
                "id": item_id,
                "title": title,
                "kind": kind,
                "status": status,
                "is_actionable": is_actionable,
                "path_ids": path_ids,
                "path_titles": path_titles,
                "item": item,
            }
        )
        nodes.extend(_collect_nodes(children, parent_path_ids=path_ids, parent_path_titles=path_titles))
    return nodes


def _legacy_completion_map(data: dict[str, Any], *, cadence_dir_exists: bool) -> dict[str, bool]:
    state = data.get("state")
    state = state if isinstance(state, dict) else {}
    return {
        "task-scaffold": bool(cadence_dir_exists),
        "task-prerequisite-gate": bool(data.get("prerequisites-pass", False)),
        "task-ideation": bool(state.get("ideation-completed", False)),
    }


def _apply_legacy_task_states(
    plan: list[dict[str, Any]],
    data: dict[str, Any],
    *,
    cadence_dir_exists: bool,
) -> None:
    for item_id, is_complete in _legacy_completion_map(data, cadence_dir_exists=cadence_dir_exists).items():
        _set_item_status(plan, item_id, "complete" if is_complete else "pending")


def _sync_legacy_flags_from_plan(data: dict[str, Any], plan: list[dict[str, Any]]) -> None:
    state = data.setdefault("state", {})
    if not isinstance(state, dict):
        state = {}
        data["state"] = state

    prerequisite_item = _find_item_by_id(plan, "task-prerequisite-gate")
    ideation_item = _find_item_by_id(plan, "task-ideation")

    if prerequisite_item is not None:
        data["prerequisites-pass"] = _is_complete_status(_coerce_status(prerequisite_item.get("status")))
    if ideation_item is not None:
        state["ideation-completed"] = _is_complete_status(_coerce_status(ideation_item.get("status")))


def _build_node_ref(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node["id"],
        "title": node["title"],
        "kind": node["kind"],
        "status": node["status"],
        "path_ids": list(node["path_ids"]),
        "path_titles": list(node["path_titles"]),
    }


def _default_route() -> dict[str, str]:
    return {"skill_name": "", "skill_path": "", "reason": ""}


def _build_route_for_node(node: dict[str, Any]) -> dict[str, str]:
    route = _normalize_route(node["id"], node["item"].get("route"))
    if not route:
        return _default_route()
    if not route.get("reason"):
        route["reason"] = f"Next workflow item '{node['title']}' is not complete."
    return route


def _derive_workflow(workflow_seed: dict[str, Any], plan: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = _collect_nodes(plan)
    actionable_nodes = [node for node in nodes if node["is_actionable"]]
    completed_actionable_nodes = [
        node for node in actionable_nodes if _is_complete_status(_coerce_status(node["status"]))
    ]

    total_actionable = len(actionable_nodes)
    completed_actionable = len(completed_actionable_nodes)
    completion_percent = (
        100 if total_actionable == 0 else int(round((completed_actionable / total_actionable) * 100))
    )

    next_node = next(
        (node for node in actionable_nodes if not _is_complete_status(_coerce_status(node["status"]))),
        None,
    )

    if next_node is None:
        next_item = {
            "id": "complete",
            "title": "Workflow Complete",
            "kind": "state",
            "status": "complete",
            "path_ids": [],
            "path_titles": [],
        }
        next_route = _default_route()
    else:
        next_item = _build_node_ref(next_node)
        next_route = _build_route_for_node(next_node)

    actionable_ids = [node["id"] for node in actionable_nodes]
    phases = {node["id"]: {"status": node["status"]} for node in actionable_nodes}
    completed_actionable_ids = [node["id"] for node in completed_actionable_nodes]

    summary = {
        "total_items": len(nodes),
        "total_actionable_items": total_actionable,
        "completed_actionable_items": completed_actionable,
        "pending_actionable_items": len([node for node in actionable_nodes if node["status"] == "pending"]),
        "in_progress_actionable_items": len(
            [node for node in actionable_nodes if node["status"] == "in_progress"]
        ),
        "blocked_actionable_items": len([node for node in actionable_nodes if node["status"] == "blocked"]),
        "completion_percent": completion_percent,
    }

    workflow = {key: value for key, value in workflow_seed.items() if key not in DERIVED_WORKFLOW_KEYS}
    workflow["schema_version"] = WORKFLOW_SCHEMA_VERSION
    workflow["plan"] = plan
    workflow["summary"] = summary
    workflow["next_item"] = next_item
    workflow["active_item"] = next_item
    workflow["next_route"] = next_route

    # Legacy-friendly computed fields retained for compatibility.
    workflow["phase_order"] = actionable_ids
    workflow["phases"] = phases
    workflow["completed_phases"] = completed_actionable_ids
    workflow["active_phase"] = next_item["id"]
    workflow["next_phase"] = next_item["id"]
    workflow["completion_percent"] = completion_percent
    return workflow


def reconcile_workflow_state(data: dict[str, Any], *, cadence_dir_exists: bool) -> dict[str, Any]:
    """Ensure cadence data contains canonical fields and up-to-date workflow state."""

    if not isinstance(data, dict):
        data = default_data()

    state = data.setdefault("state", {})
    if not isinstance(state, dict):
        state = {}
        data["state"] = state

    if "ideation-completed" not in state:
        state["ideation-completed"] = False
    if "cadence-scripts-dir" not in state:
        state["cadence-scripts-dir"] = ""
    if "repo-enabled" not in state:
        state["repo-enabled"] = False
    else:
        state["repo-enabled"] = bool(state.get("repo-enabled", False))

    if "prerequisites-pass" not in data:
        data["prerequisites-pass"] = False
    if "project-details" not in data or not isinstance(data.get("project-details"), dict):
        data["project-details"] = {}
    if "ideation" not in data or not isinstance(data.get("ideation"), dict):
        data["ideation"] = {}

    workflow_seed = data.get("workflow")
    workflow_seed = dict(workflow_seed) if isinstance(workflow_seed, dict) else {}
    plan = _normalize_plan(workflow_seed.get("plan"))
    _apply_legacy_task_states(plan, data, cadence_dir_exists=cadence_dir_exists)
    _roll_up_plan(plan)

    data["workflow"] = _derive_workflow(workflow_seed, plan)
    return data


def set_workflow_item_status(
    data: dict[str, Any],
    *,
    item_id: str,
    status: str,
    cadence_dir_exists: bool,
) -> tuple[dict[str, Any], bool]:
    """Set status for any workflow item id and return (updated_data, found)."""

    normalized_item_id = str(item_id).strip()
    if not normalized_item_id:
        return data, False

    normalized_status = str(status).strip().lower()
    if normalized_status not in VALID_STATUSES:
        raise ValueError(f"Unsupported status '{status}'.")

    reconciled = reconcile_workflow_state(data, cadence_dir_exists=cadence_dir_exists)
    workflow_seed = reconciled.get("workflow")
    workflow_seed = dict(workflow_seed) if isinstance(workflow_seed, dict) else {}
    plan = _normalize_plan(workflow_seed.get("plan"))

    found = _set_item_status(plan, normalized_item_id, normalized_status)
    if not found:
        return reconciled, False

    _roll_up_plan(plan)
    _sync_legacy_flags_from_plan(reconciled, plan)
    workflow_seed["plan"] = plan
    reconciled["workflow"] = workflow_seed
    reconciled = reconcile_workflow_state(reconciled, cadence_dir_exists=cadence_dir_exists)
    return reconciled, True


def route_for_next_phase(next_phase: str) -> dict[str, str]:
    """Compatibility helper retained for callers using legacy next_phase names."""

    next_phase_key = str(next_phase).strip()
    route = DEFAULT_ROUTE_BY_ITEM_ID.get(next_phase_key, {})
    if not route:
        return _default_route()
    return _normalize_route(next_phase_key, route)
