#!/usr/bin/env python3
"""Check GitHub repo status and persist state.repo-enabled when .cadence exists."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state


CADENCE_DIR = Path(".cadence")
CADENCE_JSON_PATH = CADENCE_DIR / "cadence.json"
SCRIPT_DIR = Path(__file__).resolve().parent


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check project repo readiness and persist Cadence repo-enabled state.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root override. If omitted, resolve via Cadence root resolver.",
    )
    parser.add_argument(
        "--set-local-only",
        action="store_true",
        help="Persist local-only mode (repo-enabled=false) when no GitHub remote is configured.",
    )
    return parser.parse_args()


def load_cadence_data(project_root: Path) -> dict[str, Any] | None:
    cadence_path = project_root / CADENCE_JSON_PATH
    cadence_dir = project_root / CADENCE_DIR
    if not cadence_path.exists():
        return None

    try:
        with cadence_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    return reconcile_workflow_state(raw, cadence_dir_exists=cadence_dir.exists())


def save_cadence_data(project_root: Path, data: dict[str, Any]) -> None:
    cadence_path = project_root / CADENCE_JSON_PATH
    cadence_path.parent.mkdir(parents=True, exist_ok=True)
    with cadence_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def parse_remotes(remote_text: str) -> list[dict[str, str]]:
    remotes: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for line in remote_text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0].strip()
        url = parts[1].strip()
        key = (name, url)
        if not name or not url or key in seen:
            continue
        seen.add(key)
        remotes.append({"name": name, "url": url})

    return remotes


def detect_git_repo(project_root: Path) -> dict[str, Any]:
    inside_result = run_command(["git", "rev-parse", "--is-inside-work-tree"], project_root)
    git_initialized = inside_result.returncode == 0 and inside_result.stdout.strip() == "true"

    repo_root = ""
    if git_initialized:
        root_result = run_command(["git", "rev-parse", "--show-toplevel"], project_root)
        if root_result.returncode == 0:
            repo_root = root_result.stdout.strip()

    remotes: list[dict[str, str]] = []
    github_remote_name = ""
    github_remote_url = ""
    if git_initialized:
        remote_result = run_command(["git", "remote", "-v"], project_root)
        if remote_result.returncode == 0:
            remotes = parse_remotes(remote_result.stdout)

        for remote in remotes:
            url = remote.get("url", "")
            if "github.com" in url.lower() or "github." in url.lower():
                github_remote_name = remote.get("name", "")
                github_remote_url = url
                break

    github_remote_configured = bool(github_remote_name and github_remote_url)
    repo_enabled_detected = bool(git_initialized and github_remote_configured)

    return {
        "git_initialized": git_initialized,
        "repo_root": repo_root,
        "remotes": remotes,
        "github_remote_configured": github_remote_configured,
        "github_remote_name": github_remote_name,
        "github_remote_url": github_remote_url,
        "repo_enabled_detected": repo_enabled_detected,
    }


def ensure_default_state(data: dict[str, Any]) -> dict[str, Any]:
    reconciled = reconcile_workflow_state(data, cadence_dir_exists=True)
    state = reconciled.setdefault("state", {})
    if not isinstance(state, dict):
        state = {}
        reconciled["state"] = state
    state["repo-enabled"] = bool(state.get("repo-enabled", False))
    return reconciled


def main() -> int:
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, project_root_source = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=False,
            allow_hint=False,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if (
        explicit_project_root is None
        and project_root_source == "cwd-fallback"
        and project_root == SCRIPT_DIR.parent
    ):
        print(
            "AMBIGUOUS_PROJECT_ROOT: use --project-root when invoking from the Cadence skill directory.",
            file=sys.stderr,
        )
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)

    repo_status = detect_git_repo(project_root)
    cadence_exists = (project_root / CADENCE_JSON_PATH).exists()
    state_updated = False

    data = load_cadence_data(project_root)
    if data is None and cadence_exists:
        # Safety fallback for race conditions between exists check and file read.
        data = default_data()

    repo_enabled_state = bool(repo_status["repo_enabled_detected"])
    if data is not None:
        original = copy.deepcopy(data)
        data = ensure_default_state(data)
        state = data["state"]

        if repo_status["repo_enabled_detected"]:
            state["repo-enabled"] = True
        elif args.set_local_only:
            state["repo-enabled"] = False
        else:
            state["repo-enabled"] = False

        repo_enabled_state = bool(state.get("repo-enabled", False))
        if data != original:
            save_cadence_data(project_root, data)
            state_updated = True

    response = {
        "status": "ok",
        "project_root": str(project_root),
        "project_root_source": project_root_source,
        "cadence_state_path": str(project_root / CADENCE_JSON_PATH),
        "cadence_state_available": data is not None,
        "state_updated": state_updated,
        "repo_enabled": repo_enabled_state,
        "repo_enabled_detected": bool(repo_status["repo_enabled_detected"]),
        "git_initialized": bool(repo_status["git_initialized"]),
        "github_remote_configured": bool(repo_status["github_remote_configured"]),
        "github_remote_name": repo_status.get("github_remote_name", ""),
        "github_remote_url": repo_status.get("github_remote_url", ""),
        "set_local_only": bool(args.set_local_only),
    }
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
