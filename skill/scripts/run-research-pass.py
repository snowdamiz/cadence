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
PASS_RESULT_TOPIC_STATUSES = {"complete", "complete_with_caveats", "needs_followup"}
PASS_RESULT_CONFIDENCE = {"low", "medium", "high"}
TOPIC_COMPLETE_STATUSES = {"complete", "complete_with_caveats"}
TOPIC_ACTIVE_STATUSES = {"pending", "in_progress", "needs_followup"}


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


def coerce_positive_int(value: Any, default: int, *, minimum: int = 1) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    if number < minimum:
        return minimum
    return number


def coerce_percent_int(value: Any, default: int, *, minimum: int = 1, maximum: int = 95) -> int:
    number = coerce_positive_int(value, default, minimum=minimum)
    if number > maximum:
        return maximum
    return number


def planning_config(execution: dict[str, Any]) -> dict[str, int]:
    planning = execution.get("planning")
    if not isinstance(planning, dict):
        planning = {}
        execution["planning"] = planning

    config = {
        "target_effort_per_pass": coerce_positive_int(planning.get("target_effort_per_pass", 12), 12),
        "max_topics_per_pass": coerce_positive_int(planning.get("max_topics_per_pass", 4), 4),
        "max_passes_per_topic": coerce_positive_int(planning.get("max_passes_per_topic", 3), 3),
        "max_total_passes": coerce_positive_int(planning.get("max_total_passes", 120), 120),
        "max_passes_per_chat": coerce_positive_int(planning.get("max_passes_per_chat", 6), 6),
        "context_window_tokens": coerce_positive_int(
            planning.get("context_window_tokens", 128000), 128000, minimum=1000
        ),
        "handoff_context_threshold_percent": coerce_percent_int(
            planning.get("handoff_context_threshold_percent", 70), 70
        ),
        "estimated_fixed_tokens_per_chat": coerce_positive_int(
            planning.get("estimated_fixed_tokens_per_chat", 12000), 12000, minimum=0
        ),
        "estimated_tokens_in_overhead_per_pass": coerce_positive_int(
            planning.get("estimated_tokens_in_overhead_per_pass", 1200), 1200, minimum=0
        ),
        "estimated_tokens_out_overhead_per_pass": coerce_positive_int(
            planning.get("estimated_tokens_out_overhead_per_pass", 400), 400, minimum=0
        ),
        "latest_round": coerce_positive_int(planning.get("latest_round", 0), 0, minimum=0),
    }
    planning.update(config)
    return config


def context_threshold_tokens(config: dict[str, int]) -> int:
    budget = config["context_window_tokens"]
    percent = config["handoff_context_threshold_percent"]
    return max(1, int(math.floor((budget * percent) / 100.0)))


def estimate_tokens(value: Any) -> int:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        except (TypeError, ValueError):
            text = coerce_string(value)
    if not text:
        return 0
    # Pragmatic heuristic: ~1 token per 4 characters for mixed English/json text.
    return max(1, int(math.ceil(len(text) / 4.0)))


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
            if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") in TOPIC_ACTIVE_STATUSES
        ]
    )


def sort_topics_for_planning(topic_ids: list[str], topic_map: dict[str, dict[str, Any]], execution: dict[str, Any]) -> list[str]:
    status_map = execution.get("topic_status")
    status_map = status_map if isinstance(status_map, dict) else {}

    status_rank = {"pending": 0, "in_progress": 1, "needs_followup": 2}
    priority_rank = {"high": 0, "medium": 1, "low": 2}

    def sort_key(topic_id: str) -> tuple[int, int, int, int, str]:
        status = "pending"
        passes_attempted = 0
        entry = status_map.get(topic_id)
        if isinstance(entry, dict):
            status = coerce_string(entry.get("status"), "pending").lower()
            passes_attempted = coerce_positive_int(entry.get("passes_attempted", 0), 0, minimum=0)

        topic = topic_map.get(topic_id, {})
        priority = coerce_string(topic.get("priority"), "medium").lower()
        return (
            status_rank.get(status, 2),
            passes_attempted,
            priority_rank.get(priority, 1),
            -topic_effort(topic),
            topic_id,
        )

    return sorted(topic_ids, key=sort_key)


