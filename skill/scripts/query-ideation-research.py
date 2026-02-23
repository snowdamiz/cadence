#!/usr/bin/env python3
"""Query ideation research agenda data with granular filters."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ideation_research import ResearchAgendaValidationError, normalize_ideation_research, slugify


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query ideation research agenda by block, topic, entity, and metadata filters."
    )
    parser.add_argument(
        "--file",
        default=str(Path(".cadence") / "cadence.json"),
        help="Path to cadence.json or a raw ideation payload JSON file",
    )
    parser.add_argument("--block-id", help="Filter by research block id")
    parser.add_argument("--topic-id", help="Filter by topic id")
    parser.add_argument("--entity", help="Filter by entity id, label, or alias")
    parser.add_argument("--category", help="Filter by topic category")
    parser.add_argument("--tag", help="Filter by topic or block tag")
    parser.add_argument("--priority", choices=["high", "medium", "low"], help="Filter by priority")
    parser.add_argument("--text", help="Case-insensitive text search across topic and block fields")
    parser.add_argument(
        "--include-related",
        action="store_true",
        help="Include related owner block and linked entity details",
    )
    return parser.parse_args()


def read_payload(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"PAYLOAD_READ_FAILED: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_PAYLOAD_JSON: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError("PAYLOAD_MUST_BE_OBJECT")

    if isinstance(raw_data.get("ideation"), dict):
        return dict(raw_data.get("ideation", {})), "cadence"
    return raw_data, "ideation"


def _lower(value: Any) -> str:
    return str(value).strip().lower()


def _searchable_text(block: dict[str, Any], topic: dict[str, Any]) -> str:
    fields = [
        topic.get("title", ""),
        topic.get("category", ""),
        topic.get("why_it_matters", ""),
        " ".join(topic.get("research_questions", []) or []),
        " ".join(topic.get("keywords", []) or []),
        " ".join(topic.get("tags", []) or []),
        block.get("title", ""),
        block.get("rationale", ""),
        " ".join(block.get("tags", []) or []),
    ]
    return " ".join(str(value) for value in fields).lower()


def _resolve_entity_id(raw_entity: str, entity_registry: list[dict[str, Any]]) -> tuple[str, list[str]]:
    requested = _lower(raw_entity)
    requested_slug = slugify(requested, requested)

    by_id: dict[str, dict[str, Any]] = {entry.get("entity_id", ""): entry for entry in entity_registry}
    if requested_slug in by_id:
        return requested_slug, []

    alias_matches: list[str] = []
    for entry in entity_registry:
        entity_id = entry.get("entity_id", "")
        labels = [entry.get("label", ""), *list(entry.get("aliases", []) or [])]
        normalized = {_lower(label) for label in labels if str(label).strip()}
        if requested in normalized:
            alias_matches.append(entity_id)

    unique_matches = sorted({match for match in alias_matches if match})
    if len(unique_matches) == 1:
        return unique_matches[0], []
    if len(unique_matches) > 1:
        return "", unique_matches
    return "", []


def main() -> int:
    args = parse_args()
    payload_path = Path(args.file)

    try:
        ideation_payload, source_type = read_payload(payload_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        ideation_payload = normalize_ideation_research(ideation_payload, require_topics=False)
    except ResearchAgendaValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    agenda = ideation_payload.get("research_agenda", {})
    blocks = agenda.get("blocks", []) if isinstance(agenda, dict) else []
    entity_registry = agenda.get("entity_registry", []) if isinstance(agenda, dict) else []

    block_filter = slugify(args.block_id, args.block_id) if args.block_id else ""
    topic_filter = slugify(args.topic_id, args.topic_id) if args.topic_id else ""

    entity_filter_id = ""
    ambiguous_entities: list[str] = []
    if args.entity:
        entity_filter_id, ambiguous_entities = _resolve_entity_id(args.entity, entity_registry)
        if ambiguous_entities:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "code": "AMBIGUOUS_ENTITY_FILTER",
                        "entity": args.entity,
                        "matches": ambiguous_entities,
                    }
                ),
                file=sys.stderr,
            )
            return 2
        if not entity_filter_id:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "code": "ENTITY_NOT_FOUND",
                        "entity": args.entity,
                    }
                ),
                file=sys.stderr,
            )
            return 2

    flat_topics: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("block_id", "")).strip()
        topics = block.get("topics", []) if isinstance(block.get("topics"), list) else []
        for topic in topics:
            if not isinstance(topic, dict):
                continue
            flat_topics.append(
                {
                    "block_id": block_id,
                    "block_title": block.get("title", ""),
                    "block_rationale": block.get("rationale", ""),
                    "block_tags": list(block.get("tags", []) or []),
                    "topic": topic,
                }
            )

    matched_topics: list[dict[str, Any]] = []
    for entry in flat_topics:
        topic = entry["topic"]
        topic_id = str(topic.get("topic_id", "")).strip()

        if block_filter and entry["block_id"] != block_filter:
            continue
        if topic_filter and topic_id != topic_filter:
            continue
        if entity_filter_id and entity_filter_id not in list(topic.get("related_entities", []) or []):
            continue
        if args.category and _lower(topic.get("category")) != _lower(args.category):
            continue
        if args.priority and _lower(topic.get("priority")) != _lower(args.priority):
            continue
        if args.tag:
            tag_value = _lower(args.tag)
            topic_tags = {_lower(tag) for tag in list(topic.get("tags", []) or [])}
            block_tags = {_lower(tag) for tag in entry["block_tags"]}
            if tag_value not in topic_tags and tag_value not in block_tags:
                continue
        if args.text:
            if _lower(args.text) not in _searchable_text(
                {
                    "title": entry["block_title"],
                    "rationale": entry["block_rationale"],
                    "tags": entry["block_tags"],
                },
                topic,
            ):
                continue

        matched_topics.append(entry)

    matched_topic_ids = {entry["topic"].get("topic_id", "") for entry in matched_topics}
    matched_block_ids = {entry["block_id"] for entry in matched_topics}
    topic_level_filter_active = bool(
        topic_filter
        or entity_filter_id
        or args.category
        or args.tag
        or args.priority
        or args.text
    )

    blocks_result: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("block_id", "")).strip()

        if block_filter and block_id != block_filter:
            continue
        if not block_filter and block_id not in matched_block_ids and matched_topics:
            continue

        block_topics = block.get("topics", []) if isinstance(block.get("topics"), list) else []
        filtered_topics = [
            topic for topic in block_topics if str(topic.get("topic_id", "")).strip() in matched_topic_ids
        ]

        if not matched_topics and block_filter:
            if topic_level_filter_active:
                continue
            filtered_topics = block_topics

        if matched_topics and not filtered_topics:
            continue

        block_payload = {
            "block_id": block_id,
            "title": block.get("title", ""),
            "rationale": block.get("rationale", ""),
            "tags": list(block.get("tags", []) or []),
            "topics": filtered_topics,
        }
        blocks_result.append(block_payload)

    entity_by_id = {
        str(entry.get("entity_id", "")).strip(): entry
        for entry in entity_registry
        if isinstance(entry, dict) and str(entry.get("entity_id", "")).strip()
    }

    entities_to_include: set[str] = set()
    if entity_filter_id:
        entities_to_include.add(entity_filter_id)
    for entry in matched_topics:
        entities_to_include.update(list(entry["topic"].get("related_entities", []) or []))

    entities_result = [entity_by_id[entity_id] for entity_id in sorted(entities_to_include) if entity_id in entity_by_id]

    topics_result: list[dict[str, Any]] = []
    for entry in matched_topics:
        topic = dict(entry["topic"])
        topic_payload = {
            "topic_id": topic.get("topic_id", ""),
            "title": topic.get("title", ""),
            "category": topic.get("category", ""),
            "priority": topic.get("priority", ""),
            "why_it_matters": topic.get("why_it_matters", ""),
            "research_questions": list(topic.get("research_questions", []) or []),
            "keywords": list(topic.get("keywords", []) or []),
            "tags": list(topic.get("tags", []) or []),
            "related_entities": list(topic.get("related_entities", []) or []),
            "block_id": entry["block_id"],
            "block_title": entry["block_title"],
        }

        if args.include_related:
            related_entities = []
            for entity_id in topic_payload["related_entities"]:
                entity = entity_by_id.get(entity_id)
                if entity is not None:
                    related_entities.append(entity)
            topic_payload["related_entity_details"] = related_entities

        topics_result.append(topic_payload)

    related_payload: dict[str, Any] = {}
    if args.include_related and entity_filter_id and entity_filter_id in entity_by_id:
        entity_entry = entity_by_id[entity_filter_id]
        owner_block_id = str(entity_entry.get("owner_block_id", "")).strip()
        owner_block = None
        for block in blocks:
            if isinstance(block, dict) and str(block.get("block_id", "")).strip() == owner_block_id:
                owner_block = block
                break

        if owner_block is not None:
            related_payload = {
                "entity": entity_entry,
                "owner_block": {
                    "block_id": owner_block.get("block_id", ""),
                    "title": owner_block.get("title", ""),
                    "rationale": owner_block.get("rationale", ""),
                },
                "owner_block_topics": list(owner_block.get("topics", []) or []),
            }

    response = {
        "status": "ok",
        "source_type": source_type,
        "path": str(payload_path),
        "query": {
            "block_id": block_filter or None,
            "topic_id": topic_filter or None,
            "entity": entity_filter_id or None,
            "category": args.category or None,
            "tag": args.tag or None,
            "priority": args.priority or None,
            "text": args.text or None,
            "include_related": bool(args.include_related),
        },
        "summary": {
            "matched_blocks": len(blocks_result),
            "matched_topics": len(topics_result),
            "matched_entities": len(entities_result),
        },
        "results": {
            "blocks": blocks_result,
            "topics": topics_result,
            "entities": entities_result,
        },
    }

    if related_payload:
        response["related"] = related_payload

    print(json.dumps(response, indent=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
