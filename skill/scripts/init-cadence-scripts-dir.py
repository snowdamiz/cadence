#!/usr/bin/env python3
"""Persist Cadence helper scripts directory in .cadence/cadence.json."""

import argparse
import json
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Persist cadence-scripts-dir in a project cadence.json.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    return parser.parse_args()


def cadence_paths(project_root: Path) -> tuple[Path, Path]:
    cadence_dir = project_root / ".cadence"
    cadence_json_path = cadence_dir / "cadence.json"
    return cadence_dir, cadence_json_path


def load_data(project_root: Path):
    cadence_dir, cadence_json_path = cadence_paths(project_root)
    if not cadence_json_path.exists():
        return default_data()
    with cadence_json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return reconcile_workflow_state(data, cadence_dir_exists=cadence_dir.exists())


def save_data(project_root: Path, data):
    cadence_dir, cadence_json_path = cadence_paths(project_root)
    cadence_dir.mkdir(parents=True, exist_ok=True)
    with cadence_json_path.open("w", encoding="utf-8") as file:
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
        print(str(exc))
        return 1

    cadence_dir, _ = cadence_paths(project_root)
    if not cadence_dir.exists():
        print("MISSING_CADENCE_DIR")
        return 1

    scripts_dir = str(SCRIPT_DIR)

    data = load_data(project_root)
    state = data.setdefault("state", {})
    state["cadence-scripts-dir"] = scripts_dir
    data = reconcile_workflow_state(data, cadence_dir_exists=cadence_dir.exists())
    save_data(project_root, data)
    write_project_root_hint(SCRIPT_DIR, project_root)

    print(json.dumps({"status": "ok", "cadence_scripts_dir": scripts_dir}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
