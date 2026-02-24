#!/usr/bin/env python3
"""Run shared Cadence subskill entry gates and emit a single JSON payload.

This helper centralizes repeated subskill preflight steps:
- resolve project root
- resolve cadence scripts dir
- run repo status gate
- optionally assert workflow route
- optionally read workflow state
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from project_root import resolve_project_root, write_project_root_hint


SCRIPT_DIR = Path(__file__).resolve().parent
RESOLVE_SCRIPTS_DIR_SCRIPT = SCRIPT_DIR / "resolve-project-scripts-dir.py"


def run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run shared Cadence subskill entry gates.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    parser.add_argument(
        "--require-cadence",
        action="store_true",
        help="Require .cadence to exist while resolving project root.",
    )
    parser.add_argument(
        "--assert-skill-name",
        default="",
        help="Optional skill name to assert against workflow route.",
    )
    parser.add_argument(
        "--allow-complete",
        action="store_true",
        help="Allow route assertion success when workflow is already complete.",
    )
    parser.add_argument(
        "--include-workflow-state",
        action="store_true",
        help="Include read-workflow-state output in the response payload.",
    )
    parser.add_argument(
        "--remote-policy",
        choices=("any", "github"),
        default="any",
        help="Remote policy for repo-enabled detection.",
    )
    parser.add_argument(
        "--set-local-only",
        action="store_true",
        help="Pass --set-local-only to check-project-repo-status.",
    )
    return parser.parse_args()


def fail(message: str, *, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_json_output(
    command: list[str],
    *,
    error_label: str,
    cwd: Path | None = None,
) -> dict[str, Any]:
    result = run_command(command, cwd=cwd)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or error_label
        fail(detail, code=result.returncode)

    raw = result.stdout.strip()
    if not raw:
        fail(f"{error_label}: EMPTY_STDOUT")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"{error_label}: INVALID_JSON: {exc}")

    if not isinstance(payload, dict):
        fail(f"{error_label}: PAYLOAD_MUST_BE_OBJECT")
    return payload


def resolve_scripts_dir(project_root: Path) -> str:
    result = run_command(
        [
            sys.executable,
            str(RESOLVE_SCRIPTS_DIR_SCRIPT),
            "--project-root",
            str(project_root),
        ]
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "MISSING_CADENCE_SCRIPTS_DIR"
        fail(detail, code=result.returncode)

    scripts_dir = result.stdout.strip()
    if not scripts_dir:
        fail("MISSING_CADENCE_SCRIPTS_DIR")

    scripts_path = Path(scripts_dir)
    if not scripts_path.is_dir():
        fail("INVALID_CADENCE_SCRIPTS_DIR")
    return str(scripts_path)


def main() -> int:
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None

    try:
        project_root, project_root_source = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=bool(args.require_cadence),
            allow_hint=True,
        )
    except ValueError as exc:
        fail(str(exc))

    write_project_root_hint(SCRIPT_DIR, project_root)
    scripts_dir = resolve_scripts_dir(project_root)

    repo_status_command = [
        sys.executable,
        str(Path(scripts_dir) / "check-project-repo-status.py"),
        "--project-root",
        str(project_root),
        "--remote-policy",
        str(args.remote_policy),
    ]
    if args.set_local_only:
        repo_status_command.append("--set-local-only")

    repo_status = load_json_output(
        repo_status_command,
        error_label="CHECK_PROJECT_REPO_STATUS_FAILED",
    )

    route_assertion: dict[str, Any] | None = None
    assert_skill_name = str(args.assert_skill_name).strip()
    if assert_skill_name:
        route_command = [
            sys.executable,
            str(Path(scripts_dir) / "assert-workflow-route.py"),
            "--skill-name",
            assert_skill_name,
            "--project-root",
            str(project_root),
        ]
        if args.allow_complete:
            route_command.append("--allow-complete")
        route_assertion = load_json_output(
            route_command,
            error_label="WORKFLOW_ROUTE_CHECK_FAILED",
        )

    workflow_state: dict[str, Any] | None = None
    if args.include_workflow_state:
        workflow_state = load_json_output(
            [
                sys.executable,
                str(Path(scripts_dir) / "read-workflow-state.py"),
                "--project-root",
                str(project_root),
            ],
            error_label="WORKFLOW_STATE_READ_FAILED",
        )

    payload: dict[str, Any] = {
        "status": "ok",
        "project_root": str(project_root),
        "project_root_source": project_root_source,
        "cadence_scripts_dir": scripts_dir,
        "repo_enabled": bool(repo_status.get("repo_enabled", False)),
        "repo_status": repo_status,
    }
    if route_assertion is not None:
        payload["route_assertion"] = route_assertion
    if workflow_state is not None:
        payload["workflow_state"] = workflow_state

    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
