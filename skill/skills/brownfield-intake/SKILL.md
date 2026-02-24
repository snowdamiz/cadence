---
name: brownfield-intake
description: Classify project mode (greenfield vs brownfield) and capture a deterministic baseline inventory for existing codebases before ideation routing.
---

# Project Mode Intake

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
   - Never read or edit `.cadence/cadence.json` directly (including `cat`, `rg`, `jq`, or file-read tools). All Cadence state reads and writes must go through Cadence scripts.
2. Run the intake gate in auto mode (default behavior):
   - `python3 "$CADENCE_SCRIPTS_DIR/run-brownfield-intake.py" --project-root "$PROJECT_ROOT" --project-mode auto`
3. Parse the intake JSON response and store `mode`, `mode_source`, and `detected_mode` for user-facing summary.
4. Do not ask the user to choose `greenfield` vs `brownfield` before running intake. A clean repository should auto-resolve to `greenfield`.
5. If the user explicitly asks to force a specific mode, rerun intake with explicit mode selection:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-brownfield-intake.py" --project-root "$PROJECT_ROOT" --project-mode <greenfield|brownfield>`
6. `run-brownfield-intake.py` performs workflow route assertion internally; if assertion fails, stop and surface the exact error.
7. In user-facing updates before mode is determined, refer to this step as `project mode intake`; do not call the repository brownfield before the result is known.
8. If mode is `brownfield`, summarize captured baseline highlights for the user:
   - repository scale (file/directory counts)
   - detected manifests/tooling
   - CI workflows
   - monorepo signal
9. If mode is `brownfield`, tell the user this gate will route to `skills/brownfield-documenter/SKILL.md` next (not ideator), and end with this exact handoff line: `Start a new chat and say "document my existing project".`
10. If mode is `greenfield`, state that existing-code baseline capture was skipped and workflow advanced.
11. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope brownfield-intake --checkpoint baseline-captured --paths .`.
12. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
13. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
14. In normal user-facing updates, report mode decision and baseline outcome without raw command traces or internal routing details unless explicitly requested.

## Strict Response Format

- If resulting mode is `brownfield`, respond exactly in this shape:

  ```text
  Project mode intake result:

  - Mode: brownfield (source: <mode_source>; detected: <detected_mode>)
  - Repository scale: files=<file_count>, directories=<directory_count>
  - Tooling manifests: <count>
  - CI workflows: <count>
  - Monorepo signal: <yes|no>
  - Checkpoint: brownfield-intake/baseline-captured (<ok|no_changes>)

  Start a new chat and say "cadence, document my existing project".
  ```

- If resulting mode is `greenfield`, respond exactly in this shape:

  ```text
  Project mode intake result:
  
  - Mode: greenfield (source: <mode_source>; detected: <detected_mode>)
  - Existing-code baseline: skipped (clean repository)
  - Checkpoint: brownfield-intake/baseline-captured (<ok|no_changes>)
  - Next step: Continue with ideation.

   Start a new chat and say "cadence, help define my project".
  ```
