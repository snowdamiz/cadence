---
name: planner
description: Create a greenfield project roadmap from cadence ideation and research by producing high-level milestones and phases only. Use when Cadence route points to planner after research is complete.
---

# Planner

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence --assert-skill-name planner`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
   - Never manually edit `.cadence/cadence.json`; all Cadence state writes must go through Cadence scripts.
2. Discover planning context directly from Cadence state:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-planner.py" --project-root "$PROJECT_ROOT" discover`
3. Optionally enrich discovery with targeted fuzzy search when details are unclear:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-planner.py" --project-root "$PROJECT_ROOT" discover --fuzzy-query "<query>"`
4. Use discovery output to draft a roadmap payload with this scope:
   - Include overarching milestones and phases only.
   - Do not include waves or tasks in this planner version.
   - Keep `detail_level` as `milestone_phase_v1`.
5. Present the proposed milestone/phase roadmap to the user and ask for confirmation.
6. After confirmation, persist the finalized roadmap by piping payload JSON:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-planner.py" --project-root "$PROJECT_ROOT" complete --stdin`
7. Verify persistence and route progression:
   - `python3 "$CADENCE_SCRIPTS_DIR/read-workflow-state.py" --project-root "$PROJECT_ROOT"`
8. At end of this successful skill conversation, run:
   - `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope planner --checkpoint plan-created --paths .`
9. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
10. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
11. In normal user-facing updates, report roadmap outcomes without raw command traces or internal routing details unless explicitly requested.

## Strict Response Format

- Before persistence confirmation, respond exactly in this shape:

  ```text
  Proposed roadmap:

  - Milestones: <milestone_count>
  - Phases: <phase_count>
  - Detail level: milestone_phase_v1
  - Key assumptions: <count or "none">
  
  Confirmation needed: Persist this roadmap? (yes/no)
  ```

- After successful persistence, respond exactly in this shape:

  ```text
  Roadmap captured:

  - Milestones: <milestone_count>
  - Phases: <phase_count>
  - Detail level: milestone_phase_v1
  - Checkpoint: planner/plan-created (<ok|no_changes>)
  
  Next route: <skill_name or "workflow complete">
  ```
