#!/usr/bin/env python3
"""Read and print the ideation payload from .cadence/cadence.json."""

import json
from pathlib import Path


CADENCE_JSON_PATH = Path(".cadence") / "cadence.json"


if CADENCE_JSON_PATH.exists():
    with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
else:
    data = {"ideation": {}}

print(json.dumps(data.get("ideation", {}), indent=4))
