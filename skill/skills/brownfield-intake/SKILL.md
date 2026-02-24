---
name: brownfield-intake
description: Classify project mode (greenfield vs brownfield) and capture a deterministic baseline inventory for existing codebases before ideation routing.
---

# Brownfield Intake

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
   - Never manually edit `.cadence/cadence.json`; all Cadence state writes must go through Cadence scripts.
2. Ask the user whether this repository should be treated as `greenfield` or `brownfield`:
   - `greenfield`: net-new project with no meaningful legacy code constraints.
   - `brownfield`: existing codebase where legacy structure/constraints should drive planning.
3. Run the intake gate with explicit mode selection:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-brownfield-intake.py" --project-root "$PROJECT_ROOT" --project-mode <greenfield|brownfield>`
4. `run-brownfield-intake.py` performs workflow route assertion internally; if assertion fails, stop and surface the exact error.
5. If mode is `brownfield`, summarize captured baseline highlights for the user:
   - repository scale (file/directory counts)
   - detected manifests/tooling
   - CI workflows
   - monorepo signal
6. If mode is `brownfield`, tell the user this gate will route to `skills/brownfield-documenter/SKILL.md` next (not ideator), and end with this exact handoff line: `Start a new chat and say "document my existing project".`
7. If mode is `greenfield`, state that brownfield baseline capture was skipped and workflow advanced.
8. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope brownfield-intake --checkpoint baseline-captured --paths .`.
9. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
10. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
11. In normal user-facing updates, report mode decision and baseline outcome without raw command traces or internal routing details unless explicitly requested.
