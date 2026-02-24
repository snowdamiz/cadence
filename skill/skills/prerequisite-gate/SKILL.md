---
name: prerequisite-gate
description: Run and persist Cadence runtime prerequisite checks. Use when Cadence starts work after scaffolding and must confirm required Cadence runtime assets before lifecycle or delivery commands.
---

# Prerequisite Gate

1. Run this only after scaffold routing from `skills/scaffold/SKILL.md`.
   - Never manually edit `.cadence/cadence.json`; all Cadence state writes must go through Cadence scripts.
   - Do not run Python interpreter availability checks in this workflow gate; installer-time preflight owns that check.
2. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
3. Run `python3 "$CADENCE_SCRIPTS_DIR/run-prerequisite-gate.py" --project-root "$PROJECT_ROOT" --scripts-dir "$CADENCE_SCRIPTS_DIR"`.
4. `run-prerequisite-gate.py` performs workflow route assertion internally; if assertion fails, stop and surface the exact error.
5. If the script reports `MISSING_CADENCE_RUNTIME_ASSET:<files>`, stop and ask the user to repair/reinstall Cadence runtime files before continuing.
6. Do not continue Cadence lifecycle or delivery execution while required runtime assets are missing.
7. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope prerequisite-gate --checkpoint prerequisites-passed --paths .`.
8. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
9. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
10. Surface script failures verbatim instead of adding custom fallback logic.
11. In normal user-facing updates, share the prerequisite outcome without raw command traces or internal routing details unless explicitly requested.

## Strict Response Format

- If `MISSING_CADENCE_RUNTIME_ASSET:<files>` is returned, respond exactly:

  ```text
  Prerequisite status:

  - Cadence runtime assets: missing
  - Cadence prerequisite gate: not passed
  
  Action required: repair or reinstall Cadence skill files, then rerun the prerequisite gate.
  ```

- On successful prerequisite completion, respond exactly:

  ```text
  Prerequisite gate complete:

  - Cadence runtime assets: available
  - Cadence prerequisite gate: passed
  - Checkpoint: prerequisite-gate/prerequisites-passed (<ok|no_changes>)
  
  Next step: Run project mode and baseline intake.
  ```