def latest_round(execution: dict[str, Any]) -> int:
    config = planning_config(execution)
    round_candidates = [config.get("latest_round", 0)]

    queue = execution.get("pass_queue")
    if isinstance(queue, list):
        for entry in queue:
            if not isinstance(entry, dict):
                continue
            round_candidates.append(coerce_positive_int(entry.get("round", 0), 0, minimum=0))

    history = execution.get("pass_history")
    if isinstance(history, list):
        for entry in history:
            if not isinstance(entry, dict):
                continue
            round_candidates.append(coerce_positive_int(entry.get("round", 0), 0, minimum=0))

    return max(round_candidates)


def rebuild_pass_queue(execution: dict[str, Any], topic_map: dict[str, dict[str, Any]], timestamp: str) -> None:
    topic_ids = unresolved_topics(execution)
    if not topic_ids:
        execution["pass_queue"] = []
        return

    config = planning_config(execution)
    target_effort = config["target_effort_per_pass"]
    max_topics = config["max_topics_per_pass"]
    round_number = latest_round(execution) + 1
    execution["planning"]["latest_round"] = round_number

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
                    "estimated_tokens_in": 0,
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
                "estimated_tokens_in": 0,
            }
        )

    execution["pass_queue"] = queue


def append_unique_note(items: list[str], note: str) -> list[str]:
    normalized = coerce_string_list(items)
    text = coerce_string(note)
    if text and text not in normalized:
        normalized.append(text)
    return normalized


def mark_topic_complete_with_caveats(
    entry: dict[str, Any],
    *,
    topic_id: str,
    topic_map: dict[str, dict[str, Any]],
    timestamp: str,
    note: str,
) -> None:
    summary = coerce_string(entry.get("latest_summary"))
    if not summary:
        title = coerce_string(topic_map.get(topic_id, {}).get("title"), topic_id)
        summary = f"Accepted with caveats after bounded research for {title}."

    entry["status"] = "complete_with_caveats"
    entry["latest_summary"] = summary
    entry["unresolved_questions"] = append_unique_note(entry.get("unresolved_questions", []), note)
    entry["updated_at"] = timestamp


def enforce_topic_retry_limits(execution: dict[str, Any], topic_map: dict[str, dict[str, Any]], timestamp: str) -> list[str]:
    topic_status = execution.get("topic_status")
    if not isinstance(topic_status, dict):
        return []

    config = planning_config(execution)
    max_passes_per_topic = config["max_passes_per_topic"]
    capped_topic_ids: list[str] = []
    note = (
        f"Pass cap reached ({max_passes_per_topic}); accepting current findings with caveats."
    )

    for topic_id, raw_entry in topic_status.items():
        if not isinstance(raw_entry, dict):
            continue

        status = coerce_string(raw_entry.get("status"), "pending")
        if status not in TOPIC_ACTIVE_STATUSES:
            continue

        passes_attempted = coerce_positive_int(raw_entry.get("passes_attempted", 0), 0, minimum=0)
        if passes_attempted < max_passes_per_topic:
            continue

        mark_topic_complete_with_caveats(
            raw_entry,
            topic_id=topic_id,
            topic_map=topic_map,
            timestamp=timestamp,
            note=note,
        )
        capped_topic_ids.append(topic_id)

    execution["topic_status"] = topic_status
    return sorted(set(capped_topic_ids))


def enforce_total_pass_limit(execution: dict[str, Any], topic_map: dict[str, dict[str, Any]], timestamp: str) -> list[str]:
    history = execution.get("pass_history")
    history = history if isinstance(history, list) else []
    config = planning_config(execution)
    max_total_passes = config["max_total_passes"]
    if len(history) < max_total_passes:
        return []

    topic_status = execution.get("topic_status")
    if not isinstance(topic_status, dict):
        return []

    capped_topic_ids: list[str] = []
    note = (
        f"Total pass cap reached ({max_total_passes}); accepting current findings with caveats."
    )
    for topic_id, raw_entry in topic_status.items():
        if not isinstance(raw_entry, dict):
            continue
        status = coerce_string(raw_entry.get("status"), "pending")
        if status not in TOPIC_ACTIVE_STATUSES:
            continue

        mark_topic_complete_with_caveats(
            raw_entry,
            topic_id=topic_id,
            topic_map=topic_map,
            timestamp=timestamp,
            note=note,
        )
        capped_topic_ids.append(topic_id)

    if capped_topic_ids:
        execution["pass_queue"] = []
        execution["topic_status"] = topic_status
    return sorted(set(capped_topic_ids))


