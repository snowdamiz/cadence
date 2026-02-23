#!/usr/bin/env python3
"""Inject finalized ideation payload into .cadence/cadence.json."""

import argparse
import json
import sys
from pathlib import Path


CADENCE_JSON_PATH = Path(".cadence") / "cadence.json"


def default_data():
    return {
        "prerequisites-pass": False,
        "state": {
            "ideation-completed": False,
        },
        "project-details": {},
        "ideation": {},
    }


def load_cadence():
    if not CADENCE_JSON_PATH.exists():
        return default_data()
    try:
        with CADENCE_JSON_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {CADENCE_JSON_PATH}: {exc}") from exc


def save_cadence(data):
    CADENCE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CADENCE_JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def deep_merge(base, patch):
    merged = dict(base)
    for key, value in patch.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def parse_payload(args):
    payload_file_path = None
    if args.file:
        payload_file_path = Path(args.file)
        try:
            payload_text = payload_file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Unable to read payload file {args.file}: {exc}") from exc
    elif args.json:
        payload_text = args.json
    elif args.stdin:
        payload_text = sys.stdin.read()
    else:
        raise ValueError("One payload input source is required.")

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object.")
    return payload, payload_file_path


def apply_completion_state(data, completion_state):
    state = data.setdefault("state", {})
    if completion_state == "complete":
        state["ideation-completed"] = True
    elif completion_state == "incomplete":
        state["ideation-completed"] = False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inject finalized ideation payload into .cadence/cadence.json."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Read ideation payload JSON from file path")
    group.add_argument("--json", help="Read ideation payload JSON from inline string")
    group.add_argument("--stdin", action="store_true", help="Read ideation payload JSON from stdin")
    parser.add_argument(
        "--completion-state",
        choices=["complete", "incomplete", "keep"],
        default="complete",
        help="How to update state.ideation-completed",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge payload into existing ideation object instead of replacing it",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        data = load_cadence()
        payload, payload_file_path = parse_payload(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    existing_ideation = data.get("ideation", {})

    if args.merge and isinstance(existing_ideation, dict):
        data["ideation"] = deep_merge(existing_ideation, payload)
    else:
        data["ideation"] = payload

    apply_completion_state(data, args.completion_state)
    save_cadence(data)

    payload_deleted = False
    if payload_file_path is not None:
        try:
            payload_file_path.unlink()
            payload_deleted = True
        except OSError as exc:
            print(f"Unable to delete payload file {payload_file_path}: {exc}", file=sys.stderr)
            return 3

    print(
        json.dumps(
            {
                "status": "ok",
                "path": str(CADENCE_JSON_PATH),
                "completion_state": args.completion_state,
                "payload_deleted": payload_deleted,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
