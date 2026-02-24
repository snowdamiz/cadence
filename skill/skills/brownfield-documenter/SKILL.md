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
7. During normal brownfield documentation, do not read Cadence script source files (for example `run-brownfield-documentation.py`, `ideation_research.py`, `get-ideation.py`) to infer schema or workflow details. Only inspect Cadence internals if the user explicitly asks to debug Cadence itself.
8. Perform AI-led deep investigation of the existing project using repository evidence:
   - inspect key docs and manifests
   - inspect runtime entrypoints and major code paths
   - inspect test surfaces, tooling, CI, and deployment configuration when present
   - infer objective, core outcome, scope boundaries, constraints, and risks from evidence
9. Use this canonical ideation payload contract and do not inspect Cadence Python scripts to infer schema during normal operation:
   - Payload root must be a JSON object representing the full `ideation` object.
   - `research_agenda` is required for brownfield completion.
   - Non-research planning fields are optional in brownfield documentation and must be evidence-backed or user-confirmed.
   - Do not invent unknown planning details. If information is missing, ask one focused clarification question or omit the field and record uncertainty in optional `assumptions` / `open_questions`.
10. Build the brownfield payload with these rules:
   - Preferred optional top-level fields when available: `objective`, `core_outcome`, `target_audience`, `core_experience`, `risks`, `success_signals`, `assumptions`, `open_questions`.
   - Optional planning fields: `in_scope`, `out_of_scope`, `implementation_approach`, `milestones`, `constraints`.
   - Required `research_agenda` keys:
     - `blocks` (array; must contain at least one topic total for completion)
     - `entity_registry` (array; can be empty)
     - `topic_index` (object; set `{}` in payload, rebuilt during normalization)
   - Each `research_agenda.blocks[]` item should include:
     - `block_id`, `title`, `rationale`, `tags`, `topics`
   - Each `topics[]` item should include:
     - `topic_id`, `title`, `category`, `priority` (`low|medium|high`), `why_it_matters`, `research_questions`, `keywords`, `tags`, `related_entities`
   - Each `entity_registry[]` item should include:
     - `entity_id`, `label`, `kind`, `aliases`, `owner_block_id`
   - Relationship rule:
     - every id listed in topic `related_entities` must exist in `entity_registry`, and that entity's `owner_block_id` must match the topic block.
11. Sparse payloads are allowed as long as `research_agenda` has at least one topic:
   - missing topic `category` defaults to `general`
   - missing topic `priority` defaults to `medium`
   - missing list fields default to `[]`
   - empty `entity_registry` is valid
12. Persist finalized ideation without creating extra project files:
   - pipe payload JSON directly to stdin and run:
   - `python3 "$CADENCE_SCRIPTS_DIR/run-brownfield-documentation.py" --project-root "$PROJECT_ROOT" complete --stdin`
13. Verify persistence by running:
   - `python3 "$CADENCE_SCRIPTS_DIR/get-ideation.py" --project-root "$PROJECT_ROOT"`
14. Mention that granular research queries are available via:
   - `python3 "$CADENCE_SCRIPTS_DIR/query-ideation-research.py" --project-root "$PROJECT_ROOT"`
15. End successful completion replies with this exact line:
   - `Start a new chat with a new agent and say "plan my project".`
16. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope brownfield-documenter --checkpoint documentation-captured --paths .`.
17. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
18. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
19. In normal user-facing updates, report brownfield findings and persisted ideation outcomes without raw command traces or internal routing details unless explicitly requested.
