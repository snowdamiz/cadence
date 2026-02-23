---
name: project-progress
description: Read and route project lifecycle progress from .cadence/cadence.json workflow state. Use when users ask to continue or resume work ("continue the project", "continue", "resume", "pick up where we left off") or ask status ("how far along are we?", "where are we in the workflow?", "what phase are we in?").
---

# Project Progress

1. Run `python3 ../../scripts/read-workflow-state.py` and parse the JSON response.
2. Always report current progress first:
   - current phase title
   - completion summary (completed vs total actionable items, percent)
   - what comes next
3. Interpret user intent:
   - If the user only asks status, answer with progress and stop.
   - If the user asks to continue or resume, answer with progress and then route using `route.skill_path` from script output.
4. Routing rules:
   - If `next_item.id` is `complete`, explain that all currently tracked workflow items are complete and ask whether they want ideation revisions via `skills/ideation-updater/SKILL.md`.
   - If `route.skill_path` is present, invoke that skill.
   - If no route is present for a non-complete item, ask the user what action they want for that item.
5. If `read-workflow-state.py` errors, surface the script error verbatim and stop.
6. At end of this successful skill conversation, run `python3 ../../scripts/finalize-skill-checkpoint.py --scope project-progress --checkpoint progress-checked --paths .`.
7. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
8. Do not expose raw workflow IDs, route paths, or execution traces in user-facing replies unless the user explicitly asks for internals.
