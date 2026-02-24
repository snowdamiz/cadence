---
name: prerequisite-gate
description: Run and persist Cadence prerequisite checks for Python availability. Use when Cadence starts work after scaffolding and must confirm prerequisites before lifecycle or delivery commands.
---

# Prerequisite Gate

1. Run this only after scaffold routing from `skills/scaffold/SKILL.md`.
   - Never manually edit `.cadence/cadence.json`; all Cadence state writes must go through Cadence scripts.
2. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
3. Run `python3 "$CADENCE_SCRIPTS_DIR/run-prerequisite-gate.py" --project-root "$PROJECT_ROOT" --scripts-dir "$CADENCE_SCRIPTS_DIR"`.
4. `run-prerequisite-gate.py` performs workflow route assertion internally; if assertion fails, stop and surface the exact error.
5. If the script reports `MISSING_PYTHON3`, stop and ask the user for confirmation to install prerequisites.
6. Do not continue Cadence lifecycle or delivery execution while prerequisites are missing.
7. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope prerequisite-gate --checkpoint prerequisites-passed --paths .`.
8. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
9. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
10. Surface script failures verbatim instead of adding custom fallback logic.
11. In normal user-facing updates, share the prerequisite outcome without raw command traces or internal routing details unless explicitly requested.
