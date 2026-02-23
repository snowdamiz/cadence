---
name: researcher
description: Execute ideation research agenda topics through dynamic multi-pass web research with strict context control. Use when Cadence route points to researcher and ideation is complete, especially when many topics require multiple passes and per-pass handoff resets.
---

# Researcher

1. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --require-cadence` and store stdout in `PROJECT_ROOT`.
2. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
3. Run `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and parse the JSON output. Treat `repo_enabled` as the authoritative push mode (`false` means local-only commits).
4. Run `python3 "$CADENCE_SCRIPTS_DIR/assert-workflow-route.py" --skill-name researcher --project-root "$PROJECT_ROOT"` and parse the JSON response.
5. If route assertion fails, stop and surface the exact error to the user.
6. Start exactly one research pass for this conversation by running `python3 "$CADENCE_SCRIPTS_DIR/run-research-pass.py" --project-root "$PROJECT_ROOT" start --ack-handoff` and parse the JSON output.
7. If start output returns `research_complete=true`, report that all research topics are complete and skip pass execution.
8. If start output returns a `pass`, research only the topics listed in that pass:
   - Use web browsing for current, source-backed information.
   - Keep scope limited to the pass topics; do not expand into other pending topics.
   - Capture concise findings and source links per topic.
9. Build a pass result JSON payload in-memory with this shape:
   - `pass_summary` (string)
   - `topics` (array)
   - Each `topics[]` item must include:
     - `topic_id` (string, must be in current pass topic_ids)
     - `status` (`complete` or `needs_followup`)
     - `summary` (string)
     - `confidence` (`low|medium|high`)
     - `unresolved_questions` (array of strings)
     - `sources` (array of objects with at least `url`; optional: `title`, `publisher`, `published_at`, `notes`)
10. Complete the pass without writing any extra state files by piping payload JSON to:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-research-pass.py" --project-root "$PROJECT_ROOT" complete --pass-id "<pass_id_from_start_output>" --stdin`
11. Never start a second pass in the same conversation.
12. If complete output returns `handoff_required=true`, end with this exact handoff line and stop: `Start a new chat and say "continue research".`
13. If complete output returns `research_complete=true`, report that research phase is complete.
14. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope researcher --checkpoint research-pass-recorded --paths .`.
15. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
16. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
17. Surface script failures verbatim and do not expose internal command traces unless explicitly requested.
