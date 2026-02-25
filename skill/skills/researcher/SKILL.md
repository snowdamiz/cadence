---
name: researcher
description: Execute ideation research agenda topics through dynamic multi-pass web research with strict context control. Use when Cadence route points to researcher and ideation is complete, especially when many topics require multiple passes and per-pass handoff resets.
---

# Researcher

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence --assert-skill-name researcher`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
   - If route assertion fails, stop and surface the exact error to the user.
   - Never read or edit `.cadence/cadence.json` directly (including `cat`, `rg`, `jq`, or file-read tools). All Cadence state reads and writes must go through Cadence scripts.
2. Start exactly one research pass for this conversation by running `python3 "$CADENCE_SCRIPTS_DIR/run-research-pass.py" --project-root "$PROJECT_ROOT" start --ack-handoff` and parse the JSON output.
3. If start output returns `research_complete=true`, report that all research topics are complete and skip pass execution.
4. If start output returns a `pass`, research only the topics listed in that pass:
   - Use web browsing for current, source-backed information.
   - Keep scope limited to the pass topics; do not expand into other pending topics.
   - Use `pass.topics[].latest_summary` and `pass.topics[].unresolved_questions` from `start` output as prior-pass context.
   - If additional Cadence context is required, read it only through scripts:
     - `python3 "$CADENCE_SCRIPTS_DIR/get-ideation.py" --project-root "$PROJECT_ROOT"`
     - `python3 "$CADENCE_SCRIPTS_DIR/query-ideation-research.py" --project-root "$PROJECT_ROOT" --topic-id "<topic_id>"`
   - Never run direct file reads/searches against `.cadence/cadence.json` (for example `cat`, `rg`, `jq`, or file-read tools).
   - Capture concise findings and source links per topic.
5. Build a pass result JSON payload in-memory with this shape:
   - `pass_summary` (string)
   - `topics` (array)
   - Each `topics[]` item must include:
     - `topic_id` (string, must be in current pass topic_ids)
     - `status` (`complete`, `complete_with_caveats`, or `needs_followup`)
     - `summary` (string)
     - `confidence` (`low|medium|high`)
     - `unresolved_questions` (array of strings)
     - `sources` (array of objects with at least `url`; optional: `title`, `publisher`, `published_at`, `notes`)
6. Complete the pass without writing any extra state files by piping payload JSON to:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-research-pass.py" --project-root "$PROJECT_ROOT" complete --pass-id "<pass_id_from_start_output>" --stdin`
7. Never start a second pass in the same conversation.
8. If complete output returns `handoff_required=true`, end with this exact handoff line and stop: `Start a new chat and say "continue research".`
9. If complete output returns `research_complete=true`:
   - Run `python3 "$CADENCE_SCRIPTS_DIR/read-workflow-state.py" --project-root "$PROJECT_ROOT"` and inspect `route.skill_name`.
   - If `route.skill_name` is `planner`, end with this exact handoff line: `Start a new chat and say "plan my project".`
   - If workflow is complete, report that research and currently tracked workflow items are complete.
10. Strict user-facing return format is required for all successful runs. Use the exact section order below and fill values from script output (and the just-submitted pass payload where applicable):
   - If `complete` returns `handoff_required=true`, respond exactly in this structure, then stop:

     ```text
     Pass recorded:

     - Pass ID: <pass_id>
     - Pass summary: <pass_summary>

     Topic outcomes:

     - <topic_id>: <status>; confidence=<confidence>; unresolved_questions=<count>
     - <topic_id>: <status>; confidence=<confidence>; unresolved_questions=<count>

     Research progress:

     - Topics complete: <topic_complete>/<topic_total>
     - Topics needing follow-up: <topic_needs_followup>
     - Topics pending: <topic_pending>
     - Passes complete: <pass_complete>
     - Passes pending: <pass_pending>
     - Next pass: <next_pass_id or "none">

     Start a new chat and say "cadence, continue research".
     ```

   - If `complete` returns `research_complete=true` and route advances to planner, respond exactly:

     ```text
     Pass recorded:

     - Pass ID: <pass_id>
     - Pass summary: <pass_summary>

     Research progress:

     - Topics complete: <topic_complete>/<topic_total>
     - Topics needing follow-up: <topic_needs_followup>
     - Topics pending: <topic_pending>
     - Passes complete: <pass_complete>
     - Passes pending: <pass_pending>

     Start a new chat and say "cadence, plan my project".
     ```

   - If `complete` returns `research_complete=true` and workflow is complete, respond exactly:

     ```text
     Pass recorded:

     - Pass ID: <pass_id>
     - Pass summary: <pass_summary>

     Research progress:

     - Topics complete: <topic_complete>/<topic_total>
     - Topics needing follow-up: <topic_needs_followup>
     - Topics pending: <topic_pending>
     - Passes complete: <pass_complete>
     - Passes pending: <pass_pending>

     Research and currently tracked workflow items are complete.
     ```

   - If `start` returns `research_complete=true`, do not run a pass; respond exactly:

     ```text
     Research progress:
     
     - Topics complete: <topic_complete>/<topic_total>
     - Topics needing follow-up: <topic_needs_followup>
     - Topics pending: <topic_pending>
     - Passes complete: <pass_complete>
     - Passes pending: <pass_pending>

     Research is already complete.
     ```

11. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope researcher --checkpoint research-pass-recorded --paths .`.
12. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
13. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
14. Surface script failures verbatim and do not expose internal command traces unless explicitly requested.
15. For successful runs, do not add extra prose before or after the strict templates in this file.
