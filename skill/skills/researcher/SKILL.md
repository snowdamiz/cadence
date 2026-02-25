---
name: researcher
description: Execute ideation research agenda topics through dynamic multi-pass web research with bounded context control. Use when Cadence route points to researcher and ideation is complete.
---

# Researcher

1. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence --assert-skill-name researcher`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
   - If route assertion fails, stop and surface the exact error to the user.
   - Never read or edit `.cadence/cadence.json` directly (including `cat`, `rg`, `jq`, or file-read tools). All Cadence state reads and writes must go through Cadence scripts.
2. Run a bounded multi-pass loop in the same conversation:
   - Start a pass with `python3 "$CADENCE_SCRIPTS_DIR/run-research-pass.py" --project-root "$PROJECT_ROOT" start --ack-handoff` and parse JSON output.
   - If start output returns `research_complete=true`, report completion and stop pass execution.
   - If start output returns a `pass`, research only that pass’s topics:
     - Use web browsing for current, source-backed information.
     - Keep scope limited to the pass topics; do not expand into other pending topics.
     - Use `pass.topics[].latest_summary` and `pass.topics[].unresolved_questions` from start output as prior-pass context.
     - If additional Cadence context is required, read only through scripts:
       - `python3 "$CADENCE_SCRIPTS_DIR/get-ideation.py" --project-root "$PROJECT_ROOT"`
       - `python3 "$CADENCE_SCRIPTS_DIR/query-ideation-research.py" --project-root "$PROJECT_ROOT" --topic-id "<topic_id>"`
   - Build pass result JSON payload with:
     - `pass_summary` (string)
     - `topics` (array)
     - Each `topics[]` includes: `topic_id`, `status` (`complete|complete_with_caveats|needs_followup`), `summary`, `confidence` (`low|medium|high`), `unresolved_questions` (array), and `sources` (objects with at least `url`).
   - Complete pass with:
     - `python3 "$CADENCE_SCRIPTS_DIR/run-research-pass.py" --project-root "$PROJECT_ROOT" complete --pass-id "<pass_id_from_start_output>" --stdin`
   - Continue looping in the same conversation while `handoff_required=false` and `research_complete=false`.
   - Stop looping when either:
     - `handoff_required=true` (context budget threshold or per-chat pass cap reached), or
     - `research_complete=true`.
3. If `research_complete=true` after completion:
   - Run `python3 "$CADENCE_SCRIPTS_DIR/read-workflow-state.py" --project-root "$PROJECT_ROOT"` and inspect `route.skill_name`.
   - If `route.skill_name` is `planner`, end with this exact line: `Start a new chat and say "plan my project".`
   - If workflow is complete, report that research and currently tracked workflow items are complete.
4. Strict user-facing return format is required for successful runs:
   - If at least one pass was completed in this conversation, respond exactly:

     ```text
     Passes recorded:

     - <pass_id>: <pass_summary>
     - <pass_id>: <pass_summary>

     Research progress:

     - Topics complete: <topic_complete>/<topic_total>
     - Topics needing follow-up: <topic_needs_followup>
     - Topics pending: <topic_pending>
     - Passes complete: <pass_complete>
     - Passes pending: <pass_pending>
     - Next pass: <next_pass_id or "none">

     Context estimate:

     - Tokens in: <context_tokens_in>
     - Tokens out: <context_tokens_out>
     - Tokens total: <context_tokens_total>
     - Context usage: <context_percent_estimate>% of <context_budget_tokens> (threshold <context_threshold_percent>%)
     ```

   - If the final `complete` output for this conversation returns `handoff_required=true`, append this exact line and stop:
     - `Start a new chat and say "cadence, continue research".`

   - If the final state for this conversation is `research_complete=true` and route advances to planner, append this exact line and stop:
     - `Start a new chat and say "cadence, plan my project".`

   - If the final state for this conversation is `research_complete=true` and workflow is complete, append this exact line:
     - `Research and currently tracked workflow items are complete.`

   - If the initial `start` call returns `research_complete=true` (no pass started), respond exactly:

     ```text
     Research progress:

     - Topics complete: <topic_complete>/<topic_total>
     - Topics needing follow-up: <topic_needs_followup>
     - Topics pending: <topic_pending>
     - Passes complete: <pass_complete>
     - Passes pending: <pass_pending>
     - Context usage: <context_percent_estimate>% of <context_budget_tokens> (threshold <context_threshold_percent>%)

     Research is already complete.
     ```

5. At end of each successful researcher conversation, run:
   - `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope researcher --checkpoint research-pass-recorded --paths .`
6. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
7. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
8. Surface script failures verbatim and do not expose internal command traces unless explicitly requested.
9. For successful runs, do not add extra prose before or after the strict templates in this file.
