#!/usr/bin/env python3
"""Project-root resolution and persistence helpers for Cadence scripts."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT_HINT_FILE = ".last-project-root"


def hint_file_path(script_dir: Path) -> Path:
    return script_dir / PROJECT_ROOT_HINT_FILE


def write_project_root_hint(script_dir: Path, project_root: Path) -> None:
    """Best-effort write of the most recent Cadence project root."""
    try:
        hint_path = hint_file_path(script_dir)
        hint_path.write_text(f"{project_root.resolve()}\n", encoding="utf-8")
    except OSError:
        # Hint persistence is convenience only; never fail gate scripts for this.
        return


def read_project_root_hint(script_dir: Path) -> Path | None:
    hint_path = hint_file_path(script_dir)
    try:
        raw = hint_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    if not raw:
        return None

    candidate = Path(raw).expanduser().resolve()
    if candidate.is_dir() and (candidate / ".cadence").is_dir():
        return candidate
    return None


def read_oldpwd_hint(*, require_cadence: bool = False) -> Path | None:
    raw = os.environ.get("OLDPWD", "").strip()
    if not raw:
        return None

    candidate = Path(raw).expanduser().resolve()
    if not candidate.exists() or not candidate.is_dir():
        return None

    if require_cadence and not (candidate / ".cadence").is_dir():
        return None

    return candidate


def find_cadence_project_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".cadence").is_dir():
            return candidate
    return None


def resolve_project_root(
    *,
    script_dir: Path,
    explicit_project_root: str | None = None,
    require_cadence: bool = False,
    allow_hint: bool = True,
) -> tuple[Path, str]:
    """Resolve the active project root.

    Resolution order:
    1) Explicit `--project-root`
    2) Nearest ancestor of cwd containing `.cadence`
    3) `OLDPWD` when invoked from the skill root (if enabled)
    4) Most recent persisted hint (if enabled)
    5) cwd fallback
    """

    source = "cwd"
    if explicit_project_root:
        project_root = Path(explicit_project_root).expanduser().resolve()
        source = "explicit"
        skill_root = script_dir.resolve().parent
        if project_root == skill_root and not (project_root / ".cadence").is_dir():
            raise ValueError(
                "AMBIGUOUS_PROJECT_ROOT: explicit --project-root resolved to the Cadence skill directory."
            )
    else:
        cwd = Path.cwd().resolve()
        project_root = find_cadence_project_root(cwd) or cwd
        if (project_root / ".cadence").is_dir():
            source = "cwd"
        elif allow_hint:
            if cwd == script_dir.resolve().parent:
                oldpwd_root = read_oldpwd_hint(require_cadence=require_cadence)
                if oldpwd_root is not None and oldpwd_root != cwd:
                    project_root = oldpwd_root
                    source = "oldpwd"
                else:
                    hinted_root = read_project_root_hint(script_dir)
                    if hinted_root is not None:
                        project_root = hinted_root
                        source = "hint"
                    else:
                        source = "cwd-fallback"
            else:
                hinted_root = read_project_root_hint(script_dir)
                if hinted_root is not None:
                    project_root = hinted_root
                    source = "hint"
                else:
                    source = "cwd-fallback"
        else:
            source = "cwd-fallback"

    if require_cadence and not (project_root / ".cadence").is_dir():
        raise ValueError(f"MISSING_CADENCE_DIR: {project_root}")

    if not project_root.exists():
        raise ValueError(f"PROJECT_ROOT_NOT_FOUND: {project_root}")

    if not project_root.is_dir():
        raise ValueError(f"PROJECT_ROOT_NOT_DIRECTORY: {project_root}")

    return project_root, source
