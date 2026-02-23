#!/usr/bin/env python3
"""Resolve the active Cadence project root and print it to stdout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from project_root import resolve_project_root, write_project_root_hint


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve Cadence project root from cwd, explicit path, or recent hint.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    parser.add_argument(
        "--require-cadence",
        action="store_true",
        help="Fail unless resolved project root contains .cadence.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of plain path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    explicit = args.project_root.strip() or None

    try:
        project_root, source = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit,
            require_cadence=bool(args.require_cadence),
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)

    if args.json:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "project_root": str(project_root),
                    "source": source,
                }
            )
        )
    else:
        print(str(project_root))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
