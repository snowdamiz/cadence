---
name: project-overview
description: Read-only project overview for Cadence state. Use when users ask for project overview, roadmap details, full milestone/phase/wave/task view, or current workflow position.
---

# Project Overview

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence --include-workflow-state`
   - Parse JSON and store `PROJECT_ROOT` from `project_root` and `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`.
   - Never read or edit `.cadence/cadence.json` directly (including `cat`, `rg`, `jq`, or file-read tools). All Cadence state reads and writes must go through Cadence scripts.
2. Read project overview payload:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-project-overview.py" --project-root "$PROJECT_ROOT"`
3. Render the response using `roadmap_display_rows` and `roadmap_display_source`:
   - If source is `planning`, render milestone -> phase only (planner v1 scope) in a compact table.
   - If source is `workflow`, render full milestone -> phase -> wave -> task rows in a compact table.
4. Keep the user-facing output minimal and essential only.
5. Include the complete displayed hierarchy; do not truncate any milestones/phases (and waves/tasks when source is workflow).
6. At end of this successful skill conversation, run:
   - `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope project-overview --checkpoint overview-reviewed --paths .`
7. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
8. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
9. Surface script failures verbatim and do not expose internal command traces unless explicitly requested.

## Strict Response Format

Respond exactly in this shape:

```text
Project overview:

| Metric | Value |
| --- | --- |
| Progress | <completion_percent>% (<completed_actionable_items>/<total_actionable_items> actionable items complete) |
| Current | <milestone or "-"> -> <phase or "-"> -> <wave or "-"> -> <task> |
| Current status | <status> |
| Next route | <route_skill_name or "none"> |
| Roadmap source | <planning|workflow> |

Roadmap:

(If roadmap source is `planning`, render this table and include every milestone/phase row with no truncation:)
| Milestone | Phase | Status |
| --- | --- | --- |
| <milestone_title> | <phase_title or "-"> | <status> |

(If roadmap source is `workflow`, render this table and include every task row with no truncation:)
| Milestone | Phase | Wave | Task | Status | Route | Current |
| --- | --- | --- | --- | --- | --- | --- |
| <milestone_title> | <phase_title> | <wave_title> | <task_title> | <status> | <route_skill_name or "-"> | <yes|no> |
```