def prune_pass_queue(execution: dict[str, Any]) -> None:
    queue = execution.get("pass_queue")
    if not isinstance(queue, list):
        execution["pass_queue"] = []
        return

    topic_status = execution.get("topic_status")
    topic_status = topic_status if isinstance(topic_status, dict) else {}
    active_topic_ids = {
        topic_id
        for topic_id, entry in topic_status.items()
        if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") in TOPIC_ACTIVE_STATUSES
    }

    filtered_queue: list[dict[str, Any]] = []
    for entry in queue:
        if not isinstance(entry, dict):
            continue
        topic_ids = [topic_id for topic_id in coerce_string_list(entry.get("topic_ids")) if topic_id in active_topic_ids]
        if not topic_ids:
            continue
        status = coerce_string(entry.get("status"), "pending")
        if status not in {"pending", "in_progress"}:
            status = "pending"
        filtered_queue.append(
            {
                "pass_id": coerce_string(entry.get("pass_id")),
                "round": coerce_positive_int(entry.get("round", 0), 0, minimum=0),
                "status": status,
                "topic_ids": topic_ids,
                "planned_effort": coerce_positive_int(entry.get("planned_effort", 0), 0, minimum=0),
                "created_at": coerce_string(entry.get("created_at")),
                "started_at": coerce_string(entry.get("started_at")),
                "estimated_tokens_in": coerce_positive_int(entry.get("estimated_tokens_in", 0), 0, minimum=0),
            }
        )

    execution["pass_queue"] = filtered_queue


def ensure_chat_context(execution: dict[str, Any], *, timestamp: str, reset: bool = False) -> dict[str, Any]:
    config = planning_config(execution)
    raw = execution.get("chat_context")
    raw = raw if isinstance(raw, dict) else {}

    prior_session_index = coerce_positive_int(raw.get("session_index", 0), 0, minimum=0)
    session_index = prior_session_index + 1 if reset else prior_session_index
    fixed_tokens = (
        config["estimated_fixed_tokens_per_chat"]
        if reset
        else coerce_positive_int(
            raw.get("estimated_tokens_fixed", config["estimated_fixed_tokens_per_chat"]),
            config["estimated_fixed_tokens_per_chat"],
            minimum=0,
        )
    )

    passes_completed = 0 if reset else coerce_positive_int(raw.get("passes_completed", 0), 0, minimum=0)
    tokens_in = 0 if reset else coerce_positive_int(raw.get("estimated_tokens_in", 0), 0, minimum=0)
    tokens_out = 0 if reset else coerce_positive_int(raw.get("estimated_tokens_out", 0), 0, minimum=0)

    budget_tokens = config["context_window_tokens"]
    threshold_percent = config["handoff_context_threshold_percent"]
    threshold_tokens = context_threshold_tokens(config)
    tokens_total = fixed_tokens + tokens_in + tokens_out
    estimated_percent = round((tokens_total / float(budget_tokens)) * 100.0, 2)

    chat_context = {
        "session_index": session_index,
        "passes_completed": passes_completed,
        "estimated_tokens_fixed": fixed_tokens,
        "estimated_tokens_in": tokens_in,
        "estimated_tokens_out": tokens_out,
        "estimated_tokens_total": tokens_total,
        "estimated_context_percent": estimated_percent,
        "budget_tokens": budget_tokens,
        "threshold_tokens": threshold_tokens,
        "threshold_percent": threshold_percent,
        "last_reset_at": timestamp if reset else coerce_string(raw.get("last_reset_at")),
        "last_updated_at": timestamp if reset else coerce_string(raw.get("last_updated_at")),
        "last_pass_id": "" if reset else coerce_string(raw.get("last_pass_id")),
        "last_pass_tokens_in": 0 if reset else coerce_positive_int(raw.get("last_pass_tokens_in", 0), 0, minimum=0),
        "last_pass_tokens_out": 0
        if reset
        else coerce_positive_int(raw.get("last_pass_tokens_out", 0), 0, minimum=0),
    }
    execution["chat_context"] = chat_context
    return chat_context


