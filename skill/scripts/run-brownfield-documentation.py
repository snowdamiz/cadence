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


def _slug_token(value: Any, fallback: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")
    if token:
        return token
    fallback_token = re.sub(r"[^a-z0-9]+", "-", str(fallback).strip().lower()).strip("-")
    return fallback_token or "item"


def _coerce_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = list(value)
    else:
        raw = [value]

    values: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text and text not in values:
            values.append(text)
    return values


def _unique_token(seed: str, used: set[str]) -> str:
    candidate = seed
    index = 2
    while candidate in used:
        candidate = f"{seed}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _normalized_aliases(label: str, aliases: Any) -> list[str]:
    values = _coerce_text_list(aliases)
    if label and label not in values:
        values.insert(0, label)
    return values


def repair_research_entity_links(payload: dict[str, Any]) -> dict[str, Any]:
    """Auto-repair cross-block entity references to reduce avoidable validation failures."""

    repairs: dict[str, Any] = {
        "applied": False,
        "generated_block_ids": 0,
        "created_entities": 0,
        "owner_assignments": 0,
        "cross_block_relinks": 0,
        "unknown_owner_resets": 0,
    }

    agenda = payload.get("research_agenda")
    if not isinstance(agenda, dict):
        return repairs

    blocks = agenda.get("blocks")
    if not isinstance(blocks, list):
        return repairs

    block_ids: list[str] = []
    for index, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("block_id", "")).strip()
        if not block_id:
            block_id = f"block-{index}"
            block["block_id"] = block_id
            repairs["generated_block_ids"] += 1
        block_ids.append(block_id)

    if not block_ids:
        return repairs

    block_id_set = set(block_ids)
    entity_registry_raw = agenda.get("entity_registry")
    entity_registry_raw = entity_registry_raw if isinstance(entity_registry_raw, list) else []

    used_entity_ids: set[str] = set()
    entity_index: dict[str, dict[str, Any]] = {}
    entity_order: list[str] = []

    for index, raw_entry in enumerate(entity_registry_raw, start=1):
        entry = dict(raw_entry) if isinstance(raw_entry, dict) else {"label": raw_entry}
        label = str(entry.get("label") or entry.get("name") or entry.get("entity_id") or entry.get("id") or "").strip()
        seed = _slug_token(entry.get("entity_id") or entry.get("id") or label, f"entity-{index}")
        owner_block_id = str(entry.get("owner_block_id") or entry.get("owner") or "").strip()
        kind = str(entry.get("kind") or entry.get("type") or "entity").strip() or "entity"
        aliases = _normalized_aliases(label, entry.get("aliases"))

        if seed in entity_index:
            existing = entity_index[seed]
            existing_owner = str(existing.get("owner_block_id", "")).strip()
            if owner_block_id and existing_owner and owner_block_id != existing_owner:
                seed = _unique_token(
                    f"{seed}--{_slug_token(owner_block_id, 'block')}",
                    used_entity_ids,
                )
            else:
                if not existing_owner and owner_block_id:
                    existing["owner_block_id"] = owner_block_id
                for alias in aliases:
                    if alias not in existing["aliases"]:
                        existing["aliases"].append(alias)
                continue
        else:
            seed = _unique_token(seed, used_entity_ids)

        entity = {
            "entity_id": seed,
            "label": label or seed.replace("-", " ").title(),
            "kind": kind,
            "aliases": aliases,
            "owner_block_id": owner_block_id,
        }
        entity_index[seed] = entity
        entity_order.append(seed)

    clone_cache: dict[tuple[str, str], str] = {}
    synthetic_index = 0

    for block_index, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("block_id") or f"block-{block_index}").strip()
        topics = block.get("topics")
        topics = topics if isinstance(topics, list) else []

        for topic in topics:
            if not isinstance(topic, dict):
                continue

            related_raw = topic.get("related_entities")
            related_entities = _coerce_text_list(related_raw)
            if not related_entities:
                topic["related_entities"] = []
                continue

            repaired_related: list[str] = []
            for raw_entity in related_entities:
                entity_seed = _slug_token(raw_entity, "entity")
                entity_id = entity_seed

                if entity_id not in entity_index:
                    synthetic_index += 1
                    if entity_id in used_entity_ids:
                        entity_id = _unique_token(f"{entity_seed}-{synthetic_index}", used_entity_ids)
                    else:
                        used_entity_ids.add(entity_id)
                    label = str(raw_entity).strip() or entity_id.replace("-", " ").title()
                    entity_index[entity_id] = {
                        "entity_id": entity_id,
                        "label": label,
                        "kind": "entity",
                        "aliases": [label] if label else [],
                        "owner_block_id": block_id,
                    }
                    entity_order.append(entity_id)
                    repairs["created_entities"] += 1
                    repairs["owner_assignments"] += 1

                entity = entity_index[entity_id]
                owner_block_id = str(entity.get("owner_block_id", "")).strip()

                if owner_block_id and owner_block_id != block_id:
                    cache_key = (entity_id, block_id)
                    clone_id = clone_cache.get(cache_key, "")
                    if not clone_id:
                        clone_id = _unique_token(
                            f"{entity_id}--{_slug_token(block_id, 'block')}",
                            used_entity_ids,
                        )
                        clone = dict(entity)
                        clone["entity_id"] = clone_id
                        clone["owner_block_id"] = block_id
                        clone["aliases"] = _normalized_aliases(
                            str(clone.get("label", "")).strip(),
                            clone.get("aliases"),
                        )
                        entity_index[clone_id] = clone
                        entity_order.append(clone_id)
                        clone_cache[cache_key] = clone_id
                        repairs["created_entities"] += 1
                    repaired_related.append(clone_id)
                    repairs["cross_block_relinks"] += 1
                    continue

                if not owner_block_id:
                    entity["owner_block_id"] = block_id
                    repairs["owner_assignments"] += 1

                repaired_related.append(entity_id)

            deduped_related: list[str] = []
            for entity_id in repaired_related:
                if entity_id not in deduped_related:
                    deduped_related.append(entity_id)
            topic["related_entities"] = deduped_related

    for entity_id in entity_order:
        entity = entity_index.get(entity_id)
        if not isinstance(entity, dict):
            continue
        owner_block_id = str(entity.get("owner_block_id", "")).strip()
        if owner_block_id and owner_block_id not in block_id_set:
            entity["owner_block_id"] = ""
            repairs["unknown_owner_resets"] += 1
        entity["aliases"] = _normalized_aliases(str(entity.get("label", "")).strip(), entity.get("aliases"))
        entity["kind"] = str(entity.get("kind", "")).strip() or "entity"

    agenda["entity_registry"] = [entity_index[entity_id] for entity_id in entity_order]
    payload["research_agenda"] = agenda

    repairs["applied"] = any(
        int(repairs[key]) > 0
        for key in (
            "generated_block_ids",
            "created_entities",
            "owner_assignments",
            "cross_block_relinks",
            "unknown_owner_resets",
        )
    )
    return repairs


def ensure_brownfield_mode(data: dict[str, Any]) -> None:
    state = data.get("state")
    state = state if isinstance(state, dict) else {}
    mode = str(state.get("project-mode", "")).strip().lower()
    if mode != "brownfield":
        raise ValueError(f"BROWNFIELD_MODE_REQUIRED: project-mode={mode or 'unknown'}")


def complete_flow(args: argparse.Namespace, project_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    ensure_brownfield_mode(data)
    payload = parse_payload(args, project_root)
    repair_summary = repair_research_entity_links(payload)
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
        "payload_repairs": repair_summary,
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
