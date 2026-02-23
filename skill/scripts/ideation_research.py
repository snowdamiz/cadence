#!/usr/bin/env python3
"""Helpers for ideation research agenda normalization and validation."""

from __future__ import annotations

import re
from typing import Any


RESEARCH_SCHEMA_VERSION = 1
PRIORITY_LEVELS = {"low", "medium", "high"}
RESEARCH_EXECUTION_SCHEMA_VERSION = 1
RESEARCH_EXECUTION_STATUSES = {"pending", "in_progress", "complete"}
RESEARCH_TOPIC_STATUSES = {"pending", "in_progress", "needs_followup", "complete"}
DEFAULT_RESEARCH_HANDOFF_MESSAGE = 'Start a new chat and say "continue research".'


class ResearchAgendaValidationError(ValueError):
    """Raised when ideation research agenda data is invalid."""


def _string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = [value]

    items: list[str] = []
    for raw in raw_items:
        text = _string(raw)
        if text and text not in items:
            items.append(text)
    return items


def slugify(value: Any, fallback: str) -> str:
    base = _string(value)
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    if slug:
        return slug

    fallback_text = _string(fallback, "item")
    fallback_slug = re.sub(r"[^a-z0-9]+", "-", fallback_text.lower()).strip("-")
    return fallback_slug or "item"


def _unique_id(seed: str, used: set[str]) -> str:
    candidate = seed
    suffix = 2
    while candidate in used:
        candidate = f"{seed}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def default_research_agenda() -> dict[str, Any]:
    return {
        "version": RESEARCH_SCHEMA_VERSION,
        "summary": {
            "block_count": 0,
            "topic_count": 0,
            "entity_count": 0,
        },
        "blocks": [],
        "entity_registry": [],
        "topic_index": {},
    }


def default_research_execution() -> dict[str, Any]:
    return {
        "version": RESEARCH_EXECUTION_SCHEMA_VERSION,
        "status": "pending",
        "planning": {
            "target_effort_per_pass": 12,
            "max_topics_per_pass": 4,
            "latest_round": 0,
        },
        "summary": {
            "topic_total": 0,
            "topic_complete": 0,
            "topic_needs_followup": 0,
            "topic_pending": 0,
            "pass_pending": 0,
            "pass_complete": 0,
            "next_pass_id": "",
        },
        "topic_status": {},
        "pass_queue": [],
        "pass_history": [],
        "source_registry": [],
        "handoff_required": False,
        "handoff_message": DEFAULT_RESEARCH_HANDOFF_MESSAGE,
    }


def _coerce_research_execution_status(value: Any) -> str:
    status = _string(value, "pending").lower()
    if status not in RESEARCH_EXECUTION_STATUSES:
        return "pending"
    return status


def _coerce_research_topic_status(value: Any) -> str:
    status = _string(value, "pending").lower()
    if status not in RESEARCH_TOPIC_STATUSES:
        return "pending"
    return status


def _agenda_topic_index(agenda: dict[str, Any]) -> dict[str, dict[str, Any]]:
    blocks = agenda.get("blocks")
    if not isinstance(blocks, list):
        return {}

    index: dict[str, dict[str, Any]] = {}
    for block in blocks:
        if not isinstance(block, dict):
            continue

        block_id = _string(block.get("block_id"))
        block_title = _string(block.get("title"))
        topics = block.get("topics")
        if not isinstance(topics, list):
            continue

        for topic in topics:
            if not isinstance(topic, dict):
                continue
            topic_id = _string(topic.get("topic_id"))
            if not topic_id:
                continue
            index[topic_id] = {
                "topic_id": topic_id,
                "title": _string(topic.get("title"), topic_id),
                "priority": _string(topic.get("priority"), "medium").lower(),
                "category": _string(topic.get("category"), "general"),
                "research_questions": _string_list(topic.get("research_questions")),
                "keywords": _string_list(topic.get("keywords")),
                "related_entities": _string_list(topic.get("related_entities")),
                "block_id": block_id,
                "block_title": block_title,
            }
    return index


