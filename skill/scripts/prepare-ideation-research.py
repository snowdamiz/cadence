#!/usr/bin/env python3
"""Normalize and validate ideation research agenda payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ideation_research import ResearchAgendaValidationError, normalize_ideation_research


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize ideation.research_agenda and validate block/topic/entity relationships."
    )
    parser.add_argument("--file", required=True, help="Path to ideation payload JSON file")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow empty research agendas (default requires at least one topic)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_path = Path(args.file)

    try:
        payload_text = payload_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"PAYLOAD_READ_FAILED: {exc}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        print(f"INVALID_PAYLOAD_JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("IDEATION_PAYLOAD_MUST_BE_OBJECT", file=sys.stderr)
        return 2

    try:
        normalized = normalize_ideation_research(payload, require_topics=not args.allow_empty)
    except ResearchAgendaValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        payload_path.write_text(json.dumps(normalized, indent=4) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"PAYLOAD_WRITE_FAILED: {exc}", file=sys.stderr)
        return 3

    agenda = normalized.get("research_agenda", {})
    summary = agenda.get("summary", {}) if isinstance(agenda, dict) else {}
    print(
        json.dumps(
            {
                "status": "ok",
                "path": str(payload_path),
                "summary": {
                    "block_count": int(summary.get("block_count", 0)),
                    "topic_count": int(summary.get("topic_count", 0)),
                    "entity_count": int(summary.get("entity_count", 0)),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
