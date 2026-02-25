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
3. Render the response as tables using only values from script output.
4. Include the complete roadmap table from `roadmap_rows`; do not truncate rows.
5. At end of this successful skill conversation, run:
   - `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope project-overview --checkpoint overview-reviewed --paths .`
6. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
7. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
8. Surface script failures verbatim and do not expose internal command traces unless explicitly requested.

## Strict Response Format

Respond exactly in this shape:

```text
Project overview:

| Field | Value |
| --- | --- |
| Project mode | <project_mode> |
| Repo enabled | <true|false> |
| Ideation completed | <true|false> |
| Research completed | <true|false> |
| Planning status | <planning_status> |
| Planning detail level | <planning_detail_level or "none"> |
| Objective | <objective or "none"> |
| Core outcome | <core_outcome or "none"> |

Workflow progress:

| Metric | Value |
| --- | --- |
| Completion | <completion_percent>% |
| Actionable items | <completed_actionable_items>/<total_actionable_items> |
| In progress | <in_progress_actionable_items> |
| Pending | <pending_actionable_items> |
| Blocked | <blocked_actionable_items> |

Current position:

| Milestone | Phase | Wave | Task | Status | Next route |
| --- | --- | --- | --- | --- | --- |
| <milestone or "-"> | <phase or "-"> | <wave or "-"> | <task> | <status> | <route_skill_name or "none"> |

Roadmap level summary:

| Level | Total | Complete | In progress | Pending | Blocked | Skipped |
| --- | --- | --- | --- | --- | --- | --- |
| milestone | <n> | <n> | <n> | <n> | <n> | <n> |
| phase | <n> | <n> | <n> | <n> | <n> | <n> |
| wave | <n> | <n> | <n> | <n> | <n> | <n> |
| task | <n> | <n> | <n> | <n> | <n> | <n> |

Roadmap:

| Milestone | Phase | Wave | Task | Status | Route | Current |
| --- | --- | --- | --- | --- | --- | --- |
| <milestone> | <phase> | <wave> | <task> | <status> | <route_skill_name or "-"> | <yes|no> |
| <milestone> | <phase> | <wave> | <task> | <status> | <route_skill_name or "-"> | <yes|no> |

Planning outline:

| Milestone | Phase count | Phase names |
| --- | --- | --- |
| <milestone_title> | <phase_count> | <phase_name_1>; <phase_name_2> |
| <milestone_title> | <phase_count> | <phase_name_1>; <phase_name_2>; <phase_name_3> |
```