def apply_pass_token_estimate(
    execution: dict[str, Any],
    *,
    pass_id: str,
    estimated_tokens_in: int,
    estimated_tokens_out: int,
    timestamp: str,
) -> dict[str, Any]:
    chat_context = ensure_chat_context(execution, timestamp=timestamp, reset=False)
    chat_context["passes_completed"] = coerce_positive_int(chat_context.get("passes_completed", 0), 0, minimum=0) + 1
    chat_context["estimated_tokens_in"] = (
        coerce_positive_int(chat_context.get("estimated_tokens_in", 0), 0, minimum=0)
        + max(0, estimated_tokens_in)
    )
    chat_context["estimated_tokens_out"] = (
        coerce_positive_int(chat_context.get("estimated_tokens_out", 0), 0, minimum=0)
        + max(0, estimated_tokens_out)
    )
    fixed_tokens = coerce_positive_int(chat_context.get("estimated_tokens_fixed", 0), 0, minimum=0)
    budget_tokens = max(1, coerce_positive_int(chat_context.get("budget_tokens", 128000), 128000))
    total_tokens = fixed_tokens + chat_context["estimated_tokens_in"] + chat_context["estimated_tokens_out"]
    chat_context["estimated_tokens_total"] = total_tokens
    chat_context["estimated_context_percent"] = round((total_tokens / float(budget_tokens)) * 100.0, 2)
    chat_context["last_pass_id"] = pass_id
    chat_context["last_pass_tokens_in"] = max(0, estimated_tokens_in)
    chat_context["last_pass_tokens_out"] = max(0, estimated_tokens_out)
    chat_context["last_updated_at"] = timestamp
    execution["chat_context"] = chat_context
    return chat_context


def handoff_decision(execution: dict[str, Any]) -> tuple[bool, str]:
    config = planning_config(execution)
    chat_context = ensure_chat_context(execution, timestamp=coerce_string(execution.get("updated_at")), reset=False)

    total_tokens = coerce_positive_int(chat_context.get("estimated_tokens_total", 0), 0, minimum=0)
    threshold_tokens = coerce_positive_int(
        chat_context.get("threshold_tokens", context_threshold_tokens(config)),
        context_threshold_tokens(config),
        minimum=1,
    )
    if total_tokens >= threshold_tokens:
        return True, "context_budget"

    passes_completed = coerce_positive_int(chat_context.get("passes_completed", 0), 0, minimum=0)
    if passes_completed >= config["max_passes_per_chat"]:
        return True, "pass_cap"

    return False, ""