def _normalize_research_execution(agenda: dict[str, Any], raw_execution: Any) -> dict[str, Any]:
    topic_index = _agenda_topic_index(agenda)
    normalized = default_research_execution()
    if not isinstance(raw_execution, dict):
        raw_execution = {}

    normalized["status"] = _coerce_research_execution_status(raw_execution.get("status"))
    normalized["handoff_required"] = bool(raw_execution.get("handoff_required", False))
    handoff_message = _string(raw_execution.get("handoff_message"), DEFAULT_RESEARCH_HANDOFF_MESSAGE)
    normalized["handoff_message"] = handoff_message or DEFAULT_RESEARCH_HANDOFF_MESSAGE

    planning = raw_execution.get("planning")
    planning = dict(planning) if isinstance(planning, dict) else {}
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

    try:
        latest_round = int(planning.get("latest_round", 0))
    except (TypeError, ValueError):
        latest_round = 0
    if latest_round < 0:
        latest_round = 0

    normalized["planning"] = {
        "target_effort_per_pass": target_effort,
        "max_topics_per_pass": max_topics,
        "latest_round": latest_round,
    }

    raw_topic_status = raw_execution.get("topic_status")
    raw_topic_status = dict(raw_topic_status) if isinstance(raw_topic_status, dict) else {}
    topic_status: dict[str, dict[str, Any]] = {}
    for topic_id, topic_meta in topic_index.items():
        existing = raw_topic_status.get(topic_id)
        existing = dict(existing) if isinstance(existing, dict) else {}
        status = _coerce_research_topic_status(existing.get("status"))

        try:
            passes_attempted = int(existing.get("passes_attempted", 0))
        except (TypeError, ValueError):
            passes_attempted = 0
        if passes_attempted < 0:
            passes_attempted = 0

        topic_status[topic_id] = {
            "topic_id": topic_id,
            "title": topic_meta["title"],
            "status": status,
            "passes_attempted": passes_attempted,
            "last_pass_id": _string(existing.get("last_pass_id")),
            "latest_summary": _string(existing.get("latest_summary")),
            "unresolved_questions": _string_list(existing.get("unresolved_questions")),
            "source_ids": _string_list(existing.get("source_ids")),
            "updated_at": _string(existing.get("updated_at")),
        }

    raw_queue = raw_execution.get("pass_queue")
    raw_queue = list(raw_queue) if isinstance(raw_queue, list) else []
    pass_queue: list[dict[str, Any]] = []
    for entry in raw_queue:
        if not isinstance(entry, dict):
            continue
        pass_id = _string(entry.get("pass_id"))
        if not pass_id:
            continue
        topic_ids = [topic_id for topic_id in _string_list(entry.get("topic_ids")) if topic_id in topic_index]
        if not topic_ids:
            continue
        status = _string(entry.get("status"), "pending").lower()
        if status not in {"pending", "in_progress"}:
            status = "pending"

        try:
            round_number = int(entry.get("round", 0))
        except (TypeError, ValueError):
            round_number = 0
        if round_number < 0:
            round_number = 0

        try:
            planned_effort = int(entry.get("planned_effort", 0))
        except (TypeError, ValueError):
            planned_effort = 0
        if planned_effort < 0:
            planned_effort = 0

        pass_queue.append(
            {
                "pass_id": pass_id,
                "round": round_number,
                "status": status,
                "topic_ids": topic_ids,
                "planned_effort": planned_effort,
                "created_at": _string(entry.get("created_at")),
                "started_at": _string(entry.get("started_at")),
            }
        )

    raw_history = raw_execution.get("pass_history")
    raw_history = list(raw_history) if isinstance(raw_history, list) else []
    pass_history: list[dict[str, Any]] = []
    for entry in raw_history:
        if not isinstance(entry, dict):
            continue
        pass_id = _string(entry.get("pass_id"))
        if not pass_id:
            continue
        pass_history.append(dict(entry))

    raw_sources = raw_execution.get("source_registry")
    raw_sources = list(raw_sources) if isinstance(raw_sources, list) else []
    source_registry: list[dict[str, Any]] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        source_id = _string(source.get("source_id"))
        url = _string(source.get("url"))
        if not source_id or not url:
            continue
        source_registry.append(
            {
                "source_id": source_id,
                "url": url,
                "title": _string(source.get("title")),
                "publisher": _string(source.get("publisher")),
                "published_at": _string(source.get("published_at")),
                "notes": _string(source.get("notes")),
                "topic_ids": [topic_id for topic_id in _string_list(source.get("topic_ids")) if topic_id in topic_index],
                "pass_id": _string(source.get("pass_id")),
                "captured_at": _string(source.get("captured_at")),
            }
        )

    normalized["version"] = RESEARCH_EXECUTION_SCHEMA_VERSION
    normalized["topic_status"] = topic_status
    normalized["pass_queue"] = pass_queue
    normalized["pass_history"] = pass_history
    normalized["source_registry"] = source_registry

    total_topics = len(topic_status)
    topic_complete = len([entry for entry in topic_status.values() if entry.get("status") == "complete"])
    topic_needs_followup = len(
        [entry for entry in topic_status.values() if entry.get("status") == "needs_followup"]
    )
    topic_pending = total_topics - topic_complete - topic_needs_followup

    in_progress_queue = [entry for entry in pass_queue if entry.get("status") == "in_progress"]
    pending_queue = [entry for entry in pass_queue if entry.get("status") == "pending"]
    next_pass_id = in_progress_queue[0]["pass_id"] if in_progress_queue else (pending_queue[0]["pass_id"] if pending_queue else "")

    if total_topics == 0:
        execution_status = "pending"
    elif topic_complete == total_topics:
        execution_status = "complete"
    elif in_progress_queue or pending_queue:
        execution_status = "in_progress"
    else:
        execution_status = "pending"

    normalized["status"] = execution_status
    if execution_status == "complete":
        normalized["handoff_required"] = False

    normalized["summary"] = {
        "topic_total": total_topics,
        "topic_complete": topic_complete,
        "topic_needs_followup": topic_needs_followup,
        "topic_pending": max(topic_pending, 0),
        "pass_pending": len(pass_queue),
        "pass_complete": len(pass_history),
        "next_pass_id": next_pass_id,
    }
    return normalized


