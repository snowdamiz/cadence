#!/usr/bin/env python3
"""Capture project mode and brownfield baseline for Cadence workflow routing."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from project_root import resolve_project_root, write_project_root_hint
from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status


SCRIPT_DIR = Path(__file__).resolve().parent
ROUTE_GUARD_SCRIPT = SCRIPT_DIR / "assert-workflow-route.py"
CADENCE_JSON_REL = Path(".cadence") / "cadence.json"

DEFAULT_EXCLUDED_DIRS = {
    ".cadence",
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".next",
    ".turbo",
    "dist",
    "build",
    "coverage",
}

KNOWN_MANIFESTS = {
    "package.json",
    "pnpm-workspace.yaml",
    "yarn.lock",
    "package-lock.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "Gemfile",
    "composer.json",
    "turbo.json",
    "nx.json",
    "lerna.json",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture Cadence project mode and brownfield inventory baseline.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )
    parser.add_argument(
        "--project-mode",
        choices=["auto", "greenfield", "brownfield"],
        default="auto",
        help="Project mode selection. auto infers from repository contents.",
    )
    parser.add_argument(
        "--max-top-level-entries",
        type=int,
        default=24,
        help="Maximum number of top-level entries to include in baseline output.",
    )
    parser.add_argument(
        "--max-sample-files",
        type=int,
        default=3000,
        help="Maximum number of files to inspect while building baseline inventory.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def assert_expected_route(project_root: Path) -> None:
    result = run_command(
        [
            sys.executable,
            str(ROUTE_GUARD_SCRIPT),
            "--skill-name",
            "brownfield-intake",
            "--project-root",
            str(project_root),
        ],
        project_root,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "WORKFLOW_ROUTE_CHECK_FAILED"
        print(detail, file=sys.stderr)
        raise SystemExit(result.returncode)


def cadence_json_path(project_root: Path) -> Path:
    return project_root / CADENCE_JSON_REL


def load_state(project_root: Path) -> dict[str, Any]:
    state_path = cadence_json_path(project_root)
    if not state_path.exists():
        return default_data()

    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"INVALID_CADENCE_JSON: {exc} path={state_path}", file=sys.stderr)
        raise SystemExit(1)

    if not isinstance(payload, dict):
        return default_data()
    return reconcile_workflow_state(payload, cadence_dir_exists=True)


def save_state(project_root: Path, data: dict[str, Any]) -> None:
    path = cadence_json_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")


def detect_git_details(project_root: Path) -> dict[str, Any]:
    inside = run_command(["git", "rev-parse", "--is-inside-work-tree"], project_root)
    git_initialized = inside.returncode == 0 and inside.stdout.strip() == "true"

    repo_root = ""
    branch = ""
    remotes: list[dict[str, str]] = []
    if git_initialized:
        root_result = run_command(["git", "rev-parse", "--show-toplevel"], project_root)
        if root_result.returncode == 0:
            repo_root = root_result.stdout.strip()

        branch_result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], project_root)
        if branch_result.returncode == 0:
            branch = branch_result.stdout.strip()
            if branch == "HEAD":
                branch = ""

        remote_result = run_command(["git", "remote", "-v"], project_root)
        if remote_result.returncode == 0:
            seen: set[tuple[str, str]] = set()
            for line in remote_result.stdout.splitlines():
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

    return {
        "git_initialized": git_initialized,
        "repo_root": repo_root,
        "branch": branch,
        "remote_count": len(remotes),
        "remotes": remotes,
    }


def iter_inventory_paths(project_root: Path, *, max_files: int) -> tuple[list[str], int, int]:
    file_paths: list[str] = []
    file_count = 0
    directory_count = 0

    for root, dirs, files in os.walk(project_root):
        rel_root = Path(root).resolve().relative_to(project_root)
        dirs[:] = [name for name in dirs if name not in DEFAULT_EXCLUDED_DIRS]
        directory_count += len(dirs)

        for filename in files:
            if filename.startswith(".DS_Store"):
                continue
            rel_path = (rel_root / filename).as_posix() if str(rel_root) != "." else filename
            file_count += 1
            if len(file_paths) < max_files:
                file_paths.append(rel_path)

    file_paths.sort()
    return file_paths, file_count, directory_count


def infer_languages(file_paths: list[str]) -> list[dict[str, Any]]:
    extension_counts: dict[str, int] = {}
    for rel_path in file_paths:
        suffix = Path(rel_path).suffix.lower()
        ext = suffix if suffix else "(no-ext)"
        extension_counts[ext] = extension_counts.get(ext, 0) + 1

    ranked = sorted(
        extension_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    return [{"extension": ext, "count": count} for ext, count in ranked[:8]]


def collect_manifests(file_paths: list[str]) -> list[str]:
    manifests: list[str] = []
    for rel_path in file_paths:
        name = Path(rel_path).name
        if name in KNOWN_MANIFESTS and rel_path not in manifests:
            manifests.append(rel_path)
    manifests.sort()
    return manifests


def collect_ci_workflows(file_paths: list[str]) -> list[str]:
    workflows = [
        rel_path
        for rel_path in file_paths
        if rel_path.startswith(".github/workflows/") and rel_path.endswith((".yml", ".yaml"))
    ]
    return sorted(set(workflows))


def parse_test_commands(project_root: Path) -> list[str]:
    package_json = project_root / "package.json"
    if not package_json.exists():
        return []

    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []

    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return []

    command_map = {
        "test": "npm test",
        "test:unit": "npm run test:unit",
        "test:integration": "npm run test:integration",
        "lint": "npm run lint",
        "typecheck": "npm run typecheck",
    }
    commands = [cmd for key, cmd in command_map.items() if key in scripts]
    return commands


def detect_monorepo(project_root: Path, manifests: list[str]) -> bool:
    indicator_files = {"pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json"}
    manifest_names = {Path(path).name for path in manifests}
    if indicator_files.intersection(manifest_names):
        return True

    package_json = project_root / "package.json"
    if not package_json.exists():
        return False

    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False

    return "workspaces" in payload


def top_level_entries(project_root: Path, *, max_entries: int) -> list[str]:
    entries: list[str] = []
    for entry in sorted(project_root.iterdir(), key=lambda p: p.name.lower()):
        name = entry.name
        if name in {".cadence", ".git"}:
            continue
        entries.append(name + ("/" if entry.is_dir() else ""))
    return entries[: max(max_entries, 0)]


def build_baseline(project_root: Path, *, max_entries: int, max_files: int) -> tuple[dict[str, Any], str]:
    file_paths, total_file_count, total_directory_count = iter_inventory_paths(
        project_root,
        max_files=max_files,
    )
    detected_mode = "brownfield" if total_file_count > 0 else "greenfield"

    manifests = collect_manifests(file_paths)
    ci_workflows = collect_ci_workflows(file_paths)
    baseline = {
        "captured_at": utc_now(),
        "repo": detect_git_details(project_root),
        "inventory": {
            "top_level_entries": top_level_entries(project_root, max_entries=max_entries),
            "file_count": total_file_count,
            "directory_count": total_directory_count,
            "inspected_file_count": len(file_paths),
            "languages": infer_languages(file_paths),
            "manifests": manifests,
            "ci_workflows": ci_workflows,
            "test_commands": parse_test_commands(project_root),
            "monorepo_detected": detect_monorepo(project_root, manifests),
        },
    }
    return baseline, detected_mode


def choose_mode(requested_mode: str, detected_mode: str) -> tuple[str, str]:
    mode = requested_mode.strip().lower()
    if mode in {"greenfield", "brownfield"}:
        return mode, "explicit"
    return detected_mode, "auto"


def main() -> int:
    args = parse_args()
    explicit_project_root = args.project_root.strip() or None
    try:
        project_root, project_root_source = resolve_project_root(
            script_dir=SCRIPT_DIR,
            explicit_project_root=explicit_project_root,
            require_cadence=True,
            allow_hint=True,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    write_project_root_hint(SCRIPT_DIR, project_root)
    assert_expected_route(project_root)

    data = load_state(project_root)
    baseline, detected_mode = build_baseline(
        project_root,
        max_entries=args.max_top_level_entries,
        max_files=max(args.max_sample_files, 50),
    )
    selected_mode, mode_source = choose_mode(args.project_mode, detected_mode)

    state = data.setdefault("state", {})
    if not isinstance(state, dict):
        state = {}
        data["state"] = state

    project_details = data.setdefault("project-details", {})
    if not isinstance(project_details, dict):
        project_details = {}
        data["project-details"] = project_details

    state["project-mode"] = selected_mode
    state["brownfield-intake-completed"] = True
    project_details["mode"] = selected_mode
    project_details["last_inventory_at"] = baseline.get("captured_at", "")

    task_status = "complete"
    if selected_mode == "greenfield":
        task_status = "skipped"
        project_details["brownfield_baseline"] = {}
        state["brownfield-documentation-completed"] = False
    else:
        project_details["brownfield_baseline"] = baseline
        state["brownfield-documentation-completed"] = False
        state["ideation-completed"] = False
        state["research-completed"] = False

    data, _ = set_workflow_item_status(
        data,
        item_id="task-brownfield-intake",
        status=task_status,
        cadence_dir_exists=True,
    )
    if selected_mode == "greenfield":
        data, _ = set_workflow_item_status(
            data,
            item_id="task-brownfield-documentation",
            status="skipped",
            cadence_dir_exists=True,
        )
    else:
        for item_id in ("task-brownfield-documentation", "task-ideation", "task-research"):
            data, _ = set_workflow_item_status(
                data,
                item_id=item_id,
                status="pending",
                cadence_dir_exists=True,
            )
    data = reconcile_workflow_state(data, cadence_dir_exists=True)
    save_state(project_root, data)

    inventory = baseline.get("inventory", {})
    response = {
        "status": "ok",
        "project_root": str(project_root),
        "project_root_source": project_root_source,
        "mode": selected_mode,
        "mode_source": mode_source,
        "detected_mode": detected_mode,
        "task_status": task_status,
        "inventory_summary": {
            "file_count": int(inventory.get("file_count", 0)),
            "directory_count": int(inventory.get("directory_count", 0)),
            "manifest_count": len(inventory.get("manifests", []))
            if isinstance(inventory.get("manifests"), list)
            else 0,
            "ci_workflow_count": len(inventory.get("ci_workflows", []))
            if isinstance(inventory.get("ci_workflows"), list)
            else 0,
            "monorepo_detected": bool(inventory.get("monorepo_detected", False)),
        },
    }
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
