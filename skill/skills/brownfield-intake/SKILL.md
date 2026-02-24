---
name: brownfield-intake
description: Classify project mode (greenfield vs brownfield) and capture a deterministic baseline inventory for existing codebases before ideation routing.
---

# Brownfield Intake

1. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --require-cadence` and store stdout in `PROJECT_ROOT`.
2. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
3. Run `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and parse the JSON output. Treat `repo_enabled` as the authoritative push mode (`false` means local-only commits).
4. Ask the user whether this repository should be treated as `greenfield` or `brownfield`:
   - `greenfield`: net-new project with no meaningful legacy code constraints.
   - `brownfield`: existing codebase where legacy structure/constraints should drive planning.
5. Run the intake gate with explicit mode selection:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-brownfield-intake.py" --project-root "$PROJECT_ROOT" --project-mode <greenfield|brownfield>`
6. `run-brownfield-intake.py` performs workflow route assertion internally; if assertion fails, stop and surface the exact error.
7. If mode is `brownfield`, summarize captured baseline highlights for the user:
   - repository scale (file/directory counts)
   - detected manifests/tooling
   - CI workflows
   - monorepo signal
8. If mode is `brownfield`, tell the user this gate will route to `skills/brownfield-documenter/SKILL.md` next (not ideator), and end with this exact handoff line: `Start a new chat and say "document my existing project".`
9. If mode is `greenfield`, state that brownfield baseline capture was skipped and workflow advanced.
10. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope brownfield-intake --checkpoint baseline-captured --paths .`.
11. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
12. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
13. In normal user-facing updates, report mode decision and baseline outcome without raw command traces or internal routing details unless explicitly requested.