def ensure_ideation_research_defaults(ideation: Any) -> dict[str, Any]:
    if not isinstance(ideation, dict):
        ideation = {}

    agenda = ideation.get("research_agenda")
    if not isinstance(agenda, dict):
        ideation["research_agenda"] = default_research_agenda()
        ideation["research_execution"] = default_research_execution()
        return ideation

    normalized = dict(agenda)
    normalized["version"] = RESEARCH_SCHEMA_VERSION

    blocks = normalized.get("blocks")
    normalized["blocks"] = blocks if isinstance(blocks, list) else []

    entities = normalized.get("entity_registry")
    normalized["entity_registry"] = entities if isinstance(entities, list) else []

    topic_index = normalized.get("topic_index")
    normalized["topic_index"] = topic_index if isinstance(topic_index, dict) else {}

    summary = normalized.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    summary["block_count"] = len(normalized["blocks"])
    summary["topic_count"] = sum(
        len(block.get("topics", [])) if isinstance(block, dict) and isinstance(block.get("topics"), list) else 0
        for block in normalized["blocks"]
    )
    summary["entity_count"] = len(normalized["entity_registry"])
    normalized["summary"] = summary

    ideation["research_agenda"] = normalized
    ideation["research_execution"] = _normalize_research_execution(
        normalized,
        ideation.get("research_execution"),
    )
    return ideation


