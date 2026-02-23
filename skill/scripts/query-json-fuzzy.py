#!/usr/bin/env python3
"""General-purpose fuzzy search over JSON scalar fields.

This script is intentionally standalone and not wired into any existing Cadence flow.
It searches recursively across arbitrary JSON structures and can target specific fields
using key/path patterns. Identifier-like keys are excluded by default.
"""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
from fnmatch import fnmatchcase
import json
import re
import sys
from pathlib import Path
from typing import Any

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
IDENTIFIER_KEY_PATTERN = re.compile(
    r"(?:^|[_-])(id|ids|uuid|guid|slug|slugs|identifier|identifiers|key|keys|token|tokens|hash|checksum|fingerprint|ref|refs|code|codes|path|paths|url|urls|uri|uris|file|files|filepath|filepaths)$",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fuzzy-search JSON scalar fields (all current/future fields by default)."
    )
    parser.add_argument(
        "--file",
        default=str(Path(".cadence") / "cadence.json"),
        help="Path to any JSON file (default: .cadence/cadence.json)",
    )
    parser.add_argument("--text", required=True, help="Query text to fuzzy-match")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.72,
        help="Minimum fuzzy score between 0.0 and 1.0 (default: 0.72)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum matches returned, sorted by score descending (default: 25)",
    )
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        help=(
            "Include only matching fields (repeatable, supports * wildcard). "
            "Matches against full path and terminal key. Example: --field 'ideation.*.title' --field title"
        ),
    )
    parser.add_argument(
        "--exclude-field",
        action="append",
        default=[],
        help=(
            "Exclude matching fields (repeatable, supports * wildcard). "
            "Matches against full path and terminal key."
        ),
    )
    parser.add_argument(
        "--include-identifiers",
        action="store_true",
        help="Include normally excluded technical keys (ids, uuid, slug, key, path, url, file, etc.)",
    )
    parser.add_argument(
        "--include-non-string",
        action="store_true",
        help="Also search numbers/booleans (strings are always searched)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=2,
        help="Skip string values shorter than this length (default: 2)",
    )
    return parser.parse_args()


def _lower(value: Any) -> str:
    return str(value).strip().lower()


def _normalize_key(key: str) -> str:
    # Convert camelCase to snake-like form before identifier checks.
    snakeish = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(key))
    return _lower(snakeish)


def _is_identifier_key(key: str) -> bool:
    normalized = _normalize_key(key)
    return bool(IDENTIFIER_KEY_PATTERN.search(normalized))


def _normalize_patterns(values: list[str]) -> list[str]:
    patterns: list[str] = []
    for raw_value in values:
        for part in str(raw_value).split(","):
            candidate = _lower(part)
            if candidate and candidate not in patterns:
                patterns.append(candidate)
    return patterns


def _path_or_key_matches(patterns: list[str], path: str, key: str) -> bool:
    path_norm = _lower(path)
    key_norm = _normalize_key(key)
    return any(fnmatchcase(path_norm, pattern) or fnmatchcase(key_norm, pattern) for pattern in patterns)


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


def _preview(value: str, limit: int = 220) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _iter_scalar_candidates(node: Any, *, path: str = "", key: str = ""):
    if isinstance(node, dict):
        for child_key, child_value in node.items():
            child_key_text = str(child_key)
            child_path = f"{path}.{child_key_text}" if path else child_key_text
            yield from _iter_scalar_candidates(child_value, path=child_path, key=child_key_text)
        return

    if isinstance(node, list):
        for index, item in enumerate(node):
            child_path = f"{path}[{index}]"
            yield from _iter_scalar_candidates(item, path=child_path, key=key)
        return

    yield {
        "path": path,
        "key": key,
        "value": node,
    }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"PAYLOAD_READ_FAILED: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_PAYLOAD_JSON: {exc}") from exc


def main() -> int:
    args = parse_args()
    payload_path = Path(args.file)

    if not 0.0 <= args.threshold <= 1.0:
        print("INVALID_THRESHOLD: must be between 0.0 and 1.0", file=sys.stderr)
        return 2
    if args.limit < 1:
        print("INVALID_LIMIT: must be >= 1", file=sys.stderr)
        return 2
    if args.min_length < 0:
        print("INVALID_MIN_LENGTH: must be >= 0", file=sys.stderr)
        return 2

    include_patterns = _normalize_patterns(args.field)
    exclude_patterns = _normalize_patterns(args.exclude_field)

    try:
        payload = _load_json(payload_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    candidates_scanned = 0
    candidates_considered = 0
    matches: list[dict[str, Any]] = []

    for candidate in _iter_scalar_candidates(payload):
        candidates_scanned += 1
        field_path = str(candidate["path"])
        field_key = str(candidate["key"])

        if not args.include_identifiers and _is_identifier_key(field_key):
            continue
        if include_patterns and not _path_or_key_matches(include_patterns, field_path, field_key):
            continue
        if exclude_patterns and _path_or_key_matches(exclude_patterns, field_path, field_key):
            continue

        raw_value = candidate["value"]
        if isinstance(raw_value, str):
            text_value = raw_value.strip()
            value_type = "string"
        elif args.include_non_string and isinstance(raw_value, (int, float, bool)):
            text_value = str(raw_value)
            value_type = type(raw_value).__name__
        else:
            continue

        if len(text_value) < args.min_length:
            continue

        candidates_considered += 1
        score = _fuzzy_score(args.text, text_value)
        if score < args.threshold:
            continue

        matches.append(
            {
                "path": field_path,
                "field": field_key,
                "value_type": value_type,
                "score": round(score, 4),
                "value_preview": _preview(text_value),
            }
        )

    matches_sorted = sorted(
        matches,
        key=lambda item: (-item["score"], item["path"]),
    )
    results = matches_sorted[: args.limit]

    response: dict[str, Any] = {
        "status": "ok",
        "path": str(payload_path),
        "query": {
            "text": args.text,
            "threshold": args.threshold,
            "limit": args.limit,
            "field": include_patterns or None,
            "exclude_field": exclude_patterns or None,
            "include_identifiers": bool(args.include_identifiers),
            "include_non_string": bool(args.include_non_string),
            "min_length": args.min_length,
        },
        "summary": {
            "candidates_scanned": candidates_scanned,
            "candidates_considered": candidates_considered,
            "matches_before_limit": len(matches_sorted),
            "matches_returned": len(results),
        },
        "results": results,
    }

    if results:
        response["summary"]["best_score"] = max(item["score"] for item in results)

    print(json.dumps(response, indent=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
