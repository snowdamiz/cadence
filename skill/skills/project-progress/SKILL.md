---
name: project-progress
description: Read and route project lifecycle progress from .cadence/cadence.json workflow state. Use when users ask to continue or resume work ("continue the project", "continue", "resume", "pick up where we left off") or ask status ("how far along are we?", "where are we in the workflow?", "what phase are we in?").
---

# Project Progress

1. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --require-cadence` and store stdout in `PROJECT_ROOT`.
2. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
3. Run `python3 "$CADENCE_SCRIPTS_DIR/read-workflow-state.py" --project-root "$PROJECT_ROOT"` and parse the JSON response.
4. Always report current progress first:
   - current phase title
   - completion summary (completed vs total actionable items, percent)
   - what comes next
5. Interpret user intent:
   - If the user only asks status, answer with progress and stop.
   - If the user asks to continue or resume, answer with progress and then route using `route.skill_path` from script output.
6. Routing rules:
   - If `next_item.id` is `complete`, explain that all currently tracked workflow items are complete and ask whether they want ideation revisions via `skills/ideation-updater/SKILL.md`.
   - If `route.skill_path` is present, invoke that skill.
   - If no route is present for a non-complete item, ask the user what action they want for that item.
7. If `read-workflow-state.py` errors, surface the script error verbatim and stop.
8. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope project-progress --checkpoint progress-checked --paths .`.
9. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
10. Do not expose raw workflow IDs, route paths, or execution traces in user-facing replies unless the user explicitly asks for internals.