def reset_research_execution(ideation: Any) -> dict[str, Any]:
    normalized = ensure_ideation_research_defaults(ideation)
    agenda = normalized.get("research_agenda")
    agenda = dict(agenda) if isinstance(agenda, dict) else default_research_agenda()

    topic_index = _agenda_topic_index(agenda)
    execution = default_research_execution()
    execution["topic_status"] = {
        topic_id: {
            "topic_id": topic_id,
            "title": topic.get("title", topic_id),
            "status": "pending",
            "passes_attempted": 0,
            "last_pass_id": "",
            "latest_summary": "",
            "unresolved_questions": [],
            "source_ids": [],
            "updated_at": "",
        }
        for topic_id, topic in topic_index.items()
    }
    execution["summary"] = {
        "topic_total": len(topic_index),
        "topic_complete": 0,
        "topic_needs_followup": 0,
        "topic_pending": len(topic_index),
        "pass_pending": 0,
        "pass_complete": 0,
        "next_pass_id": "",
    }

    normalized["research_execution"] = execution
    return normalized


def _coerce_entity_refs(raw: Any) -> tuple[list[str], dict[str, str]]:
    refs = []
    if isinstance(raw, (list, tuple, set)):
        refs = list(raw)
    elif raw is not None:
        refs = [raw]

    entity_ids: list[str] = []
    labels: dict[str, str] = {}
    for ref in refs:
        if isinstance(ref, dict):
            label = _string(
                ref.get("label")
                or ref.get("name")
                or ref.get("entity")
                or ref.get("entity_id")
                or ref.get("id")
            )
            seed = _string(ref.get("entity_id") or ref.get("id") or label)
        else:
            label = _string(ref)
            seed = label

        if not seed:
            continue

        entity_id = slugify(seed, "entity")
        if label:
            labels.setdefault(entity_id, label)
        if entity_id not in entity_ids:
            entity_ids.append(entity_id)

    return entity_ids, labels


def _iter_entity_entries(raw_registry: Any) -> list[Any]:
    if isinstance(raw_registry, list):
        return raw_registry
    if isinstance(raw_registry, dict):
        # Accept either object-form entity entries or map-form entity_id -> entry.
        if {"entity_id", "label", "name", "owner_block_id"} & set(raw_registry.keys()):
            return [raw_registry]

        entries: list[Any] = []
        for key, value in raw_registry.items():
            if isinstance(value, dict):
                entry = dict(value)
                entry.setdefault("entity_id", key)
                entries.append(entry)
            else:
                entries.append({"entity_id": key, "label": value})
        return entries
    return []


def _normalize_priority(raw: Any) -> str:
    priority = _string(raw, "medium").lower()
    if priority not in PRIORITY_LEVELS:
        return "medium"
    return priority


def _match_alias(alias: str, haystack: str) -> bool:
    if not alias:
        return False
    pattern = r"\b" + re.escape(alias) + r"\b"
    return re.search(pattern, haystack) is not None


def _ordered_block_choice(block_ids: set[str], block_order: list[str]) -> str:
    if not block_ids:
        return ""
    order_index = {block_id: index for index, block_id in enumerate(block_order)}
    return sorted(block_ids, key=lambda item: order_index.get(item, len(order_index)))[0]


