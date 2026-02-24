#!/usr/bin/env python3
"""Create and push Cadence checkpoint commits using skill-local conventions."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "commit-conventions.json"


class CheckpointError(RuntimeError):
    """Signal a deterministic checkpoint failure."""


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def format_git_error(prefix: str, result: subprocess.CompletedProcess[str]) -> str:
    detail = result.stderr.strip() or result.stdout.strip() or "UNKNOWN_GIT_ERROR"
    return f"{prefix}: {detail}"


def git_output(args: list[str], cwd: Path, error_prefix: str) -> str:
    result = run_git(args, cwd)
    if result.returncode != 0:
        raise CheckpointError(format_git_error(error_prefix, result))
    return result.stdout.strip()


def load_config() -> dict[str, Any]:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CheckpointError(f"COMMIT_CONFIG_READ_FAILED: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CheckpointError(f"COMMIT_CONFIG_INVALID_JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise CheckpointError("COMMIT_CONFIG_INVALID_TYPE")
    return data


def truncate_subject_fragment(text: str, max_length: int) -> str:
    if max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return text[:max_length]

    clipped = text[: max_length - 3].rstrip()
    if not clipped:
        clipped = text[: max_length - 3]
    return f"{clipped}..."


def build_commit_message(
    config: dict[str, Any],
    scope: str,
    checkpoint: str,
    message_suffix: str = "",
) -> str:
    commit_type = str(config.get("commit_type", "")).strip()
    if not commit_type:
        raise CheckpointError("COMMIT_CONFIG_MISSING_COMMIT_TYPE")

    scopes = config.get("scopes")
    if not isinstance(scopes, dict):
        raise CheckpointError("COMMIT_CONFIG_MISSING_SCOPES")
    if scope not in scopes:
        raise CheckpointError(f"INVALID_SCOPE: {scope}")

    scope_entry = scopes.get(scope)
    if not isinstance(scope_entry, dict):
        raise CheckpointError(f"INVALID_SCOPE_CONFIG: {scope}")

    checkpoints = scope_entry.get("checkpoints")
    if not isinstance(checkpoints, dict):
        raise CheckpointError(f"MISSING_SCOPE_CHECKPOINTS: {scope}")
    if checkpoint not in checkpoints:
        raise CheckpointError(f"INVALID_CHECKPOINT: {scope}/{checkpoint}")

    summary = str(checkpoints[checkpoint]).strip()
    if not summary:
        raise CheckpointError(f"EMPTY_CHECKPOINT_SUMMARY: {scope}/{checkpoint}")

    suffix = str(message_suffix).strip()
    if "\n" in suffix or "\r" in suffix:
        raise CheckpointError("INVALID_MESSAGE_SUFFIX")

    max_length_raw = config.get("subject_max_length", 72)
    try:
        max_length = int(max_length_raw)
    except (TypeError, ValueError) as exc:
        raise CheckpointError("COMMIT_CONFIG_INVALID_SUBJECT_MAX_LENGTH") from exc

    prefix = f"{commit_type}({scope}): "
    if len(prefix) >= max_length:
        raise CheckpointError(f"COMMIT_SUBJECT_PREFIX_TOO_LONG: {len(prefix)}>{max_length}")

    available_for_summary = max_length - len(prefix)
    summary_text = truncate_subject_fragment(summary, available_for_summary)

    message = f"{prefix}{summary_text}"
    if suffix:
        compact_suffix = suffix
        if compact_suffix.startswith("[") and compact_suffix.endswith("]") and len(compact_suffix) >= 2:
            compact_suffix = compact_suffix[1:-1]

        compact_suffix = " ".join(part for part in compact_suffix.split() if part)

        if compact_suffix:
            allowed_content_len = max_length - len(message) - 3
            if allowed_content_len > 0:
                trimmed_suffix = compact_suffix[:allowed_content_len]
                message = f"{message} [{trimmed_suffix}]"

    if len(message) > max_length:
        raise CheckpointError(f"COMMIT_SUBJECT_TOO_LONG: {len(message)}>{max_length}")

    return message


def resolve_repo_root(project_root: Path) -> Path:
    root = git_output(
        ["rev-parse", "--show-toplevel"],
        project_root,
        "NOT_A_GIT_REPOSITORY",
    )
    return Path(root)


def ensure_no_pre_staged_changes(repo_root: Path) -> None:
    staged = git_output(
        ["diff", "--cached", "--name-only"],
        repo_root,
        "FAILED_TO_READ_STAGED_CHANGES",
    )
    if staged:
        raise CheckpointError("STAGED_CHANGES_PRESENT")


def path_exists_or_tracked(repo_root: Path, pathspec: str) -> bool:
    if (repo_root / pathspec).exists():
        return True

    result = run_git(["ls-files", "--error-unmatch", "--", pathspec], repo_root)
    return result.returncode == 0


def stage_paths(repo_root: Path, paths: list[str]) -> None:
    valid_paths = [path for path in paths if path_exists_or_tracked(repo_root, path)]
    if not valid_paths:
        return

    result = run_git(["add", "--", *valid_paths], repo_root)
    if result.returncode != 0:
        raise CheckpointError(format_git_error("GIT_ADD_FAILED", result))


def list_staged_files(repo_root: Path) -> list[str]:
    output = git_output(
        ["diff", "--cached", "--name-only"],
        repo_root,
        "FAILED_TO_READ_STAGED_CHANGES",
    )
    return [line for line in output.splitlines() if line.strip()]


def commit_staged(repo_root: Path, message: str) -> str:
    result = run_git(["commit", "-m", message], repo_root)
    if result.returncode != 0:
        raise CheckpointError(format_git_error("GIT_COMMIT_FAILED", result))
    return git_output(["rev-parse", "HEAD"], repo_root, "FAILED_TO_READ_COMMIT_SHA")


def current_branch(repo_root: Path) -> str:
    branch = git_output(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        repo_root,
        "FAILED_TO_RESOLVE_BRANCH",
    )
    if branch == "HEAD":
        raise CheckpointError("DETACHED_HEAD_NOT_SUPPORTED")
    return branch


def remote_exists(repo_root: Path, remote: str) -> bool:
    result = run_git(["remote", "get-url", remote], repo_root)
    return result.returncode == 0


def has_upstream(repo_root: Path) -> bool:
    result = run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        repo_root,
    )
    return result.returncode == 0


def push_commit(repo_root: Path, remote: str) -> dict[str, str]:
    branch = current_branch(repo_root)
    if not remote_exists(repo_root, remote):
        raise CheckpointError(f"MISSING_REMOTE: {remote}")

    if has_upstream(repo_root):
        result = run_git(["push"], repo_root)
    else:
        result = run_git(["push", "-u", remote, branch], repo_root)

    if result.returncode != 0:
        raise CheckpointError(format_git_error("GIT_PUSH_FAILED", result))

    return {"remote": remote, "branch": branch}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and push a checkpoint commit using skill-local conventions.",
    )
    parser.add_argument("--scope", required=True, help="Commit scope from commit config")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint key from commit config")
    parser.add_argument(
        "--paths",
        nargs="+",
        required=True,
        help="Pathspecs to stage for the checkpoint commit",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Repository path where checkpoint commit should run",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Commit without pushing (used only for local dry runs)",
    )
    parser.add_argument(
        "--message-suffix",
        default="",
        help="Optional short semantic suffix appended to the commit subject",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        config = load_config()
        message = build_commit_message(
            config,
            scope=args.scope,
            checkpoint=args.checkpoint,
            message_suffix=args.message_suffix,
        )
        project_root = Path(args.project_root).resolve()
        repo_root = resolve_repo_root(project_root)
        ensure_no_pre_staged_changes(repo_root)
        stage_paths(repo_root, args.paths)
        staged_files = list_staged_files(repo_root)
        if not staged_files:
            print(
                json.dumps(
                    {
                        "status": "no_changes",
                        "scope": args.scope,
                        "checkpoint": args.checkpoint,
                        "message": message,
                        "message_suffix": args.message_suffix,
                        "repo_root": str(repo_root),
                    }
                )
            )
            return 0

        commit_sha = commit_staged(repo_root, message)

        push_details: dict[str, Any] = {"pushed": False}
        if not args.skip_push:
            remote = str(config.get("default_remote", "origin")).strip() or "origin"
            push_result = push_commit(repo_root, remote)
            push_details = {"pushed": True, **push_result}

        print(
            json.dumps(
                {
                    "status": "ok",
                    "scope": args.scope,
                    "checkpoint": args.checkpoint,
                    "message": message,
                    "message_suffix": args.message_suffix,
                    "commit": commit_sha,
                    "staged_files": staged_files,
                    **push_details,
                }
            )
        )
        return 0
    except CheckpointError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
