#!/usr/bin/env python3
"""Persist Cadence helper scripts directory in .cadence/cadence.json."""

import json
from pathlib import Path


CADENCE_DIR = Path(".cadence")
CADENCE_JSON_PATH = CADENCE_DIR / "cadence.json"
GETTER_PATH = CADENCE_DIR / "get-cadence-scripts-dir.py"


def default_data():
    return {
        "prerequisites-pass": False,
        "state": {
            "ideation-completed": False,
            "cadence-scripts-dir": "",
        },
        "project-details": {},
        "ideation": {},
    }


def load_data():
    if not CADENCE_JSON_PATH.exists():
        return default_data()
    with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    CADENCE_DIR.mkdir(parents=True, exist_ok=True)
    with CADENCE_JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def write_getter_script():
    content = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

cadence_json_path = Path(".cadence") / "cadence.json"
if not cadence_json_path.exists():
    print("MISSING_CADENCE_JSON", file=sys.stderr)
    raise SystemExit(1)

try:
    with cadence_json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
except json.JSONDecodeError as exc:
    print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
    raise SystemExit(1)

scripts_dir = data.get("state", {}).get("cadence-scripts-dir", "")
if not scripts_dir:
    print("MISSING_CADENCE_SCRIPTS_DIR", file=sys.stderr)
    raise SystemExit(1)

print(scripts_dir)
"""
    GETTER_PATH.write_text(content, encoding="utf-8")


def main():
    if not CADENCE_DIR.exists():
        print("MISSING_CADENCE_DIR")
        return 1

    scripts_dir = str(Path(__file__).resolve().parent)

    data = load_data()
    state = data.setdefault("state", {})
    state["cadence-scripts-dir"] = scripts_dir
    save_data(data)
    write_getter_script()

    print(json.dumps({"status": "ok", "cadence_scripts_dir": scripts_dir, "getter_path": str(GETTER_PATH)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
