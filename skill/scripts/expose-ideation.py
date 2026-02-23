#!/usr/bin/env python3
"""Expose .cadence/cadence.json ideation payload for AI consumption."""

import json
from pathlib import Path


CADENCE_JSON_PATH = Path(".cadence") / "cadence.json"


def load_ideation():
    if not CADENCE_JSON_PATH.exists():
        return {}

    with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    ideation = data.get("ideation", {})
    if isinstance(ideation, dict):
        return ideation
    return {}


print(json.dumps(load_ideation(), indent=4))
