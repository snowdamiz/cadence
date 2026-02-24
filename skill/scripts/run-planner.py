#!/usr/bin/env python3
"""Discover and persist roadmap planning for greenfield Cadence projects."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status


SCRIPT_DIR = Path(__file__).resolve().parent
ROUTE_GUARD_SCRIPT = SCRIPT_DIR / "assert-workflow-route.py"
FUZZY_QUERY_SCRIPT = SCRIPT_DIR / "query-json-fuzzy.py"
CADENCE_JSON_REL = Path(".cadence") / "cadence.json"
DETAIL_LEVEL = "milestone_phase_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover and persist Cadence roadmap planning.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser(
        "discover",
        help="Extract planning-ready context from cadence state.",
    )
    discover.add_argument(
        "--fuzzy-query",
        action="append",
        default=[],
        help="Optional fuzzy query text to search against cadence.json (repeatable).",
    )
    discover.add_argument(
        "--fuzzy-threshold",
        type=float,
        default=0.76,
        help="Minimum fuzzy score threshold when using --fuzzy-query (default: 0.76).",
    )
    discover.add_argument(
        "--fuzzy-limit",
        type=int,
        default=8,
        help="Maximum results per fuzzy query (default: 8).",
    )
    discover.add_argument(
        "--fuzzy-field",
        action="append",
        default=[],
        help="Optional field path pattern passed to query-json-fuzzy.py --field (repeatable).",
    )

    complete = subparsers.add_parser(
        "complete",
        help="Persist roadmap planning payload and advance workflow.",
    )
    payload_group = complete.add_mutually_exclusive_group(required=True)
    payload_group.add_argument("--file", help="Path to planner payload JSON file")
    payload_group.add_argument("--json", help="Inline planner payload JSON")
    payload_group.add_argument("--stdin", action="store_true", help="Read planner payload JSON from stdin")

    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def assert_expected_route(project_root: Path) -> None:
    result = run_command(
        [
            sys.executable,
            str(ROUTE_GUARD_SCRIPT),
            "--skill-name",
            "planner",
            "--project-root",
            str(project_root),
        ],
        project_root,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "WORKFLOW_ROUTE_CHECK_FAILED"
        print(detail, file=sys.stderr)
        raise SystemExit(result.returncode)


def cadence_json_path(project_root: Path) -> Path:
    return project_root / CADENCE_JSON_REL


def load_state(project_root: Path) -> dict[str, Any]:
    state_path = cadence_json_path(project_root)
    if not state_path.exists():
        return default_data()

    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc} path={state_path}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(payload, dict):
        return default_data()
    return reconcile_workflow_state(payload, cadence_dir_exists=True)


def save_state(project_root: Path, data: dict[str, Any]) -> None:
    path = cadence_json_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")


def _coerce_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _coerce_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]

    values: list[str] = []
    for raw in raw_values:
        text = _coerce_text(raw)
        if text and text not in values:
            values.append(text)
    return values


def _slug_token(value: Any, fallback: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", _coerce_text(value).lower()).strip("-")
    if token:
        return token
    fallback_token = re.sub(r"[^a-z0-9]+", "-", _coerce_text(fallback).lower()).strip("-")
    return fallback_token or "item"


def ensure_planner_prerequisites(data: dict[str, Any]) -> None:
    state = data.get("state")
    state = state if isinstance(state, dict) else {}
    mode = _coerce_text(state.get("project-mode", "unknown")).lower()
    if mode != "greenfield":
        raise ValueError(f"PLANNER_REQUIRES_GREENFIELD_MODE: project-mode={mode or 'unknown'}")
    if not bool(state.get("ideation-completed", False)):
        raise ValueError("IDEATION_NOT_COMPLETE")
    if not bool(state.get("research-completed", False)):
        raise ValueError("RESEARCH_NOT_COMPLETE")


def planning_contract() -> dict[str, Any]:
    return {
        "detail_level": DETAIL_LEVEL,
        "required_fields": ["summary", "milestones"],
        "optional_fields": ["assumptions"],
        "milestone_fields": [
            "milestone_id",
            "title",
            "objective",
            "success_criteria",
            "phases",
        ],
        "phase_fields": [
            "phase_id",
            "title",
            "objective",
            "deliverables",
            "exit_criteria",
            "notes",
        ],
        "constraints": [
            "At least one milestone is required.",
            "Each milestone must include at least one phase.",
            "Do not include waves or tasks in this planner version.",
        ],
    }


def summarize_context(data: dict[str, Any]) -> dict[str, Any]:
    ideation = data.get("ideation")
    ideation = ideation if isinstance(ideation, dict) else {}
    agenda = ideation.get("research_agenda")
    agenda = agenda if isinstance(agenda, dict) else {}
    agenda_summary = agenda.get("summary")
    agenda_summary = agenda_summary if isinstance(agenda_summary, dict) else {}
    execution = ideation.get("research_execution")
    execution = execution if isinstance(execution, dict) else {}
    execution_summary = execution.get("summary")
    execution_summary = execution_summary if isinstance(execution_summary, dict) else {}
    blocks = agenda.get("blocks")
    blocks = blocks if isinstance(blocks, list) else []
    pass_history = execution.get("pass_history")
    pass_history = pass_history if isinstance(pass_history, list) else []

    block_summaries: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        topics = block.get("topics")
        topics = topics if isinstance(topics, list) else []
        topic_titles = [
            _coerce_text(topic.get("title", ""))
            for topic in topics
            if isinstance(topic, dict) and _coerce_text(topic.get("title", ""))
        ]
        block_summaries.append(
            {
                "block_id": _coerce_text(block.get("block_id")),
                "title": _coerce_text(block.get("title")),
                "rationale": _coerce_text(block.get("rationale")),
                "topic_count": len(topics),
                "topic_titles": topic_titles[:8],
            }
        )

    recent_passes: list[dict[str, Any]] = []
    for entry in pass_history[-4:]:
        if not isinstance(entry, dict):
            continue
        topics = entry.get("topics")
        topics = topics if isinstance(topics, list) else []
        recent_passes.append(
            {
                "pass_id": _coerce_text(entry.get("pass_id")),
                "completed_at": _coerce_text(entry.get("completed_at")),
                "pass_summary": _coerce_text(entry.get("pass_summary")),
                "topic_count": len(topics),
            }
        )

    planning = data.get("planning")
    planning = planning if isinstance(planning, dict) else {}
    milestones = planning.get("milestones")
    milestones = milestones if isinstance(milestones, list) else []

    return {
        "objective": _coerce_text(ideation.get("objective")),
        "core_outcome": _coerce_text(ideation.get("core_outcome")),
        "target_audience": ideation.get("target_audience", ""),
        "in_scope": _coerce_text_list(ideation.get("in_scope")),
        "out_of_scope": _coerce_text_list(ideation.get("out_of_scope")),
        "constraints": _coerce_text_list(ideation.get("constraints")),
        "risks": _coerce_text_list(ideation.get("risks")),
        "success_signals": _coerce_text_list(ideation.get("success_signals")),
        "research_agenda_summary": {
            "block_count": int(agenda_summary.get("block_count", 0) or 0),
            "topic_count": int(agenda_summary.get("topic_count", 0) or 0),
            "entity_count": int(agenda_summary.get("entity_count", 0) or 0),
        },
        "research_execution_summary": {
            "topic_total": int(execution_summary.get("topic_total", 0) or 0),
            "topic_complete": int(execution_summary.get("topic_complete", 0) or 0),
            "pass_complete": int(execution_summary.get("pass_complete", 0) or 0),
        },
        "research_blocks": block_summaries,
        "recent_research_passes": recent_passes,
        "existing_plan_summary": {
            "status": _coerce_text(planning.get("status", "pending")),
            "detail_level": _coerce_text(planning.get("detail_level")),
            "milestone_count": len(milestones),
            "updated_at": _coerce_text(planning.get("updated_at")),
        },
        "planner_payload_contract": planning_contract(),
    }


def run_fuzzy_queries(args: argparse.Namespace, project_root: Path) -> list[dict[str, Any]]:
    queries = [query for query in (_coerce_text(value) for value in args.fuzzy_query) if query]
    if not queries:
        return []

    threshold = float(args.fuzzy_threshold)
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError("INVALID_FUZZY_THRESHOLD: must be between 0.0 and 1.0")

    limit = int(args.fuzzy_limit)
    if limit < 1:
        raise ValueError("INVALID_FUZZY_LIMIT: must be >= 1")

    fields = [field for field in (_coerce_text(value) for value in args.fuzzy_field) if field]
    cadence_path = cadence_json_path(project_root)
    responses: list[dict[str, Any]] = []

    for query in queries:
        command = [
            sys.executable,
            str(FUZZY_QUERY_SCRIPT),
            "--file",
            str(cadence_path),
            "--text",
            query,
            "--threshold",
            str(threshold),
            "--limit",
            str(limit),
        ]
        for field in fields:
            command.extend(["--field", field])

        result = run_command(command, project_root)
        if result.returncode != 0:
            responses.append(
                {
                    "query": query,
                    "status": "error",
                    "error": result.stderr.strip() or result.stdout.strip() or "FUZZY_QUERY_FAILED",
                }
            )
            continue

        raw = result.stdout.strip()
        if not raw:
            responses.append(
                {
                    "query": query,
                    "status": "error",
                    "error": "FUZZY_QUERY_EMPTY_OUTPUT",
                }
            )
            continue

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            responses.append(
                {
                    "query": query,
                    "status": "error",
                    "error": f"FUZZY_QUERY_INVALID_JSON: {exc}",
                }
            )
            continue

        responses.append(
            {
                "query": query,
                "status": "ok",
                "summary": payload.get("summary", {}),
                "results": payload.get("results", []),
            }
        )

    return responses


def parse_payload(args: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    if args.file:
        payload_path = Path(args.file).expanduser()
        if not payload_path.is_absolute():
            payload_path = (project_root / payload_path).resolve()
        try:
            raw = payload_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"PAYLOAD_READ_FAILED: {exc}") from exc
    elif args.json:
        raw = args.json
    else:
        raw = sys.stdin.read()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_PAYLOAD_JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("PLANNER_PAYLOAD_MUST_BE_OBJECT")
    return payload


def normalize_phase(raw_phase: Any, *, fallback_index: int, milestone_seed: str) -> dict[str, Any]:
    phase = dict(raw_phase) if isinstance(raw_phase, dict) else {}
    if phase.get("waves") is not None or phase.get("tasks") is not None:
        raise ValueError("PHASE_WAVES_AND_TASKS_NOT_ALLOWED_IN_V1")

    phase_id_raw = phase.get("phase_id", phase.get("id", ""))
    title = _coerce_text(phase.get("title")) or f"Phase {fallback_index}"
    phase_id = _slug_token(phase_id_raw, f"{milestone_seed}-phase-{fallback_index}")

    return {
        "phase_id": phase_id,
        "title": title,
        "objective": _coerce_text(phase.get("objective")),
        "deliverables": _coerce_text_list(phase.get("deliverables")),
        "exit_criteria": _coerce_text_list(phase.get("exit_criteria")),
        "notes": _coerce_text(phase.get("notes")),
    }


def normalize_milestone(raw_milestone: Any, *, fallback_index: int) -> dict[str, Any]:
    milestone = dict(raw_milestone) if isinstance(raw_milestone, dict) else {}
    if milestone.get("waves") is not None or milestone.get("tasks") is not None:
        raise ValueError("MILESTONE_WAVES_AND_TASKS_NOT_ALLOWED_IN_V1")

    milestone_id_raw = milestone.get("milestone_id", milestone.get("id", ""))
    title = _coerce_text(milestone.get("title")) or f"Milestone {fallback_index}"
    milestone_id = _slug_token(milestone_id_raw, f"milestone-{fallback_index}")

    raw_phases = milestone.get("phases")
    if not isinstance(raw_phases, list) or not raw_phases:
        raise ValueError(f"MILESTONE_PHASES_REQUIRED: milestone_id={milestone_id}")

    phases: list[dict[str, Any]] = []
    seen_phase_ids: set[str] = set()
    for index, raw_phase in enumerate(raw_phases, start=1):
        normalized_phase = normalize_phase(raw_phase, fallback_index=index, milestone_seed=milestone_id)
        phase_id = normalized_phase["phase_id"]
        if phase_id in seen_phase_ids:
            raise ValueError(f"DUPLICATE_PHASE_ID: {phase_id}")
        seen_phase_ids.add(phase_id)
        phases.append(normalized_phase)

    return {
        "milestone_id": milestone_id,
        "title": title,
        "objective": _coerce_text(milestone.get("objective")),
        "success_criteria": _coerce_text_list(milestone.get("success_criteria")),
        "phases": phases,
    }


def normalize_planning_payload(payload: dict[str, Any], *, current_planning: dict[str, Any]) -> dict[str, Any]:
    seed = payload.get("planning")
    seed = seed if isinstance(seed, dict) else payload

    detail_level = _coerce_text(seed.get("detail_level", DETAIL_LEVEL)) or DETAIL_LEVEL
    if detail_level != DETAIL_LEVEL:
        raise ValueError(f"UNSUPPORTED_DETAIL_LEVEL: {detail_level}")

    raw_milestones = seed.get("milestones")
    if not isinstance(raw_milestones, list) or not raw_milestones:
        raise ValueError("PLANNER_MILESTONES_REQUIRED")

    milestones: list[dict[str, Any]] = []
    seen_milestones: set[str] = set()
    for index, raw_milestone in enumerate(raw_milestones, start=1):
        milestone = normalize_milestone(raw_milestone, fallback_index=index)
        milestone_id = milestone["milestone_id"]
        if milestone_id in seen_milestones:
            raise ValueError(f"DUPLICATE_MILESTONE_ID: {milestone_id}")
        seen_milestones.add(milestone_id)
        milestones.append(milestone)

    created_at = _coerce_text(current_planning.get("created_at")) or utc_now()
    return {
        "version": 1,
        "status": "complete",
        "detail_level": detail_level,
        "decomposition_pending": True,
        "created_at": created_at,
        "updated_at": utc_now(),
        "summary": _coerce_text(seed.get("summary")),
        "assumptions": _coerce_text_list(seed.get("assumptions")),
        "milestones": milestones,
    }


def discover_flow(args: argparse.Namespace, project_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    ensure_planner_prerequisites(data)
    fuzzy_results = run_fuzzy_queries(args, project_root)

    return {
        "status": "ok",
        "mode": "greenfield",
        "action": "discover",
        "project_root": str(project_root),
        "context": summarize_context(data),
        "fuzzy_context": fuzzy_results,
    }


def complete_flow(args: argparse.Namespace, project_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    ensure_planner_prerequisites(data)
    payload = parse_payload(args, project_root)

    planning_seed = data.get("planning")
    planning_seed = planning_seed if isinstance(planning_seed, dict) else {}
    normalized = normalize_planning_payload(payload, current_planning=planning_seed)
    data["planning"] = normalized

    data, found = set_workflow_item_status(
        data,
        item_id="task-roadmap-planning",
        status="complete",
        cadence_dir_exists=True,
    )
    if not found:
        raise ValueError("WORKFLOW_ITEM_NOT_FOUND: task-roadmap-planning")

    data = reconcile_workflow_state(data, cadence_dir_exists=True)
    save_state(project_root, data)

    milestones = normalized.get("milestones")
    milestones = milestones if isinstance(milestones, list) else []
    phase_count = sum(
        len(milestone.get("phases", []))
        for milestone in milestones
        if isinstance(milestone, dict) and isinstance(milestone.get("phases"), list)
    )

    return {
        "status": "ok",
        "mode": "greenfield",
        "action": "complete",
        "project_root": str(project_root),
        "planning_summary": {
            "detail_level": normalized.get("detail_level", DETAIL_LEVEL),
            "milestone_count": len(milestones),
            "phase_count": phase_count,
            "decomposition_pending": bool(normalized.get("decomposition_pending", True)),
        },
        "next_route": data.get("workflow", {}).get("next_route", {}),
    }


def main() -> int:
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, project_root_source = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=True,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)
    assert_expected_route(project_root)
    data = load_state(project_root)

    try:
        if args.command == "discover":
            response = discover_flow(args, project_root, data)
        else:
            response = complete_flow(args, project_root, data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    response["project_root_source"] = project_root_source
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
