#!/usr/bin/env python3
"""Query ideation research agenda data with granular filters."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
import re
import sys
from pathlib import Path
from typing import Any

from ideation_research import ResearchAgendaValidationError, normalize_ideation_research, slugify

FUZZY_TEXT_FIELDS: tuple[str, ...] = (
    "block.title",
    "block.rationale",
    "block.tags",
    "topic.title",
    "topic.category",
    "topic.why_it_matters",
    "topic.research_questions",
    "topic.keywords",
    "topic.tags",
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


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
        "--fuzzy-text",
        action="store_true",
        help="Enable fuzzy matching for --text instead of strict substring matching",
    )
    parser.add_argument(
        "--fuzzy-threshold",
        type=float,
        default=0.72,
        help="Fuzzy score threshold between 0.0 and 1.0 (default: 0.72)",
    )
    parser.add_argument(
        "--fuzzy-fields",
        help=(
            "Comma-separated fuzzy field paths. "
            f"Supported: {', '.join(FUZZY_TEXT_FIELDS)}. "
            "If omitted, all supported fields are searched."
        ),
    )
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


def _field_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return " ".join(part for part in (_field_text(item) for item in value) if part)
    return str(value).strip()


def _entry_field_map(entry: dict[str, Any]) -> dict[str, str]:
    topic = entry.get("topic", {})
    return {
        "block.title": _field_text(entry.get("block_title", "")),
        "block.rationale": _field_text(entry.get("block_rationale", "")),
        "block.tags": _field_text(entry.get("block_tags", [])),
        "topic.title": _field_text(topic.get("title", "")),
        "topic.category": _field_text(topic.get("category", "")),
        "topic.why_it_matters": _field_text(topic.get("why_it_matters", "")),
        "topic.research_questions": _field_text(topic.get("research_questions", [])),
        "topic.keywords": _field_text(topic.get("keywords", [])),
        "topic.tags": _field_text(topic.get("tags", [])),
    }


def _parse_fuzzy_fields(raw_fields: str | None) -> list[str]:
    if not raw_fields:
        return []
    fields = [value.strip() for value in raw_fields.split(",") if value.strip()]
    if not fields:
        raise ValueError("FUZZY_FIELDS_EMPTY")

    invalid_fields = sorted({field for field in fields if field not in FUZZY_TEXT_FIELDS})
    if invalid_fields:
        supported = ", ".join(FUZZY_TEXT_FIELDS)
        invalid = ", ".join(invalid_fields)
        raise ValueError(f"UNKNOWN_FUZZY_FIELDS: {invalid}. Supported fields: {supported}")

    unique_fields: list[str] = []
    for field in fields:
        if field not in unique_fields:
            unique_fields.append(field)
    return unique_fields


def _tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(_lower(value))


def _token_overlap_ratio(query: str, candidate: str) -> float:
    query_tokens = set(_tokenize(query))
    candidate_tokens = set(_tokenize(candidate))
    if not query_tokens or not candidate_tokens:
        return 0.0
    return len(query_tokens & candidate_tokens) / float(len(query_tokens))


def _fuzzy_score(query: str, candidate: str) -> float:
    query_norm = _lower(query)
    candidate_norm = _lower(candidate)
    if not query_norm or not candidate_norm:
        return 0.0
    if query_norm in candidate_norm:
        return 1.0

    best = max(
        SequenceMatcher(None, query_norm, candidate_norm).ratio(),
        _token_overlap_ratio(query_norm, candidate_norm),
    )

    candidate_tokens = _tokenize(candidate_norm)
    query_token_count = max(1, len(_tokenize(query_norm)))
    max_span = min(len(candidate_tokens), max(query_token_count + 1, 3))
    for span in range(1, max_span + 1):
        for start in range(0, len(candidate_tokens) - span + 1):
            phrase = " ".join(candidate_tokens[start : start + span])
            score = SequenceMatcher(None, query_norm, phrase).ratio()
            if score > best:
                best = score
    return best


def _fuzzy_text_match(
    query: str,
    entry: dict[str, Any],
    *,
    threshold: float,
    fields: list[str],
) -> tuple[bool, float, list[str]]:
    field_map = _entry_field_map(entry)
    target_fields = fields or list(FUZZY_TEXT_FIELDS)

    best_score = 0.0
    matched_fields: list[str] = []
    for field in target_fields:
        candidate = field_map.get(field, "")
        score = _fuzzy_score(query, candidate)
        if score > best_score:
            best_score = score
        if score >= threshold:
            matched_fields.append(field)

    return best_score >= threshold, best_score, sorted(set(matched_fields))


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

    if not 0.0 <= args.fuzzy_threshold <= 1.0:
        print("INVALID_FUZZY_THRESHOLD: must be between 0.0 and 1.0", file=sys.stderr)
        return 2
    if args.fuzzy_text and not args.text:
        print("FUZZY_TEXT_REQUIRES_TEXT_FILTER: provide --text when using --fuzzy-text", file=sys.stderr)
        return 2
    if args.fuzzy_fields and not args.fuzzy_text:
        print("FUZZY_FIELDS_REQUIRES_FUZZY_TEXT: use --fuzzy-text with --fuzzy-fields", file=sys.stderr)
        return 2
    try:
        fuzzy_fields = _parse_fuzzy_fields(args.fuzzy_fields)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

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
    fuzzy_match_meta: dict[str, dict[str, Any]] = {}
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
            if args.fuzzy_text:
                is_match, score, matched_fields = _fuzzy_text_match(
                    args.text,
                    entry,
                    threshold=args.fuzzy_threshold,
                    fields=fuzzy_fields,
                )
                if not is_match:
                    continue
                fuzzy_match_meta[topic_id] = {
                    "score": round(score, 4),
                    "matched_fields": matched_fields,
                }
            else:
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

        if args.fuzzy_text and args.text:
            fuzzy_metadata = fuzzy_match_meta.get(str(topic_payload.get("topic_id", "")).strip())
            if fuzzy_metadata is not None:
                topic_payload["fuzzy_match"] = fuzzy_metadata

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
            "fuzzy_text": bool(args.fuzzy_text),
            "fuzzy_threshold": args.fuzzy_threshold if args.fuzzy_text else None,
            "fuzzy_fields": (fuzzy_fields or list(FUZZY_TEXT_FIELDS)) if args.fuzzy_text else None,
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

    if args.fuzzy_text and fuzzy_match_meta:
        response["summary"]["best_fuzzy_score"] = max(meta["score"] for meta in fuzzy_match_meta.values())

    if related_payload:
        response["related"] = related_payload

    print(json.dumps(response, indent=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
