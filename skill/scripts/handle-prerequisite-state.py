#!/usr/bin/env python3
"""Read or update prerequisite pass state in .cadence/cadence.json."""

import argparse
import json
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read or update prerequisites-pass in cadence.json.",
    )
    parser.add_argument(
        "pass_state",
        nargs="?",
        choices=("0", "1"),
        help="Set prerequisites-pass to 0 or 1. Omit to read current value.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def cadence_json_path(project_root: Path) -> Path:
    return project_root / ".cadence" / "cadence.json"


def load_data(project_root: Path):
    state_path = cadence_json_path(project_root)
    if not state_path.exists():
        return default_data()
    try:
        with state_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_CADENCE_JSON: {exc} path={state_path}") from exc
    return reconcile_workflow_state(data, cadence_dir_exists=state_path.parent.exists())


def save_data(project_root: Path, data):
    state_path = cadence_json_path(project_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


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
    data = load_data(project_root)

    if args.pass_state is None:
        print("true" if bool(data.get("prerequisites-pass", False)) else "false")
        return 0

    data["prerequisites-pass"] = args.pass_state == "1"
    data = reconcile_workflow_state(data, cadence_dir_exists=cadence_json_path(project_root).parent.exists())
    save_data(project_root, data)
    print("true" if data["prerequisites-pass"] else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
