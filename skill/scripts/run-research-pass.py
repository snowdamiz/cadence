#!/usr/bin/env python3
"""Plan and persist Cadence research passes inside .cadence/cadence.json."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from ideation_research import (
    DEFAULT_RESEARCH_HANDOFF_MESSAGE,
    ensure_ideation_research_defaults,
)
from project_root import resolve_project_root, write_project_root_hint
from workflow_state import reconcile_workflow_state


SCRIPT_DIR = Path(__file__).resolve().parent
ROUTE_GUARD_SCRIPT = SCRIPT_DIR / "assert-workflow-route.py"
CADENCE_JSON_REL = Path(".cadence") / "cadence.json"
PASS_RESULT_TOPIC_STATUSES = {"complete", "needs_followup"}
PASS_RESULT_CONFIDENCE = {"low", "medium", "high"}


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"CADENCE_READ_FAILED: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_CADENCE_JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("CADENCE_PAYLOAD_MUST_BE_OBJECT")
    return payload


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=4) + "\n", encoding="utf-8")


def coerce_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]

    items: list[str] = []
    for raw in raw_values:
        text = coerce_string(raw)
        if text and text not in items:
            items.append(text)
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan and persist Cadence ideation research passes.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show current research execution status")

    start_parser = subparsers.add_parser(
        "start",
        help="Start the next research pass and return pass payload.",
    )
    start_parser.add_argument(
        "--ack-handoff",
        action="store_true",
        help="Acknowledge pending handoff requirement before starting a new pass.",
    )

    complete_parser = subparsers.add_parser(
        "complete",
        help="Complete an in-progress research pass and persist topic findings.",
    )
    complete_parser.add_argument("--pass-id", required=True, help="In-progress pass id")
    complete_group = complete_parser.add_mutually_exclusive_group(required=True)
    complete_group.add_argument("--file", help="Path to pass result JSON payload")
    complete_group.add_argument("--json", help="Inline pass result JSON payload")
    complete_group.add_argument("--stdin", action="store_true", help="Read pass result JSON from stdin")

    return parser.parse_args()


def resolve_root(args: argparse.Namespace) -> Path:
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, _ = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=True,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

    write_project_root_hint(SCRIPT_DIR, project_root)
    return project_root


def assert_researcher_route(project_root: Path) -> None:
    result = run_command(
        [
            sys.executable,
            str(ROUTE_GUARD_SCRIPT),
            "--skill-name",
            "researcher",
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "WORKFLOW_ROUTE_CHECK_FAILED"
        print(detail, file=sys.stderr)
        raise SystemExit(result.returncode)


def cadence_paths(project_root: Path) -> tuple[Path, Path]:
    cadence_dir = project_root / ".cadence"
    cadence_json = cadence_dir / "cadence.json"
    return cadence_dir, cadence_json


def load_state(project_root: Path) -> tuple[dict[str, Any], Path]:
    cadence_dir, cadence_json = cadence_paths(project_root)
    if not cadence_json.exists():
        raise ValueError(f"MISSING_CADENCE_STATE: {cadence_json}")

    data = read_json_file(cadence_json)
    data = reconcile_workflow_state(data, cadence_dir_exists=cadence_dir.exists())
    ideation = ensure_ideation_research_defaults(data.get("ideation", {}))
    data["ideation"] = ideation
    return data, cadence_json


def save_state(project_root: Path, data: dict[str, Any], cadence_json: Path) -> dict[str, Any]:
    cadence_dir = project_root / ".cadence"
    data = reconcile_workflow_state(data, cadence_dir_exists=cadence_dir.exists())
    write_json_file(cadence_json, data)
    return data


def topic_records(agenda: dict[str, Any]) -> dict[str, dict[str, Any]]:
    blocks = agenda.get("blocks")
    if not isinstance(blocks, list):
        return {}

    records: dict[str, dict[str, Any]] = {}
    for block in blocks:
        if not isinstance(block, dict):
            continue

        block_id = coerce_string(block.get("block_id"))
        block_title = coerce_string(block.get("title"))
        topics = block.get("topics")
        if not isinstance(topics, list):
            continue

        for topic in topics:
            if not isinstance(topic, dict):
                continue
            topic_id = coerce_string(topic.get("topic_id"))
            if not topic_id:
                continue
            records[topic_id] = {
                "topic_id": topic_id,
                "title": coerce_string(topic.get("title"), topic_id),
                "category": coerce_string(topic.get("category"), "general"),
                "priority": coerce_string(topic.get("priority"), "medium").lower(),
                "why_it_matters": coerce_string(topic.get("why_it_matters")),
                "research_questions": coerce_string_list(topic.get("research_questions")),
                "keywords": coerce_string_list(topic.get("keywords")),
                "tags": coerce_string_list(topic.get("tags")),
                "related_entities": coerce_string_list(topic.get("related_entities")),
                "block_id": block_id,
                "block_title": block_title,
            }
    return records


def topic_effort(topic: dict[str, Any]) -> int:
    priority = coerce_string(topic.get("priority"), "medium").lower()
    priority_weight = {"low": 1, "medium": 2, "high": 3}.get(priority, 2)
    question_weight = int(math.ceil(len(coerce_string_list(topic.get("research_questions"))) / 2.0))
    keyword_weight = int(math.ceil(len(coerce_string_list(topic.get("keywords"))) / 4.0))
    entity_weight = min(2, len(coerce_string_list(topic.get("related_entities"))))
    return max(1, 1 + priority_weight + question_weight + keyword_weight + entity_weight)


def unresolved_topics(execution: dict[str, Any]) -> list[str]:
    topic_status = execution.get("topic_status")
    if not isinstance(topic_status, dict):
        return []
    return sorted(
        [
            topic_id
            for topic_id, entry in topic_status.items()
            if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") != "complete"
        ]
    )


def sort_topics_for_planning(topic_ids: list[str], topic_map: dict[str, dict[str, Any]], execution: dict[str, Any]) -> list[str]:
    status_map = execution.get("topic_status")
    status_map = status_map if isinstance(status_map, dict) else {}

    status_rank = {"needs_followup": 0, "in_progress": 1, "pending": 2}
    priority_rank = {"high": 0, "medium": 1, "low": 2}

    def sort_key(topic_id: str) -> tuple[int, int, int, str]:
        status = "pending"
        entry = status_map.get(topic_id)
        if isinstance(entry, dict):
            status = coerce_string(entry.get("status"), "pending").lower()

        topic = topic_map.get(topic_id, {})
        priority = coerce_string(topic.get("priority"), "medium").lower()
        return (
            status_rank.get(status, 2),
            priority_rank.get(priority, 1),
            -topic_effort(topic),
            topic_id,
        )

    return sorted(topic_ids, key=sort_key)


def latest_round(execution: dict[str, Any]) -> int:
    planning = execution.get("planning")
    planning = planning if isinstance(planning, dict) else {}
    try:
        round_value = int(planning.get("latest_round", 0))
    except (TypeError, ValueError):
        round_value = 0
    if round_value < 0:
        return 0
    return round_value


def rebuild_pass_queue(execution: dict[str, Any], topic_map: dict[str, dict[str, Any]], timestamp: str) -> None:
    topic_ids = unresolved_topics(execution)
    if not topic_ids:
        execution["pass_queue"] = []
        return

    planning = execution.get("planning")
    if not isinstance(planning, dict):
        planning = {}
        execution["planning"] = planning

    try:
        target_effort = int(planning.get("target_effort_per_pass", 12))
    except (TypeError, ValueError):
        target_effort = 12
    if target_effort < 1:
        target_effort = 1

    try:
        max_topics = int(planning.get("max_topics_per_pass", 4))
    except (TypeError, ValueError):
        max_topics = 4
    if max_topics < 1:
        max_topics = 1

    round_number = latest_round(execution) + 1
    planning["latest_round"] = round_number
    planning["target_effort_per_pass"] = target_effort
    planning["max_topics_per_pass"] = max_topics

    ordered_topics = sort_topics_for_planning(topic_ids, topic_map, execution)
    queue: list[dict[str, Any]] = []

    current_topics: list[str] = []
    current_effort = 0
    pass_index = 1

    for topic_id in ordered_topics:
        topic = topic_map.get(topic_id, {})
        effort = topic_effort(topic)
        should_close = bool(
            current_topics
            and (
                len(current_topics) >= max_topics
                or current_effort + effort > target_effort
            )
        )
        if should_close:
            queue.append(
                {
                    "pass_id": f"pass-r{round_number}-{pass_index:02d}",
                    "round": round_number,
                    "status": "pending",
                    "topic_ids": list(current_topics),
                    "planned_effort": current_effort,
                    "created_at": timestamp,
                    "started_at": "",
                }
            )
            pass_index += 1
            current_topics = []
            current_effort = 0

        current_topics.append(topic_id)
        current_effort += effort

    if current_topics:
        queue.append(
            {
                "pass_id": f"pass-r{round_number}-{pass_index:02d}",
                "round": round_number,
                "status": "pending",
                "topic_ids": list(current_topics),
                "planned_effort": current_effort,
                "created_at": timestamp,
                "started_at": "",
            }
        )

    execution["pass_queue"] = queue


def recompute_execution_summary(execution: dict[str, Any]) -> None:
    topic_status = execution.get("topic_status")
    topic_status = topic_status if isinstance(topic_status, dict) else {}
    queue = execution.get("pass_queue")
    queue = queue if isinstance(queue, list) else []
    history = execution.get("pass_history")
    history = history if isinstance(history, list) else []

    total = len(topic_status)
    complete = len([entry for entry in topic_status.values() if isinstance(entry, dict) and entry.get("status") == "complete"])
    followup = len(
        [
            entry
            for entry in topic_status.values()
            if isinstance(entry, dict) and entry.get("status") == "needs_followup"
        ]
    )
    pending = max(total - complete - followup, 0)

    in_progress = next(
        (
            item
            for item in queue
            if isinstance(item, dict) and coerce_string(item.get("status"), "pending") == "in_progress"
        ),
        None,
    )
    pending_item = next(
        (
            item
            for item in queue
            if isinstance(item, dict) and coerce_string(item.get("status"), "pending") == "pending"
        ),
        None,
    )
    next_pass_id = (
        coerce_string(in_progress.get("pass_id"))
        if isinstance(in_progress, dict)
        else coerce_string(pending_item.get("pass_id")) if isinstance(pending_item, dict) else ""
    )

    if total == 0:
        status = "pending"
    elif complete == total:
        status = "complete"
    elif next_pass_id:
        status = "in_progress"
    else:
        status = "pending"

    execution["status"] = status
    if status == "complete":
        execution["handoff_required"] = False

    execution["summary"] = {
        "topic_total": total,
        "topic_complete": complete,
        "topic_needs_followup": followup,
        "topic_pending": pending,
        "pass_pending": len(queue),
        "pass_complete": len(history),
        "next_pass_id": next_pass_id,
    }


def build_pass_payload(pass_entry: dict[str, Any], topic_map: dict[str, dict[str, Any]], execution: dict[str, Any]) -> dict[str, Any]:
    topic_status = execution.get("topic_status")
    topic_status = topic_status if isinstance(topic_status, dict) else {}
    topic_ids = coerce_string_list(pass_entry.get("topic_ids"))

    topics: list[dict[str, Any]] = []
    for topic_id in topic_ids:
        topic = topic_map.get(topic_id, {})
        status_entry = topic_status.get(topic_id)
        status_entry = status_entry if isinstance(status_entry, dict) else {}
        topics.append(
            {
                "topic_id": topic_id,
                "title": topic.get("title", topic_id),
                "category": topic.get("category", "general"),
                "priority": topic.get("priority", "medium"),
                "why_it_matters": topic.get("why_it_matters", ""),
                "research_questions": list(topic.get("research_questions", [])),
                "keywords": list(topic.get("keywords", [])),
                "tags": list(topic.get("tags", [])),
                "related_entities": list(topic.get("related_entities", [])),
                "block_id": topic.get("block_id", ""),
                "block_title": topic.get("block_title", ""),
                "current_status": status_entry.get("status", "pending"),
                "latest_summary": status_entry.get("latest_summary", ""),
                "unresolved_questions": list(status_entry.get("unresolved_questions", [])),
            }
        )

    return {
        "pass_id": coerce_string(pass_entry.get("pass_id")),
        "round": int(pass_entry.get("round", 0) or 0),
        "planned_effort": int(pass_entry.get("planned_effort", 0) or 0),
        "topic_ids": topic_ids,
        "topics": topics,
    }


def parse_pass_result_payload(args: argparse.Namespace) -> tuple[dict[str, Any], Path | None]:
    payload_file_path: Path | None = None
    if getattr(args, "file", None):
        payload_file_path = Path(args.file)
        try:
            raw = payload_file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"PASS_RESULT_READ_FAILED: {exc}") from exc
    elif getattr(args, "json", None):
        raw = args.json
    else:
        raw = sys.stdin.read()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_PASS_RESULT_JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("PASS_RESULT_PAYLOAD_MUST_BE_OBJECT")
    return payload, payload_file_path


def next_source_id(source_registry: list[dict[str, Any]]) -> str:
    used_ids = {coerce_string(entry.get("source_id")) for entry in source_registry if isinstance(entry, dict)}
    index = 1
    while True:
        candidate = f"source-{index}"
        if candidate not in used_ids:
            return candidate
        index += 1


def register_sources(
    execution: dict[str, Any],
    *,
    pass_id: str,
    topic_id: str,
    source_entries: Any,
    captured_at: str,
) -> list[str]:
    registry = execution.get("source_registry")
    if not isinstance(registry, list):
        registry = []
        execution["source_registry"] = registry

    created_ids: list[str] = []
    entries = source_entries if isinstance(source_entries, list) else []
    for source in entries:
        if not isinstance(source, dict):
            continue
        url = coerce_string(source.get("url"))
        if not url:
            continue

        existing = next(
            (
                entry
                for entry in registry
                if isinstance(entry, dict)
                and coerce_string(entry.get("url")) == url
                and topic_id in coerce_string_list(entry.get("topic_ids"))
            ),
            None,
        )
        if isinstance(existing, dict):
            source_id = coerce_string(existing.get("source_id"))
            if pass_id and not coerce_string(existing.get("pass_id")):
                existing["pass_id"] = pass_id
            created_ids.append(source_id)
            continue

        source_id = next_source_id(registry)
        registry.append(
            {
                "source_id": source_id,
                "url": url,
                "title": coerce_string(source.get("title")),
                "publisher": coerce_string(source.get("publisher")),
                "published_at": coerce_string(source.get("published_at")),
                "notes": coerce_string(source.get("notes")),
                "topic_ids": [topic_id],
                "pass_id": pass_id,
                "captured_at": captured_at,
            }
        )
        created_ids.append(source_id)

    return sorted(set(created_ids))


def require_ideation_ready(data: dict[str, Any]) -> None:
    state = data.get("state")
    state = state if isinstance(state, dict) else {}
    if not bool(state.get("ideation-completed", False)):
        raise ValueError("IDEATION_NOT_COMPLETE")

    ideation = data.get("ideation")
    ideation = ideation if isinstance(ideation, dict) else {}
    agenda = ideation.get("research_agenda")
    agenda = agenda if isinstance(agenda, dict) else {}
    summary = agenda.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    try:
        topic_count = int(summary.get("topic_count", 0))
    except (TypeError, ValueError):
        topic_count = 0
    if topic_count < 1:
        raise ValueError("RESEARCH_TOPICS_REQUIRED")


def handle_status(project_root: Path) -> int:
    try:
        data, _ = load_state(project_root)
        require_ideation_ready(data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ideation = data.get("ideation", {})
    execution = ideation.get("research_execution", {})
    summary = execution.get("summary", {}) if isinstance(execution, dict) else {}
    topic_status = execution.get("topic_status", {}) if isinstance(execution, dict) else {}
    queue = execution.get("pass_queue", []) if isinstance(execution, dict) else []

    in_progress = next(
        (
            entry
            for entry in queue
            if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") == "in_progress"
        ),
        None,
    )
    pending = next(
        (
            entry
            for entry in queue
            if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") == "pending"
        ),
        None,
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "project_root": str(project_root),
                "execution_status": coerce_string(execution.get("status"), "pending"),
                "handoff_required": bool(execution.get("handoff_required", False)),
                "handoff_message": coerce_string(
                    execution.get("handoff_message"),
                    DEFAULT_RESEARCH_HANDOFF_MESSAGE,
                ),
                "summary": summary,
                "current_pass": in_progress,
                "next_pass": pending,
                "topic_status_count": len(topic_status) if isinstance(topic_status, dict) else 0,
            }
        )
    )
    return 0


def handle_start(project_root: Path, args: argparse.Namespace) -> int:
    assert_researcher_route(project_root)

    try:
        data, cadence_json = load_state(project_root)
        require_ideation_ready(data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ideation = data.get("ideation", {})
    execution = ideation.get("research_execution", {})
    execution = execution if isinstance(execution, dict) else {}
    agenda = ideation.get("research_agenda", {})
    agenda = agenda if isinstance(agenda, dict) else {}
    topic_map = topic_records(agenda)
    timestamp = utc_now()

    if bool(execution.get("handoff_required", False)) and not bool(args.ack_handoff):
        print(
            "RESEARCH_HANDOFF_REQUIRED: Start a new chat and say \"continue research\" "
            "before starting the next pass (rerun with --ack-handoff).",
            file=sys.stderr,
        )
        return 2

    queue = execution.get("pass_queue")
    queue = queue if isinstance(queue, list) else []
    current_pass = next(
        (
            entry
            for entry in queue
            if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") == "in_progress"
        ),
        None,
    )

    if not isinstance(current_pass, dict):
        if not queue:
            rebuild_pass_queue(execution, topic_map, timestamp)
            queue = execution.get("pass_queue", [])
        current_pass = next(
            (
                entry
                for entry in queue
                if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") == "pending"
            ),
            None,
        )
        if not isinstance(current_pass, dict):
            recompute_execution_summary(execution)
            if execution.get("status") == "complete":
                data.setdefault("state", {})["research-completed"] = True
                data = save_state(project_root, data, cadence_json)
                print(
                    json.dumps(
                        {
                            "status": "ok",
                            "project_root": str(project_root),
                            "research_complete": True,
                            "summary": execution.get("summary", {}),
                        }
                    )
                )
                return 0
            print("NO_RESEARCH_PASS_AVAILABLE", file=sys.stderr)
            return 2

        current_pass["status"] = "in_progress"
        current_pass["started_at"] = timestamp

    pass_id = coerce_string(current_pass.get("pass_id"))
    topic_status = execution.get("topic_status")
    topic_status = topic_status if isinstance(topic_status, dict) else {}
    for topic_id in coerce_string_list(current_pass.get("topic_ids")):
        entry = topic_status.get(topic_id)
        if not isinstance(entry, dict):
            continue
        if coerce_string(entry.get("status"), "pending") != "complete":
            if entry.get("status") != "needs_followup":
                entry["status"] = "in_progress"
            entry["last_pass_id"] = pass_id
            entry["updated_at"] = timestamp

    execution["handoff_required"] = False
    execution["handoff_message"] = coerce_string(
        execution.get("handoff_message"),
        DEFAULT_RESEARCH_HANDOFF_MESSAGE,
    ) or DEFAULT_RESEARCH_HANDOFF_MESSAGE
    recompute_execution_summary(execution)

    data.setdefault("state", {})["research-completed"] = execution.get("status") == "complete"
    data["ideation"] = ideation
    data = save_state(project_root, data, cadence_json)

    execution = data.get("ideation", {}).get("research_execution", {})
    current_pass_payload = build_pass_payload(current_pass, topic_map, execution)
    print(
        json.dumps(
            {
                "status": "ok",
                "project_root": str(project_root),
                "action": "start",
                "pass": current_pass_payload,
                "summary": execution.get("summary", {}),
                "handoff_required": bool(execution.get("handoff_required", False)),
                "handoff_message": coerce_string(
                    execution.get("handoff_message"),
                    DEFAULT_RESEARCH_HANDOFF_MESSAGE,
                ),
            }
        )
    )
    return 0


def handle_complete(project_root: Path, args: argparse.Namespace) -> int:
    assert_researcher_route(project_root)

    try:
        data, cadence_json = load_state(project_root)
        require_ideation_ready(data)
        payload, payload_file_path = parse_pass_result_payload(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ideation = data.get("ideation", {})
    execution = ideation.get("research_execution", {})
    execution = execution if isinstance(execution, dict) else {}
    agenda = ideation.get("research_agenda", {})
    agenda = agenda if isinstance(agenda, dict) else {}
    topic_map = topic_records(agenda)
    timestamp = utc_now()

    queue = execution.get("pass_queue")
    queue = queue if isinstance(queue, list) else []
    pass_id = coerce_string(args.pass_id)
    pass_entry = next(
        (
            entry
            for entry in queue
            if isinstance(entry, dict)
            and coerce_string(entry.get("pass_id")) == pass_id
            and coerce_string(entry.get("status"), "pending") == "in_progress"
        ),
        None,
    )
    if not isinstance(pass_entry, dict):
        print(f"IN_PROGRESS_PASS_NOT_FOUND: {pass_id}", file=sys.stderr)
        return 2

    pass_topic_ids = coerce_string_list(pass_entry.get("topic_ids"))
    topic_results_raw = payload.get("topics")
    if not isinstance(topic_results_raw, list):
        print("PASS_RESULTS_TOPICS_REQUIRED", file=sys.stderr)
        return 2

    topic_results_index: dict[str, dict[str, Any]] = {}
    for topic_result in topic_results_raw:
        if not isinstance(topic_result, dict):
            continue
        topic_id = coerce_string(topic_result.get("topic_id"))
        if not topic_id:
            continue
        if topic_id not in pass_topic_ids:
            print(f"PASS_RESULT_TOPIC_NOT_IN_PASS: {topic_id}", file=sys.stderr)
            return 2
        if topic_id in topic_results_index:
            print(f"PASS_RESULT_TOPIC_DUPLICATE: {topic_id}", file=sys.stderr)
            return 2
        topic_results_index[topic_id] = topic_result

    missing_topic_ids = [topic_id for topic_id in pass_topic_ids if topic_id not in topic_results_index]
    if missing_topic_ids:
        print(
            "PASS_RESULT_MISSING_TOPICS: " + ", ".join(missing_topic_ids),
            file=sys.stderr,
        )
        return 2

    topic_status = execution.get("topic_status")
    topic_status = topic_status if isinstance(topic_status, dict) else {}
    pass_sources: list[str] = []
    pass_topic_results: list[dict[str, Any]] = []

    for topic_id in pass_topic_ids:
        result = topic_results_index.get(topic_id, {})
        raw_status = coerce_string(result.get("status"), "needs_followup").lower()
        status = raw_status if raw_status in PASS_RESULT_TOPIC_STATUSES else "needs_followup"

        unresolved = coerce_string_list(result.get("unresolved_questions"))
        if status == "complete" and unresolved:
            status = "needs_followup"

        summary = coerce_string(result.get("summary"))
        confidence = coerce_string(result.get("confidence"), "medium").lower()
        if confidence not in PASS_RESULT_CONFIDENCE:
            confidence = "medium"

        source_ids = register_sources(
            execution,
            pass_id=pass_id,
            topic_id=topic_id,
            source_entries=result.get("sources"),
            captured_at=timestamp,
        )
        pass_sources.extend(source_ids)

        entry = topic_status.get(topic_id)
        if not isinstance(entry, dict):
            entry = {
                "topic_id": topic_id,
                "title": topic_map.get(topic_id, {}).get("title", topic_id),
                "status": "pending",
                "passes_attempted": 0,
                "last_pass_id": "",
                "latest_summary": "",
                "unresolved_questions": [],
                "source_ids": [],
                "updated_at": "",
            }
            topic_status[topic_id] = entry

        try:
            passes_attempted = int(entry.get("passes_attempted", 0))
        except (TypeError, ValueError):
            passes_attempted = 0
        if passes_attempted < 0:
            passes_attempted = 0
        entry["passes_attempted"] = passes_attempted + 1
        entry["status"] = status
        entry["last_pass_id"] = pass_id
        entry["latest_summary"] = summary
        entry["unresolved_questions"] = unresolved
        merged_sources = sorted(set(coerce_string_list(entry.get("source_ids")) + source_ids))
        entry["source_ids"] = merged_sources
        entry["updated_at"] = timestamp

        pass_topic_results.append(
            {
                "topic_id": topic_id,
                "status": status,
                "confidence": confidence,
                "summary": summary,
                "unresolved_question_count": len(unresolved),
                "source_ids": source_ids,
            }
        )

    # Normalize any stale in-progress states outside the completed pass.
    for topic_id, entry in topic_status.items():
        if not isinstance(entry, dict):
            continue
        if topic_id in pass_topic_ids:
            continue
        if coerce_string(entry.get("status"), "pending") == "in_progress":
            entry["status"] = "pending"
            entry["updated_at"] = timestamp

    execution["topic_status"] = topic_status

    pass_summary = coerce_string(payload.get("pass_summary"))
    history = execution.get("pass_history")
    history = history if isinstance(history, list) else []
    history.append(
        {
            "pass_id": pass_id,
            "round": int(pass_entry.get("round", 0) or 0),
            "completed_at": timestamp,
            "pass_summary": pass_summary,
            "topics": pass_topic_results,
            "source_ids": sorted(set(pass_sources)),
        }
    )
    execution["pass_history"] = history

    # Remove the completed in-progress pass and dynamically rebuild next passes.
    execution["pass_queue"] = [
        entry
        for entry in queue
        if isinstance(entry, dict) and coerce_string(entry.get("pass_id")) != pass_id
    ]
    rebuild_pass_queue(execution, topic_map, timestamp)

    recompute_execution_summary(execution)
    summary = execution.get("summary", {})
    total = int(summary.get("topic_total", 0))
    complete = int(summary.get("topic_complete", 0))

    state = data.setdefault("state", {})
    state["research-completed"] = bool(total > 0 and complete == total)
    if state["research-completed"]:
        execution["status"] = "complete"
        execution["handoff_required"] = False
    else:
        execution["status"] = "in_progress"
        execution["handoff_required"] = True
        execution["handoff_message"] = coerce_string(
            execution.get("handoff_message"),
            DEFAULT_RESEARCH_HANDOFF_MESSAGE,
        ) or DEFAULT_RESEARCH_HANDOFF_MESSAGE

    recompute_execution_summary(execution)
    data["ideation"] = ideation
    data = save_state(project_root, data, cadence_json)

    payload_deleted = False
    if payload_file_path is not None:
        try:
            payload_file_path.unlink()
            payload_deleted = True
        except OSError as exc:
            print(f"PASS_RESULT_DELETE_FAILED: {exc}", file=sys.stderr)
            return 3

    execution = data.get("ideation", {}).get("research_execution", {})
    print(
        json.dumps(
            {
                "status": "ok",
                "project_root": str(project_root),
                "action": "complete",
                "pass_id": pass_id,
                "pass_summary": pass_summary,
                "payload_deleted": payload_deleted,
                "summary": execution.get("summary", {}),
                "research_complete": bool(data.get("state", {}).get("research-completed", False)),
                "handoff_required": bool(execution.get("handoff_required", False)),
                "handoff_message": coerce_string(
                    execution.get("handoff_message"),
                    DEFAULT_RESEARCH_HANDOFF_MESSAGE,
                ),
            }
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    project_root = resolve_root(args)

    if args.command == "status":
        return handle_status(project_root)
    if args.command == "start":
        return handle_start(project_root, args)
    if args.command == "complete":
        return handle_complete(project_root, args)

    print(f"UNKNOWN_COMMAND: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
