---
name: project-progress
description: Read and route project lifecycle progress from .cadence/cadence.json workflow state. Use when users ask to continue or resume work ("continue the project", "continue", "resume", "pick up where we left off") or ask status ("how far along are we?", "where are we in the workflow?", "what phase are we in?").
---

# Project Progress

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence --include-workflow-state`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, push mode from `repo_enabled` (`false` means local-only commits), and workflow payload from `workflow_state`.
   - Never read or edit `.cadence/cadence.json` directly (including `cat`, `rg`, `jq`, or file-read tools). All Cadence state reads and writes must go through Cadence scripts.
2. Always report current progress first with route-aware formatting:
   - current phase title
   - what comes next
   - If `workflow_state.route.skill_name` is `researcher` (or `workflow_state.next_item.id` is `task-research`):
     - Run `python3 "$CADENCE_SCRIPTS_DIR/run-research-pass.py" --project-root "$PROJECT_ROOT" status`.
     - Report research progress only from that output:
       - topics complete vs total
       - topics needing follow-up
       - topics pending
       - completed passes vs pending passes
       - next pass id (if present)
     - Do not show global workflow completion counts/percent in this mode unless the user explicitly asks for full workflow metrics.
   - Otherwise, report completion summary (completed vs total actionable items, percent).
3. Interpret user intent:
   - If the user only asks status, answer with progress and stop.
   - If the user asks to continue or resume, answer with progress and then route using `workflow_state.route.skill_path` from the entry gate payload.
4. Routing rules:
   - If `next_item.id` is `complete`, explain that all currently tracked workflow items are complete and ask whether they want ideation revisions via `skills/ideation-updater/SKILL.md`.
   - If `route.skill_path` is present, invoke that skill.
   - If route skill is `researcher`, keep execution to one pass per conversation and follow researcher handoff behavior between passes.
   - If no route is present for a non-complete item, ask the user what action they want for that item.
5. If `workflow_state.route.skill_name` is `researcher` and `run-research-pass.py status` fails, surface the script error verbatim and stop.
6. If `run-skill-entry-gate.py` errors (including workflow read failures), surface the script error verbatim and stop.
7. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope project-progress --checkpoint progress-checked --paths .`.
8. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
9. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
10. Do not expose raw workflow IDs, route paths, or execution traces in user-facing replies unless the user explicitly asks for internals.

## Strict Response Format

- If routing is `researcher`, respond exactly in this shape:

  ```text
  Research progress:
  
  - Current phase: <phase_title>
  - Topics complete: <topic_complete>/<topic_total>
  - Topics needing follow-up: <topic_needs_followup>
  - Topics pending: <topic_pending>
  - Passes complete: <pass_complete>
  - Passes pending: <pass_pending>
  - Next pass: <next_pass_id or "none">
  - Next route: researcher

  Start a new chat and say "cadence, plan my project".
  ```

  - If the user asked to continue/resume and more passes remain, append this exact line:
    - `Start a new chat and say "continue research".`

- If routing is not `researcher`, respond exactly in this shape:

  ```text
  Workflow progress:

  - Current phase: <phase_title>
  - Completion: <completed_actionable_items>/<total_actionable_items> (<completion_percent>%)
  - Next item: <next_item_title>
  - Next route: <route_skill_name or "none">

  Start a new chat and say "cadence, research my project".
  ```

- If workflow is complete, respond exactly:

  ```text
  Workflow progress:

  - Current phase: Workflow Complete
  - Completion: 100%
  - Status: All currently tracked workflow items are complete.
  ```