def normalize_ideation_research(
    ideation: Any,
    *,
    require_topics: bool,
) -> dict[str, Any]:
    if not isinstance(ideation, dict):
        raise ResearchAgendaValidationError("IDEATION_PAYLOAD_MUST_BE_OBJECT")

    agenda_raw = ideation.get("research_agenda")
    if not isinstance(agenda_raw, dict):
        if require_topics:
            raise ResearchAgendaValidationError(
                "MISSING_RESEARCH_AGENDA: ideation.research_agenda is required when ideation is complete."
            )
        ideation["research_agenda"] = default_research_agenda()
        return ideation

    blocks_raw = agenda_raw.get("blocks")
    if not isinstance(blocks_raw, list):
        blocks_raw = []

    used_block_ids: set[str] = set()
    used_topic_ids: set[str] = set()
    block_order: list[str] = []
    block_titles: dict[str, str] = {}
    referenced_entity_labels: dict[str, str] = {}

    normalized_blocks: list[dict[str, Any]] = []
    flat_topics: list[dict[str, Any]] = []

    for block_index, raw_block in enumerate(blocks_raw, start=1):
        block = dict(raw_block) if isinstance(raw_block, dict) else {"title": raw_block}
        title = _string(block.get("title") or block.get("name"), f"Research Block {block_index}")
        block_id_seed = slugify(
            block.get("block_id") or block.get("id") or title,
            f"block-{block_index}",
        )
        block_id = _unique_id(block_id_seed, used_block_ids)

        rationale = _string(block.get("rationale") or block.get("why") or block.get("why_this_matters"))
        tags = _string_list(block.get("tags"))

        topics_raw = block.get("topics") if isinstance(block.get("topics"), list) else []
        normalized_topics: list[dict[str, Any]] = []

        for topic_index, raw_topic in enumerate(topics_raw, start=1):
            topic = dict(raw_topic) if isinstance(raw_topic, dict) else {"title": raw_topic}
            topic_title = _string(topic.get("title") or topic.get("topic"), f"Topic {topic_index}")
            topic_id_seed = slugify(
                topic.get("topic_id") or topic.get("id") or topic_title,
                f"{block_id}-topic-{topic_index}",
            )
            topic_id = _unique_id(topic_id_seed, used_topic_ids)

            related_entities, labels = _coerce_entity_refs(
                topic.get("related_entities")
                or topic.get("entity_ids")
                or topic.get("entities")
                or topic.get("entity")
            )
            referenced_entity_labels.update(labels)

            normalized_topic = {
                "topic_id": topic_id,
                "title": topic_title,
                "category": _string(topic.get("category"), "general"),
                "priority": _normalize_priority(topic.get("priority")),
                "why_it_matters": _string(topic.get("why_it_matters") or topic.get("rationale")),
                "research_questions": _string_list(topic.get("research_questions")),
                "keywords": _string_list(topic.get("keywords")),
                "tags": _string_list(topic.get("tags")),
                "related_entities": related_entities,
            }
            normalized_topics.append(normalized_topic)
            flat_topics.append({"block_id": block_id, "block_title": title, "topic": normalized_topic})

        normalized_block = {
            "block_id": block_id,
            "title": title,
            "rationale": rationale,
            "tags": tags,
            "topics": normalized_topics,
        }
        normalized_blocks.append(normalized_block)
        block_order.append(block_id)
        block_titles[block_id] = title

    raw_registry_entries = _iter_entity_entries(agenda_raw.get("entity_registry"))
    normalized_entities: list[dict[str, Any]] = []
    entity_index: dict[str, dict[str, Any]] = {}

    for raw_entry in raw_registry_entries:
        entry = dict(raw_entry) if isinstance(raw_entry, dict) else {"label": raw_entry}
        label = _string(entry.get("label") or entry.get("name") or entry.get("entity_id") or entry.get("id"))
        seed = _string(entry.get("entity_id") or entry.get("id") or label)
        if not seed:
            continue

        entity_id = slugify(seed, "entity")
        aliases = _string_list(entry.get("aliases"))
        if label and label not in aliases:
            aliases.insert(0, label)

        owner_seed = _string(entry.get("owner_block_id") or entry.get("owner"))
        owner_block_id = slugify(owner_seed, owner_seed) if owner_seed else ""
        if owner_block_id and owner_block_id not in block_titles:
            raise ResearchAgendaValidationError(
                f"UNKNOWN_ENTITY_OWNER_BLOCK: entity '{entity_id}' references unknown block '{owner_seed}'."
            )

        current = entity_index.get(entity_id)
        if current is None:
            normalized = {
                "entity_id": entity_id,
                "label": label or referenced_entity_labels.get(entity_id, entity_id.replace("-", " ").title()),
                "kind": _string(entry.get("kind") or entry.get("type"), "entity"),
                "aliases": aliases,
                "owner_block_id": owner_block_id,
            }
            entity_index[entity_id] = normalized
            normalized_entities.append(normalized)
            continue

        # Merge duplicate entity entries deterministically.
        if not current["owner_block_id"] and owner_block_id:
            current["owner_block_id"] = owner_block_id
        if current["owner_block_id"] and owner_block_id and current["owner_block_id"] != owner_block_id:
            raise ResearchAgendaValidationError(
                f"ENTITY_OWNER_CONFLICT: entity '{entity_id}' has conflicting owner blocks."
            )
        for alias in aliases:
            if alias not in current["aliases"]:
                current["aliases"].append(alias)

    for entity_id, label in referenced_entity_labels.items():
        if entity_id in entity_index:
            continue
        normalized = {
            "entity_id": entity_id,
            "label": label,
            "kind": "entity",
            "aliases": [label] if label else [],
            "owner_block_id": "",
        }
        entity_index[entity_id] = normalized
        normalized_entities.append(normalized)

    alias_lookup: dict[str, set[str]] = {}
    for entity in normalized_entities:
        alias_values = list(entity.get("aliases", []))
        label_value = _string(entity.get("label"))
        if label_value:
            alias_values.append(label_value)

        for alias in alias_values:
            normalized_alias = alias.strip().lower()
            # Keep auto-detection conservative to avoid accidental entity linkage.
            if len(normalized_alias) < 3:
                continue
            alias_lookup.setdefault(normalized_alias, set()).add(entity["entity_id"])

    # Track block usage from explicit topic references before alias inference.
    entity_blocks: dict[str, set[str]] = {}
    entity_topic_refs: dict[str, list[tuple[str, str]]] = {}
    for topic_ref in flat_topics:
        block_id = topic_ref["block_id"]
        topic_id = _string(topic_ref["topic"].get("topic_id"))
        for entity_id in topic_ref["topic"]["related_entities"]:
            entity_blocks.setdefault(entity_id, set()).add(block_id)
            entity_topic_refs.setdefault(entity_id, []).append((block_id, topic_id))

    for topic_ref in flat_topics:
        topic = topic_ref["topic"]
        topic_block_id = topic_ref["block_id"]
        topic_id = _string(topic.get("topic_id"))
        haystack = " ".join(
            [
                _string(topic.get("title")),
                " ".join(_string_list(topic.get("keywords"))),
                " ".join(_string_list(topic.get("tags"))),
            ]
        ).lower()

        detected_ids: list[str] = []
        for alias in sorted(alias_lookup.keys(), key=len, reverse=True):
            matches = alias_lookup[alias]
            if len(matches) != 1:
                continue
            if not _match_alias(alias, haystack):
                continue
            entity_id = next(iter(matches))
            if entity_id not in detected_ids:
                detected_ids.append(entity_id)

        for entity_id in detected_ids:
            if entity_id in topic["related_entities"]:
                continue

            entity = entity_index.get(entity_id)
            if entity is None:
                continue

            owner_block_id = _string(entity.get("owner_block_id"))
            referenced_blocks = entity_blocks.get(entity_id, set())
            # Alias inference is advisory only and must never introduce cross-block links.
            if owner_block_id and owner_block_id != topic_block_id:
                continue
            if referenced_blocks and topic_block_id not in referenced_blocks:
                continue

            topic["related_entities"].append(entity_id)
            entity_blocks.setdefault(entity_id, set()).add(topic_block_id)
            entity_topic_refs.setdefault(entity_id, []).append((topic_block_id, topic_id))

    for entity in normalized_entities:
        entity_id = entity["entity_id"]
        referenced_blocks = entity_blocks.get(entity_id, set())
        owner_block_id = _string(entity.get("owner_block_id"))

        if len(referenced_blocks) > 1:
            refs = ", ".join(
                sorted(
                    f"{topic_id}@{block_id}"
                    for block_id, topic_id in entity_topic_refs.get(entity_id, [])
                    if block_id and topic_id
                )
            )
            raise ResearchAgendaValidationError(
                f"ENTITY_BLOCK_CONFLICT: entity '{entity_id}' is referenced across multiple blocks "
                f"({', '.join(sorted(referenced_blocks))})."
                f"{f' References: {refs}.' if refs else ''}"
            )

        if owner_block_id:
            if owner_block_id not in block_titles:
                raise ResearchAgendaValidationError(
                    f"UNKNOWN_ENTITY_OWNER_BLOCK: entity '{entity_id}' references unknown block '{owner_block_id}'."
                )
            if referenced_blocks and owner_block_id not in referenced_blocks:
                block_label = _ordered_block_choice(referenced_blocks, block_order)
                refs = ", ".join(
                    sorted(
                        f"{topic_id}@{block_id}"
                        for block_id, topic_id in entity_topic_refs.get(entity_id, [])
                        if block_id and topic_id
                    )
                )
                raise ResearchAgendaValidationError(
                    f"ENTITY_OWNER_MISMATCH: entity '{entity_id}' owner block '{owner_block_id}' "
                    f"does not match referenced block '{block_label}'."
                    f"{f' References: {refs}.' if refs else ''}"
                )
        elif referenced_blocks:
            entity["owner_block_id"] = _ordered_block_choice(referenced_blocks, block_order)

    topic_index: dict[str, dict[str, Any]] = {}
    for block in normalized_blocks:
        block_id = block["block_id"]
        block_title = block["title"]
        for topic in block["topics"]:
            for entity_id in topic["related_entities"]:
                entity = entity_index.get(entity_id)
                if entity is None:
                    raise ResearchAgendaValidationError(
                        f"UNKNOWN_ENTITY_REFERENCE: topic '{topic['topic_id']}' references '{entity_id}'."
                    )
                owner_block_id = _string(entity.get("owner_block_id"))
                if owner_block_id and owner_block_id != block_id:
                    raise ResearchAgendaValidationError(
                        f"ENTITY_BLOCK_MISMATCH: topic '{topic['topic_id']}' references entity '{entity_id}' "
                        f"owned by '{owner_block_id}' but is placed in '{block_id}'."
                    )
                if not owner_block_id:
                    entity["owner_block_id"] = block_id

            topic_index[topic["topic_id"]] = {
                "topic_id": topic["topic_id"],
                "title": topic["title"],
                "block_id": block_id,
                "block_title": block_title,
                "category": topic["category"],
                "priority": topic["priority"],
                "tags": list(topic["tags"]),
                "keywords": list(topic["keywords"]),
                "related_entities": list(topic["related_entities"]),
            }

    topic_count = len(topic_index)
    if require_topics and topic_count == 0:
        raise ResearchAgendaValidationError(
            "RESEARCH_TOPICS_REQUIRED: ideation.research_agenda.blocks must contain at least one topic."
        )

    normalized_entities.sort(key=lambda entry: entry["entity_id"])

    ideation["research_agenda"] = {
        "version": RESEARCH_SCHEMA_VERSION,
        "summary": {
            "block_count": len(normalized_blocks),
            "topic_count": topic_count,
            "entity_count": len(normalized_entities),
        },
        "blocks": normalized_blocks,
        "entity_registry": normalized_entities,
        "topic_index": {key: topic_index[key] for key in sorted(topic_index.keys())},
    }
    return ideation
