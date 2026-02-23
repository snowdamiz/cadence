#!/usr/bin/env python3
"""Render .cadence/cadence.json ideation payload in human-readable text."""

import json
from pathlib import Path


CADENCE_JSON_PATH = Path(".cadence") / "cadence.json"


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


def load_ideation():
    if not CADENCE_JSON_PATH.exists():
        return {}
    with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
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
    ideation = load_ideation()
    print("Current Project Ideation")
    print("========================")
    if not ideation:
        print("No ideation is currently saved.")
        return

    core_ideation = {key: value for key, value in ideation.items() if key != "research_agenda"}
    if core_ideation:
        for line in render_value(core_ideation):
            print(line)

    agenda_lines = render_research_agenda(ideation.get("research_agenda"))
    if core_ideation:
        print()
    for line in agenda_lines:
        print(line)


if __name__ == "__main__":
    main()
