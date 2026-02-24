#!/usr/bin/env python3
"""Discover and persist brownfield documentation in two explicit steps.

This script intentionally separates:
1) discovery (programmatic context extraction only)
2) completion (persist AI-authored ideation/research payload)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from ideation_research import normalize_ideation_research, reset_research_execution
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
        description="Discover and persist brownfield documentation for Cadence.",
    )
    parser.add_argument(
        "--project-root",
        default="",
        help="Explicit project root path override.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser(
        "discover",
        help="Extract deterministic repository context for AI-led analysis (no state mutation).",
    )
    discover.add_argument(
        "--max-scan-files",
        type=int,
        default=12000,
        help="Maximum files to scan while extracting brownfield context.",
    )
    discover.add_argument(
        "--max-doc-snippets",
        type=int,
        default=10,
        help="Maximum documentation snippets to capture.",
    )
    discover.add_argument(
        "--max-package-manifests",
        type=int,
        default=40,
        help="Maximum package manifests to parse for signals.",
    )

    complete = subparsers.add_parser(
        "complete",
        help="Persist AI-authored ideation/research payload and advance workflow.",
    )
    payload_group = complete.add_mutually_exclusive_group(required=True)
    payload_group.add_argument("--file", help="Path to ideation payload JSON file")
    payload_group.add_argument("--json", help="Inline ideation payload JSON")
    payload_group.add_argument("--stdin", action="store_true", help="Read ideation payload JSON from stdin")

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
            "brownfield-documenter",
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


def safe_read_text(path: Path, max_chars: int = 2000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def first_sentence(text: str) -> str:
    candidate = str(text).strip()
    if not candidate:
        return ""
    match = re.search(r"(.+?[.!?])(\s|$)", candidate)
    if match:
        return match.group(1).strip()
    return candidate[:240]


def iter_repo_files(
    project_root: Path,
    *,
    max_scan_files: int,
) -> tuple[list[str], dict[str, int], dict[str, int], bool]:
    files: list[str] = []
    ext_counts: dict[str, int] = {}
    top_dir_counts: dict[str, int] = {}
    scanned = 0
    truncated = False

    for root, dirs, filenames in os.walk(project_root):
        dirs[:] = [name for name in dirs if name not in DEFAULT_EXCLUDED_DIRS]
        rel_root = Path(root).resolve().relative_to(project_root)

        for filename in filenames:
            if scanned >= max_scan_files:
                truncated = True
                return files, ext_counts, top_dir_counts, truncated
            if filename.startswith(".DS_Store"):
                continue

            rel_path = (rel_root / filename).as_posix() if str(rel_root) != "." else filename
            files.append(rel_path)
            scanned += 1

            ext = Path(rel_path).suffix.lower() or "(no-ext)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

            parts = Path(rel_path).parts
            top_dir = parts[0] if len(parts) > 1 else "(root)"
            top_dir_counts[top_dir] = top_dir_counts.get(top_dir, 0) + 1

    files.sort()
    return files, ext_counts, top_dir_counts, truncated


def parse_package_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None

    scripts = payload.get("scripts")
    scripts = scripts if isinstance(scripts, dict) else {}
    deps = payload.get("dependencies")
    deps = deps if isinstance(deps, dict) else {}
    dev_deps = payload.get("devDependencies")
    dev_deps = dev_deps if isinstance(dev_deps, dict) else {}

    return {
        "path": str(path),
        "name": str(payload.get("name", "")).strip(),
        "private": bool(payload.get("private", False)),
        "script_keys": sorted(str(key) for key in scripts.keys())[:20],
        "dependency_keys": sorted(str(key) for key in deps.keys())[:60],
        "dev_dependency_keys": sorted(str(key) for key in dev_deps.keys())[:60],
        "dependency_count": len(deps),
        "dev_dependency_count": len(dev_deps),
        "description": str(payload.get("description", "")).strip(),
    }


def collect_manifest_details(
    project_root: Path,
    files: list[str],
    *,
    max_package_manifests: int,
) -> dict[str, Any]:
    manifests: list[str] = []
    package_manifests: list[dict[str, Any]] = []
    ci_workflows: list[str] = []
    docker_files: list[str] = []
    dependency_names: set[str] = set()
    package_json_paths: list[str] = []

    for rel_path in files:
        lower = rel_path.lower()
        name = Path(rel_path).name
        if name in KNOWN_MANIFESTS:
            manifests.append(rel_path)
        if rel_path.startswith(".github/workflows/") and lower.endswith((".yml", ".yaml")):
            ci_workflows.append(rel_path)
        if name == "Dockerfile" or lower.endswith("docker-compose.yml") or lower.endswith("docker-compose.yaml"):
            docker_files.append(rel_path)
        if name == "package.json":
            package_json_paths.append(rel_path)

    for rel_path in sorted(package_json_paths)[: max(max_package_manifests, 0)]:
        manifest = parse_package_json(project_root / rel_path)
        if manifest is None:
            continue
        manifest["path"] = rel_path
        package_manifests.append(manifest)
        for dep in manifest["dependency_keys"]:
            dependency_names.add(dep.lower())
        for dep in manifest["dev_dependency_keys"]:
            dependency_names.add(dep.lower())

    return {
        "manifests": sorted(set(manifests)),
        "package_manifests": package_manifests,
        "ci_workflows": sorted(set(ci_workflows)),
        "docker_files": sorted(set(docker_files)),
        "dependency_names": sorted(dependency_names),
    }


def collect_docs(project_root: Path, files: list[str], *, max_doc_snippets: int) -> list[dict[str, str]]:
    candidates: list[str] = []
    for rel_path in files:
        lower = rel_path.lower()
        name = Path(lower).name
        if name.startswith("readme") and lower.endswith((".md", ".mdx", ".txt", ".rst", ".adoc")):
            candidates.append(rel_path)
            continue
        if lower.startswith("docs/") and lower.endswith((".md", ".mdx", ".txt", ".rst", ".adoc")):
            candidates.append(rel_path)
            continue
        if name in {"about.md", "architecture.md", "changelog.md"}:
            candidates.append(rel_path)

    ordered = sorted(set(candidates), key=lambda path: (0 if Path(path).name.lower().startswith("readme") else 1, path))
    docs: list[dict[str, str]] = []
    for rel_path in ordered[: max(max_doc_snippets, 0)]:
        snippet = safe_read_text(project_root / rel_path, max_chars=3000)
        docs.append(
            {
                "path": rel_path,
                "snippet": snippet,
                "summary_sentence": first_sentence(snippet),
            }
        )
    return docs


def top_items(counts: dict[str, int], *, limit: int) -> list[dict[str, Any]]:
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"name": name, "count": count} for name, count in ranked[: max(limit, 0)]]


def collect_context(
    project_root: Path,
    *,
    max_scan_files: int,
    max_doc_snippets: int,
    max_package_manifests: int,
) -> dict[str, Any]:
    files, ext_counts, top_dir_counts, truncated = iter_repo_files(
        project_root,
        max_scan_files=max_scan_files,
    )
    manifest_details = collect_manifest_details(
        project_root,
        files,
        max_package_manifests=max_package_manifests,
    )
    docs = collect_docs(project_root, files, max_doc_snippets=max_doc_snippets)

    return {
        "captured_at": utc_now(),
        "scan": {
            "max_scan_files": max_scan_files,
            "scanned_file_count": len(files),
            "truncated": truncated,
        },
        "inventory": {
            "top_directories": top_items(top_dir_counts, limit=16),
            "top_extensions": top_items(ext_counts, limit=16),
            "manifests": manifest_details["manifests"],
            "package_manifests": manifest_details["package_manifests"],
            "ci_workflows": manifest_details["ci_workflows"],
            "docker_files": manifest_details["docker_files"],
            "dependency_names": manifest_details["dependency_names"],
        },
        "docs": docs,
        "suggested_entrypoints": {
            "docs": [entry["path"] for entry in docs[:5]],
            "directories": [entry["name"] for entry in top_items(top_dir_counts, limit=8)],
            "manifests": manifest_details["manifests"][:12],
        },
    }


def parse_payload(args: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    if args.file:
        file_path = Path(args.file).expanduser()
        if not file_path.is_absolute():
            file_path = (project_root / file_path).resolve()
        try:
            raw = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"PAYLOAD_READ_FAILED: {exc}") from exc
    elif args.json:
        raw = args.json
    else:
        raw = sys.stdin.read()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_PAYLOAD_JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("IDEATION_PAYLOAD_MUST_BE_OBJECT")
    return payload


def ensure_brownfield_mode(data: dict[str, Any]) -> None:
    state = data.get("state")
    state = state if isinstance(state, dict) else {}
    mode = str(state.get("project-mode", "")).strip().lower()
    if mode != "brownfield":
        raise ValueError(f"BROWNFIELD_MODE_REQUIRED: project-mode={mode or 'unknown'}")


def complete_flow(args: argparse.Namespace, project_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    ensure_brownfield_mode(data)
    payload = parse_payload(args, project_root)
    normalized = normalize_ideation_research(payload, require_topics=True)
    normalized = reset_research_execution(normalized)
    data["ideation"] = normalized

    state = data.setdefault("state", {})
    if not isinstance(state, dict):
        state = {}
        data["state"] = state

    project_details = data.setdefault("project-details", {})
    if not isinstance(project_details, dict):
        project_details = {}
        data["project-details"] = project_details

    project_details["mode"] = "brownfield"
    project_details["last_documentation_at"] = utc_now()
    baseline = project_details.get("brownfield_baseline")
    baseline = baseline if isinstance(baseline, dict) else {}
    project_details["brownfield_baseline"] = baseline

    state["brownfield-documentation-completed"] = True
    state["ideation-completed"] = True
    state["research-completed"] = False

    data, _ = set_workflow_item_status(
        data,
        item_id="task-brownfield-documentation",
        status="complete",
        cadence_dir_exists=True,
    )
    data, _ = set_workflow_item_status(
        data,
        item_id="task-ideation",
        status="skipped",
        cadence_dir_exists=True,
    )
    data, _ = set_workflow_item_status(
        data,
        item_id="task-research",
        status="pending",
        cadence_dir_exists=True,
    )
    data = reconcile_workflow_state(data, cadence_dir_exists=True)
    save_state(project_root, data)

    agenda = normalized.get("research_agenda", {})
    summary = agenda.get("summary", {}) if isinstance(agenda, dict) else {}
    return {
        "status": "ok",
        "mode": "brownfield",
        "action": "complete",
        "project_root": str(project_root),
        "ideation_summary": {
            "objective": str(normalized.get("objective", "")),
            "block_count": int(summary.get("block_count", 0)),
            "topic_count": int(summary.get("topic_count", 0)),
            "entity_count": int(summary.get("entity_count", 0)),
        },
        "next_route": data.get("workflow", {}).get("next_route", {}),
    }


def discover_flow(args: argparse.Namespace, project_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    ensure_brownfield_mode(data)
    context = collect_context(
        project_root,
        max_scan_files=max(args.max_scan_files, 400),
        max_doc_snippets=max(args.max_doc_snippets, 1),
        max_package_manifests=max(args.max_package_manifests, 1),
    )
    return {
        "status": "ok",
        "mode": "brownfield",
        "action": "discover",
        "project_root": str(project_root),
        "context": context,
    }


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

    try:
        if args.command == "discover":
            response = discover_flow(args, project_root, data)
        else:
            response = complete_flow(args, project_root, data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    response["project_root_source"] = project_root_source
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
