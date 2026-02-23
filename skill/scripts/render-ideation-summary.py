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


def main():
    ideation = load_ideation()
    print("Current Project Ideation")
    print("========================")
    if not ideation:
        print("No ideation is currently saved.")
        return

    for line in render_value(ideation):
        print(line)


if __name__ == "__main__":
    main()
