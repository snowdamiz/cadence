---
name: brownfield-documenter
description: Perform deep evidence-based analysis of an existing codebase and persist brownfield ideation/research structures into .cadence/cadence.json.
---

# Brownfield Documenter

1. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --require-cadence` and store stdout in `PROJECT_ROOT`.
2. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
3. Run `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and parse the JSON output. Treat `repo_enabled` as the authoritative push mode (`false` means local-only commits).
4. Run brownfield discovery context extraction:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-brownfield-documentation.py" --project-root "$PROJECT_ROOT" discover`
5. `run-brownfield-documentation.py` performs workflow route assertion internally; if assertion fails, stop and surface the exact error.
6. Treat discover output as helper context only:
   - It must not be treated as final documentation.
   - Use it to choose where to inspect deeply in the repository.
7. Perform AI-led deep investigation of the existing project using repository evidence:
   - inspect key docs and manifests
   - inspect runtime entrypoints and major code paths
   - inspect test surfaces, tooling, CI, and deployment configuration when present
   - infer objective, core outcome, scope boundaries, constraints, and risks from evidence
8. Build a finalized ideation payload using the same structure as greenfield ideation
   - payload root is full `ideation` object
   - `research_agenda` is required; non-research planning fields are optional in brownfield documentation
   - include only fields that are explicitly evidenced in the repository or confirmed by the user
   - do not invent `in_scope`, `out_of_scope`, `implementation_approach`, `milestones`, or `constraints` when evidence is missing
   - when important details are unknown, ask a focused clarification question or omit those fields and capture uncertainty in optional `assumptions` / `open_questions`
   - preferred evidence-backed core fields when available: `objective`, `core_outcome`, `target_audience`, `core_experience`, `risks`, `success_signals`
   - include required `research_agenda` with `blocks`, `entity_registry`, and `topic_index` (`topic_index` can be `{}` in payload; normalization rebuilds it)
   - each topic must include `topic_id`, `title`, `category`, `priority`, `why_it_matters`, `research_questions`, `keywords`, `tags`, `related_entities`
   - each entity must include `entity_id`, `label`, `kind`, `aliases`, `owner_block_id`
   - entity/topic relationships must remain block-consistent
9. Persist finalized ideation without creating extra project files:
   - pipe payload JSON directly to stdin and run:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-brownfield-documentation.py" --project-root "$PROJECT_ROOT" complete --stdin`
10. Verify persistence by running:
   - `python3 "$CADENCE_SCRIPTS_DIR/get-ideation.py" --project-root "$PROJECT_ROOT"`
11. Mention that granular research queries are available via:
   - `python3 "$CADENCE_SCRIPTS_DIR/query-ideation-research.py" --project-root "$PROJECT_ROOT"`
12. End successful completion replies with this exact line:
   - `Start a new chat with a new agent and say "plan my project".`
13. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope brownfield-documenter --checkpoint documentation-captured --paths .`.
14. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
15. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
16. In normal user-facing updates, report brownfield findings and persisted ideation outcomes without raw command traces or internal routing details unless explicitly requested.
