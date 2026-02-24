#!/usr/bin/env python3
"""Render .cadence/cadence.json ideation payload in human-readable text."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render ideation payload from cadence.json in human-readable text.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def cadence_json_path(project_root: Path) -> Path:
    return project_root / ".cadence" / "cadence.json"


def humanize_key(key):
    return str(key).replace("_", " ").replace("-", " ").strip().title()


def scalar_to_text(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None:
        return "None"
    return str(value)


def render_value(value, indent=0):
    space = " " * indent
    lines = []

    if isinstance(value, dict):
        if not value:
            return [f"{space}(empty)"]
        for key, inner in value.items():
            label = humanize_key(key)
            if isinstance(inner, (dict, list)):
                lines.append(f"{space}- {label}:")
                lines.extend(render_value(inner, indent + 2))
            else:
                lines.append(f"{space}- {label}: {scalar_to_text(inner)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [f"{space}(empty list)"]
        for idx, item in enumerate(value, start=1):
            if isinstance(item, (dict, list)):
                lines.append(f"{space}- Item {idx}:")
                lines.extend(render_value(item, indent + 2))
            else:
                lines.append(f"{space}- {scalar_to_text(item)}")
        return lines

    return [f"{space}{scalar_to_text(value)}"]


def load_ideation(project_root: Path):
    state_path = cadence_json_path(project_root)
    if not state_path.exists():
        return {}
    try:
        with state_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_CADENCE_JSON: {exc} path={state_path}") from exc
    ideation = data.get("ideation", {})
    return ideation if isinstance(ideation, dict) else {}


def render_research_agenda(agenda):
    if not isinstance(agenda, dict):
        return ["No research agenda is currently saved."]

    blocks = agenda.get("blocks") if isinstance(agenda.get("blocks"), list) else []
    entities = agenda.get("entity_registry") if isinstance(agenda.get("entity_registry"), list) else []
    summary = agenda.get("summary") if isinstance(agenda.get("summary"), dict) else {}
    topic_count = int(summary.get("topic_count", 0))
    if not topic_count:
        topic_count = sum(
            len(block.get("topics", []))
            for block in blocks
            if isinstance(block, dict) and isinstance(block.get("topics"), list)
        )

    lines = ["Research Agenda", "---------------"]
    lines.append(f"- Blocks: {len(blocks)}")
    lines.append(f"- Topics: {topic_count}")
    lines.append(f"- Entities: {len(entities)}")

    if not blocks:
        lines.append("- No research blocks defined yet.")
        return lines

    lines.append("- Blocks Detail:")
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_title = scalar_to_text(block.get("title", "Untitled"))
        block_id = scalar_to_text(block.get("block_id", ""))
        topics = block.get("topics") if isinstance(block.get("topics"), list) else []
        lines.append(f"  - {block_title} ({block_id})")
        for topic in topics:
            if not isinstance(topic, dict):
                continue
            topic_title = scalar_to_text(topic.get("title", "Untitled Topic"))
            topic_id = scalar_to_text(topic.get("topic_id", ""))
            priority = scalar_to_text(topic.get("priority", "medium"))
            lines.append(f"    - {topic_title} ({topic_id}) [priority: {priority}]")

    return lines


def main():
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, _ = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=False,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)
    try:
        ideation = load_ideation(project_root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Current Project Ideation")
    print("========================")
    if not ideation:
        print("No ideation is currently saved.")
        return 0

    core_ideation = {key: value for key, value in ideation.items() if key != "research_agenda"}
    if core_ideation:
        for line in render_value(core_ideation):
            print(line)

    agenda_lines = render_research_agenda(ideation.get("research_agenda"))
    if core_ideation:
        print()
    for line in agenda_lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