def recompute_execution_summary(execution: dict[str, Any]) -> None:
    topic_status = execution.get("topic_status")
    topic_status = topic_status if isinstance(topic_status, dict) else {}
    queue = execution.get("pass_queue")
    queue = queue if isinstance(queue, list) else []
    history = execution.get("pass_history")
    history = history if isinstance(history, list) else []

    total = len(topic_status)
    complete = len(
        [
            entry
            for entry in topic_status.values()
            if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") in TOPIC_COMPLETE_STATUSES
        ]
    )
    caveated = len(
        [
            entry
            for entry in topic_status.values()
            if isinstance(entry, dict) and coerce_string(entry.get("status"), "pending") == "complete_with_caveats"
        ]
    )
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

    config = planning_config(execution)
    default_threshold_tokens = context_threshold_tokens(config)
    chat_context = ensure_chat_context(execution, timestamp=coerce_string(execution.get("updated_at")), reset=False)
    context_budget_tokens = coerce_positive_int(chat_context.get("budget_tokens", config["context_window_tokens"]), config["context_window_tokens"])
    threshold_tokens_value = coerce_positive_int(
        chat_context.get("threshold_tokens", default_threshold_tokens),
        default_threshold_tokens,
    )
    context_threshold_percent = coerce_percent_int(
        chat_context.get("threshold_percent", config.get("handoff_context_threshold_percent", 70)),
        config.get("handoff_context_threshold_percent", 70),
    )
    context_tokens_in = coerce_positive_int(chat_context.get("estimated_tokens_in", 0), 0, minimum=0)
    context_tokens_out = coerce_positive_int(chat_context.get("estimated_tokens_out", 0), 0, minimum=0)
    context_tokens_total = coerce_positive_int(chat_context.get("estimated_tokens_total", 0), 0, minimum=0)
    context_percent_estimate = round((context_tokens_total / float(max(1, context_budget_tokens))) * 100.0, 2)
    context_passes_completed = coerce_positive_int(chat_context.get("passes_completed", 0), 0, minimum=0)

    chat_context["estimated_tokens_total"] = context_tokens_total
    chat_context["estimated_context_percent"] = context_percent_estimate
    chat_context["budget_tokens"] = context_budget_tokens
    chat_context["threshold_tokens"] = threshold_tokens_value
    chat_context["threshold_percent"] = context_threshold_percent
    execution["chat_context"] = chat_context

    execution["summary"] = {
        "topic_total": total,
        "topic_complete": complete,
        "topic_caveated": caveated,
        "topic_needs_followup": followup,
        "topic_pending": pending,
        "pass_pending": len(queue),
        "pass_complete": len(history),
        "next_pass_id": next_pass_id,
        "context_budget_tokens": context_budget_tokens,
        "context_threshold_tokens": threshold_tokens_value,
        "context_threshold_percent": context_threshold_percent,
        "context_tokens_in": context_tokens_in,
        "context_tokens_out": context_tokens_out,
        "context_tokens_total": context_tokens_total,
        "context_percent_estimate": context_percent_estimate,
        "context_passes_completed": context_passes_completed,
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


def parse_pass_result_payload(args: argparse.Namespace) -> tuple[dict[str, Any], Path | None, str]:
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
    return payload, payload_file_path, raw


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
                "handoff_reason": coerce_string(execution.get("handoff_reason")),
                "handoff_message": coerce_string(
                    execution.get("handoff_message"),
                    DEFAULT_RESEARCH_HANDOFF_MESSAGE,
                ),
                "summary": summary,
                "context": execution.get("chat_context", {}) if isinstance(execution, dict) else {},
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
    config = planning_config(execution)

    pending_handoff = bool(execution.get("handoff_required", False))
    handoff_reason = coerce_string(execution.get("handoff_reason")).lower()
    chat_context = ensure_chat_context(execution, timestamp=timestamp, reset=False)
    if pending_handoff and not bool(args.ack_handoff):
        if handoff_reason == "context_budget":
            print(
                "RESEARCH_HANDOFF_REQUIRED: Start a new chat and say \"continue research\" "
                f"before starting the next pass (estimated context {chat_context.get('estimated_context_percent', 0.0)}% "
                f"of {chat_context.get('threshold_percent', config['handoff_context_threshold_percent'])}% threshold; rerun with --ack-handoff).",
                file=sys.stderr,
            )
            return 2
        if handoff_reason == "pass_cap":
            print(
                "RESEARCH_HANDOFF_REQUIRED: Start a new chat and say \"continue research\" "
                f"before starting the next pass (chat pass cap {config['max_passes_per_chat']} reached; rerun with --ack-handoff).",
                file=sys.stderr,
            )
            return 2
        print(
            "RESEARCH_HANDOFF_REQUIRED: Start a new chat and say \"continue research\" "
            "before starting the next pass (rerun with --ack-handoff).",
            file=sys.stderr,
        )
        return 2

    if pending_handoff and bool(args.ack_handoff):
        ensure_chat_context(execution, timestamp=timestamp, reset=True)
        execution["handoff_required"] = False
        execution["handoff_reason"] = ""

    enforce_topic_retry_limits(execution, topic_map, timestamp)
    enforce_total_pass_limit(execution, topic_map, timestamp)
    prune_pass_queue(execution)

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
        if not queue and unresolved_topics(execution):
            rebuild_pass_queue(execution, topic_map, timestamp)
            prune_pass_queue(execution)
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
            execution["updated_at"] = timestamp
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
        if coerce_string(entry.get("status"), "pending") not in TOPIC_COMPLETE_STATUSES:
            if entry.get("status") != "needs_followup":
                entry["status"] = "in_progress"
            entry["last_pass_id"] = pass_id
            entry["updated_at"] = timestamp

    execution["handoff_required"] = False
    execution["handoff_reason"] = ""
    execution["handoff_message"] = coerce_string(
        execution.get("handoff_message"),
        DEFAULT_RESEARCH_HANDOFF_MESSAGE,
    ) or DEFAULT_RESEARCH_HANDOFF_MESSAGE
    pass_payload_preview = build_pass_payload(current_pass, topic_map, execution)
    estimated_tokens_in = coerce_positive_int(current_pass.get("estimated_tokens_in", 0), 0, minimum=0)
    if estimated_tokens_in < 1:
        estimated_tokens_in = (
            estimate_tokens(pass_payload_preview) + config["estimated_tokens_in_overhead_per_pass"]
        )
        current_pass["estimated_tokens_in"] = estimated_tokens_in
    pass_payload_preview["estimated_tokens_in"] = estimated_tokens_in
    execution["updated_at"] = timestamp
    recompute_execution_summary(execution)

    data.setdefault("state", {})["research-completed"] = execution.get("status") == "complete"
    data["ideation"] = ideation
    data = save_state(project_root, data, cadence_json)

    execution = data.get("ideation", {}).get("research_execution", {})
    queue = execution.get("pass_queue")
    queue = queue if isinstance(queue, list) else []
    persisted_pass = next(
        (
            entry
            for entry in queue
            if isinstance(entry, dict) and coerce_string(entry.get("pass_id")) == pass_id
        ),
        None,
    )
    current_pass_payload = build_pass_payload(
        persisted_pass if isinstance(persisted_pass, dict) else current_pass,
        topic_map,
        execution,
    )
    current_pass_payload["estimated_tokens_in"] = coerce_positive_int(
        (persisted_pass if isinstance(persisted_pass, dict) else current_pass).get("estimated_tokens_in", estimated_tokens_in),
        estimated_tokens_in,
        minimum=0,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "project_root": str(project_root),
                "action": "start",
                "pass": current_pass_payload,
                "summary": execution.get("summary", {}),
                "context": execution.get("chat_context", {}),
                "handoff_required": bool(execution.get("handoff_required", False)),
                "handoff_reason": coerce_string(execution.get("handoff_reason")),
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
        payload, payload_file_path, payload_raw = parse_pass_result_payload(args)
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
    config = planning_config(execution)

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
            status = "complete_with_caveats"

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

        passes_attempted = coerce_positive_int(entry.get("passes_attempted", 0), 0, minimum=0)
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
    estimated_tokens_in = coerce_positive_int(pass_entry.get("estimated_tokens_in", 0), 0, minimum=0)
    if estimated_tokens_in < 1:
        estimated_tokens_in = (
            estimate_tokens(
                {
                    "pass_id": pass_id,
                    "topic_ids": pass_topic_ids,
                    "topics": [
                        topic_map.get(topic_id, {})
                        for topic_id in pass_topic_ids
                    ],
                }
            )
            + config["estimated_tokens_in_overhead_per_pass"]
        )
    estimated_tokens_out = estimate_tokens(payload_raw) + config["estimated_tokens_out_overhead_per_pass"]

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
            "estimated_tokens_in": estimated_tokens_in,
            "estimated_tokens_out": estimated_tokens_out,
        }
    )
    execution["pass_history"] = history

    # Remove the completed in-progress pass. Re-plan only at round boundaries.
    execution["pass_queue"] = [
        entry
        for entry in queue
        if isinstance(entry, dict) and coerce_string(entry.get("pass_id")) != pass_id
    ]
    enforce_topic_retry_limits(execution, topic_map, timestamp)
    enforce_total_pass_limit(execution, topic_map, timestamp)
    prune_pass_queue(execution)
    if not execution.get("pass_queue") and unresolved_topics(execution):
        rebuild_pass_queue(execution, topic_map, timestamp)

    execution["updated_at"] = timestamp
    apply_pass_token_estimate(
        execution,
        pass_id=pass_id,
        estimated_tokens_in=estimated_tokens_in,
        estimated_tokens_out=estimated_tokens_out,
        timestamp=timestamp,
    )
    recompute_execution_summary(execution)
    summary = execution.get("summary", {})
    total = int(summary.get("topic_total", 0))
    complete = int(summary.get("topic_complete", 0))

    state = data.setdefault("state", {})
    state["research-completed"] = bool(total > 0 and complete == total)
    if state["research-completed"]:
        execution["status"] = "complete"
        execution["handoff_required"] = False
        execution["handoff_reason"] = ""
    else:
        execution["status"] = "in_progress"
        handoff_required, handoff_reason = handoff_decision(execution)
        execution["handoff_required"] = handoff_required
        execution["handoff_reason"] = handoff_reason
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
                "estimated_tokens_in": estimated_tokens_in,
                "estimated_tokens_out": estimated_tokens_out,
                "summary": execution.get("summary", {}),
                "context": execution.get("chat_context", {}),
                "research_complete": bool(data.get("state", {}).get("research-completed", False)),
                "handoff_required": bool(execution.get("handoff_required", False)),
                "handoff_reason": coerce_string(execution.get("handoff_reason")),
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
