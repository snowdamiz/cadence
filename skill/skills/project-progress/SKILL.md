---
name: project-progress
description: Read and route project lifecycle progress from .cadence/cadence.json workflow state. Use when users ask to continue or resume work ("continue the project", "continue", "resume", "pick up where we left off") or ask status ("how far along are we?", "where are we in the workflow?", "what phase are we in?").
---

# Project Progress

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence --include-workflow-state`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, push mode from `repo_enabled` (`false` means local-only commits), and workflow payload from `workflow_state`.
   - Never manually edit `.cadence/cadence.json`; all Cadence state writes must go through Cadence scripts.
2. Always report current progress first:
   - current phase title
   - completion summary (completed vs total actionable items, percent)
   - what comes next
3. Interpret user intent:
   - If the user only asks status, answer with progress and stop.
   - If the user asks to continue or resume, answer with progress and then route using `workflow_state.route.skill_path` from the entry gate payload.
4. Routing rules:
   - If `next_item.id` is `complete`, explain that all currently tracked workflow items are complete and ask whether they want ideation revisions via `skills/ideation-updater/SKILL.md`.
   - If `route.skill_path` is present, invoke that skill.
   - If route skill is `researcher`, keep execution to one pass per conversation and follow researcher handoff behavior between passes.
   - If no route is present for a non-complete item, ask the user what action they want for that item.
5. If `run-skill-entry-gate.py` errors (including workflow read failures), surface the script error verbatim and stop.
6. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope project-progress --checkpoint progress-checked --paths .`.
7. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
8. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
9. Do not expose raw workflow IDs, route paths, or execution traces in user-facing replies unless the user explicitly asks for internals.
