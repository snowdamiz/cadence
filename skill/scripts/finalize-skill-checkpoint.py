#!/usr/bin/env python3
"""Finalize a skill run by creating atomic semantic checkpoint commits."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
CHECKPOINT_SCRIPT = SCRIPT_DIR / "git-checkpoint.py"
REPO_STATUS_SCRIPT = SCRIPT_DIR / "check-project-repo-status.py"
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "commit-conventions.json"


class FinalizeError(RuntimeError):
    """Signal deterministic finalization failures."""


def run_cmd(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def resolve_repo_root(project_root: Path) -> Path:
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], project_root)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "NOT_A_GIT_REPOSITORY"
        raise FinalizeError(detail)
    return Path(result.stdout.strip()).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create atomic checkpoint commits for changed files at skill finalization.",
    )
    parser.add_argument("--scope", required=True, help="Checkpoint scope")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint key")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["."],
        help="Optional pathspec filters for files eligible for checkpoint commits",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root where git commands should run",
    )
    return parser.parse_args()


def load_config() -> dict[str, Any]:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FinalizeError(f"COMMIT_CONFIG_READ_FAILED: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FinalizeError(f"COMMIT_CONFIG_INVALID_JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise FinalizeError("COMMIT_CONFIG_INVALID_TYPE")
    return data


def normalize_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def parse_status_paths(status_output: str) -> list[str]:
    seen: set[str] = set()
    paths: list[str] = []

    for raw_line in status_output.splitlines():
        line = raw_line.rstrip("\n")
        if len(line) < 4:
            continue
        if line.startswith("!! "):
            continue

        path_part = line[3:]
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]

        path = path_part.strip()
        if path.startswith('"') and path.endswith('"') and len(path) >= 2:
            path = path[1:-1]

        normalized = normalize_path(path)
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        paths.append(normalized)

    return sorted(paths)


def path_matches_spec(path: str, pathspec: str) -> bool:
    spec = normalize_path(pathspec)
    if spec in {"", "."}:
        return True

    if any(token in spec for token in "*?["):
        return fnmatch(path, spec)

    prefix = spec.rstrip("/")
    return path == prefix or path.startswith(f"{prefix}/")


def filter_paths(paths: list[str], pathspecs: list[str]) -> list[str]:
    if not pathspecs:
        return paths

    filtered = [
        path for path in paths if any(path_matches_spec(path, pathspec) for pathspec in pathspecs)
    ]
    return sorted(filtered)


def sanitize_tag(tag: str) -> str:
    raw = "".join(ch.lower() if ch.isalnum() else "-" for ch in tag.strip())
    compact = "-".join(part for part in raw.split("-") if part)
    if not compact:
        compact = "batch"
    return compact[:10]


def project_relative_root(repo_root: Path, project_root: Path) -> str:
    try:
        relative = project_root.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise FinalizeError("PROJECT_ROOT_OUTSIDE_REPOSITORY") from exc
    text = normalize_path(relative.as_posix())
    return "." if text in {"", "."} else text


def normalize_requested_pathspecs(
    *,
    requested_pathspecs: list[str],
    project_root: Path,
    repo_root: Path,
) -> list[str]:
    project_rel = project_relative_root(repo_root, project_root)
    normalized_specs: list[str] = []

    for raw in requested_pathspecs:
        text = str(raw).strip()
        if not text or text == ".":
            normalized = project_rel
        else:
            candidate = Path(text)
            if candidate.is_absolute():
                try:
                    relative = candidate.resolve().relative_to(repo_root.resolve())
                except ValueError as exc:
                    raise FinalizeError(f"PATHSPEC_OUTSIDE_REPOSITORY: {text}") from exc
                normalized = normalize_path(relative.as_posix())
            else:
                parts = candidate.parts
                if any(part == ".." for part in parts):
                    raise FinalizeError(f"PATHSPEC_OUTSIDE_PROJECT_ROOT: {text}")
                rel_text = normalize_path(text)
                if project_rel == ".":
                    normalized = rel_text
                else:
                    normalized = normalize_path(f"{project_rel}/{rel_text}")

        if project_rel != ".":
            project_prefix = project_rel.rstrip("/")
            if normalized != project_prefix and not normalized.startswith(f"{project_prefix}/"):
                raise FinalizeError(f"PATHSPEC_OUTSIDE_PROJECT_ROOT: {text}")

        if not normalized:
            normalized = "."
        if normalized not in normalized_specs:
            normalized_specs.append(normalized)

    if not normalized_specs:
        return [project_rel]
    return normalized_specs


def classify_path(
    path: str,
    group_order: list[str],
    groups: dict[str, Any],
) -> tuple[str, str, str]:
    ordered_keys = [key for key in group_order if key in groups]
    ordered_keys.extend(sorted(key for key in groups.keys() if key not in ordered_keys))

    for key in ordered_keys:
        raw_group = groups.get(key)
        if not isinstance(raw_group, dict):
            continue

        patterns = raw_group.get("patterns")
        if not isinstance(patterns, list):
            continue

        if any(fnmatch(path, str(pattern)) for pattern in patterns):
            label = str(raw_group.get("label", key)).strip() or key
            tag = sanitize_tag(str(raw_group.get("tag", key)))
            return key, label, tag

    if "/" in path:
        top_level = path.split("/", 1)[0]
        return f"area:{top_level}", f"{top_level} area", sanitize_tag(top_level)

    return "area:root", "root files", "root"


def chunk_paths(paths: list[str], size: int) -> list[list[str]]:
    return [paths[index : index + size] for index in range(0, len(paths), size)]


def build_message_suffix(tag: str, index: int, total: int) -> str:
    if total <= 1:
        return f"[{tag}]"
    return f"[{tag}{index}/{total}]"


def build_batches(paths: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
    atomic = config.get("atomic", {})
    if not isinstance(atomic, dict):
        atomic = {}

    max_files_raw = atomic.get("max_files_per_commit", 4)
    try:
        max_files = int(max_files_raw)
    except (TypeError, ValueError):
        max_files = 4
    if max_files < 1:
        max_files = 1

    group_order = atomic.get("group_order", [])
    if not isinstance(group_order, list):
        group_order = []
    group_order = [str(key) for key in group_order]

    groups = atomic.get("groups", {})
    if not isinstance(groups, dict):
        groups = {}

    grouped: dict[str, dict[str, Any]] = {}
    for path in paths:
        key, label, tag = classify_path(path, group_order, groups)
        entry = grouped.setdefault(
            key,
            {
                "label": label,
                "tag": tag,
                "paths": [],
            },
        )
        entry["paths"].append(path)

    ordered_keys = [key for key in group_order if key in grouped]
    ordered_keys.extend(sorted(key for key in grouped.keys() if key not in ordered_keys))

    batches: list[dict[str, Any]] = []
    for key in ordered_keys:
        entry = grouped[key]
        deduped_paths = sorted(set(str(path) for path in entry["paths"]))
        chunks = chunk_paths(deduped_paths, max_files)
        total_chunks = len(chunks)
        for idx, chunk in enumerate(chunks, start=1):
            batches.append(
                {
                    "group_key": key,
                    "group_label": str(entry["label"]),
                    "group_tag": str(entry["tag"]),
                    "batch_index": idx,
                    "batch_total": total_chunks,
                    "paths": chunk,
                    "message_suffix": build_message_suffix(str(entry["tag"]), idx, total_chunks),
                }
            )

    return batches


def parse_json_output(raw_output: str) -> dict[str, Any]:
    text = raw_output.strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"raw_output": text}
    if isinstance(payload, dict):
        return payload
    return {"raw_output": text}


def load_repo_status(project_root: Path) -> dict[str, Any]:
    result = run_cmd(
        [
            sys.executable,
            str(REPO_STATUS_SCRIPT),
            "--project-root",
            str(project_root),
        ],
        project_root,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "REPO_STATUS_CHECK_FAILED"
        raise FinalizeError(detail)

    payload = parse_json_output(result.stdout)
    if payload.get("status") != "ok":
        raise FinalizeError("REPO_STATUS_INVALID_RESPONSE")
    return payload


def run_atomic_commits(
    *,
    project_root: Path,
    scope: str,
    checkpoint: str,
    batches: list[dict[str, Any]],
    push_enabled: bool,
) -> list[dict[str, Any]]:
    commits: list[dict[str, Any]] = []

    for batch in batches:
        command = [
            sys.executable,
            str(CHECKPOINT_SCRIPT),
            "--scope",
            scope,
            "--checkpoint",
            checkpoint,
            "--paths",
            *batch["paths"],
            "--project-root",
            str(project_root),
            "--message-suffix",
            batch["message_suffix"],
        ]
        if not push_enabled:
            command.append("--skip-push")

        result = run_cmd(command, project_root)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "CHECKPOINT_FAILED"
            raise FinalizeError(detail)

        payload = parse_json_output(result.stdout)
        if payload.get("status") == "no_changes":
            continue

        commits.append(
            {
                "group_key": batch["group_key"],
                "group_label": batch["group_label"],
                "message_suffix": batch["message_suffix"],
                "paths": batch["paths"],
                "result": payload,
            }
        )

    return commits


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    try:
        repo_status = load_repo_status(project_root)
    except FinalizeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not bool(repo_status.get("git_initialized", False)):
        print("LOCAL_GIT_REPOSITORY_NOT_INITIALIZED", file=sys.stderr)
        return 2

    try:
        repo_root = resolve_repo_root(project_root)
        scoped_pathspecs = normalize_requested_pathspecs(
            requested_pathspecs=[str(path) for path in args.paths],
            project_root=project_root,
            repo_root=repo_root,
        )
    except FinalizeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    push_enabled = bool(repo_status.get("repo_enabled", False))

    status_result = run_cmd(
        [
            "git",
            "-c",
            "core.quotepath=false",
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        project_root,
    )
    if status_result.returncode != 0:
        detail = status_result.stderr.strip() or status_result.stdout.strip() or "GIT_STATUS_FAILED"
        print(f"GIT_STATUS_FAILED: {detail}", file=sys.stderr)
        return 2

    changed_files = parse_status_paths(status_result.stdout)
    if not changed_files:
        print(
            json.dumps(
                {
                    "status": "no_changes",
                    "scope": args.scope,
                    "checkpoint": args.checkpoint,
                    "reason": "working tree clean",
                }
            )
        )
        return 0

    eligible_files = filter_paths(changed_files, scoped_pathspecs)
    if not eligible_files:
        print(
            json.dumps(
                {
                    "status": "no_changes",
                    "scope": args.scope,
                    "checkpoint": args.checkpoint,
                    "reason": "no changed files matched requested pathspecs",
                }
            )
        )
        return 0

    try:
        config = load_config()
        batches = build_batches(eligible_files, config)
        commits = run_atomic_commits(
            project_root=project_root,
            scope=args.scope,
            checkpoint=args.checkpoint,
            batches=batches,
            push_enabled=push_enabled,
        )
    except FinalizeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not commits:
        print(
            json.dumps(
                {
                    "status": "no_changes",
                    "scope": args.scope,
                    "checkpoint": args.checkpoint,
                    "reason": "no commitable batches after filtering",
                }
            )
        )
        return 0

    print(
        json.dumps(
                {
                    "status": "ok",
                    "scope": args.scope,
                    "checkpoint": args.checkpoint,
                    "atomic": True,
                "changed_file_count": len(eligible_files),
                "batch_count": len(batches),
                    "commit_count": len(commits),
                    "push_enabled": push_enabled,
                    "scoped_pathspecs": scoped_pathspecs,
                    "repo_status": repo_status,
                    "commits": commits,
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
