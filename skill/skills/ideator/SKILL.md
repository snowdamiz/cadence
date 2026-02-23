---
name: ideator
description: Guide users from a rough concept to a fully defined project idea through adaptive, one-question-at-a-time discovery. Use when users want to shape or refine what they want to build, write, or create across any domain, then persist final ideation into .cadence/cadence.json.
---

# Ideator

1. Keep user-facing responses focused on ideation content. Do not expose internal skill-routing, command output, or execution traces unless the user explicitly asks.
2. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --require-cadence` and store stdout in `PROJECT_ROOT`.
3. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
4. Run `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and parse the JSON output. Treat `repo_enabled` as the authoritative push mode (`false` means local-only commits).
5. Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/assert-workflow-route.py" --skill-name ideator --project-root "$PROJECT_ROOT"` and parse the JSON response.
6. If route assertion fails, stop and surface the exact error to the user.
7. Run steps 2-6 once when entering this ideator conversation. Do not rerun those gate commands between normal ideation Q/A turns.
8. Start from the user's input and briefly restate your understanding.
9. Accept two input modes:
   - Conversational discovery from a rough idea.
   - Project brief or project document provided up front.
10. If the user provides a project brief or document:
   - Extract the explicit requirements into a working ideation object.
   - Judge whether the brief is execution-ready across the relevant dimensions below.
   - If information is sufficient, present the final ideation summary and ask for confirmation.
   - If information is missing or ambiguous, ask exactly one highest-leverage follow-up question.
11. Ask exactly one question at a time. Never ask a batch of questions in a single turn.
12. After each user answer:
   - Summarize what changed in one short sentence.
   - Decide the next highest-leverage unknown.
   - Ask one natural follow-up question.
13. Keep discovery domain-agnostic and adaptive:
   - Derive the question path from the user's domain, any provided document, and prior answers.
   - Do not force fixed templates or hard-coded checklists during discovery.
   - Drill deep where ambiguity remains; move on when the topic is clear.
14. Build understanding until the idea is execution-ready. Cover the relevant dimensions for the domain, including:
   - objective and core outcome
   - target audience or user
   - core experience or structure (for example mechanics, flow, chapters, systems)
   - scope boundaries (in-scope vs out-of-scope)
   - implementation approach (for example tools, tech stack, process, platforms)
   - delivery shape (milestones, sequencing, constraints, risks, success signals)
   - assume execution is AI-driven by default; if timeline expectations are discussed, calibrate estimates to roughly 10-100x faster than human-only delivery.
   - do not force timeline-specific prompts just to apply this assumption.
15. Build a complete later-phase research agenda from the ideation conversation:
   - Infer all relevant research topics that should be explored in later phases.
   - Keep the agenda domain-agnostic and driven by what the user discussed.
   - Group topics into coherent `research_agenda.blocks`.
   - Track concrete entities (for example technologies, methods, standards, regulations, tools, audiences, channels) in `research_agenda.entity_registry`.
   - Ensure entity relationships are block-consistent: if a topic references an entity, that topic must be in the entity's owner block.
16. Do not hard-code assumptions. If you infer something, label it explicitly and ask for confirmation.
17. When coverage is deep enough, present a final ideation summary and ask for confirmation.
18. Use this canonical ideation payload contract and do not inspect Cadence scripts to infer shape during normal operation:
   - Payload root must be a JSON object representing the full `ideation` object.
   - Include execution-ready core fields from discovery. Preferred keys:
     - `objective` (string)
     - `core_outcome` (string)
     - `target_audience` (string or array)
     - `core_experience` (string, array, or object)
     - `in_scope` (array)
     - `out_of_scope` (array)
     - `implementation_approach` (object or array)
     - `milestones` (array)
     - `constraints` (array)
     - `risks` (array)
     - `success_signals` (array)
     - `assumptions` (array, optional)
   - `research_agenda` is required and must include:
     - `blocks` (array with at least one topic total for ideator completion)
     - `entity_registry` (array)
     - `topic_index` (object, set to `{}` in payload; it is rebuilt during normalization)
   - Each `research_agenda.blocks[]` item should include `block_id`, `title`, `rationale`, `tags`, and `topics`.
   - Each `topics[]` item should include `topic_id`, `title`, `category`, `priority` (`low|medium|high`), `why_it_matters`, `research_questions`, `keywords`, `tags`, and `related_entities`.
   - Each `entity_registry[]` item should include `entity_id`, `label`, `kind`, `aliases`, and `owner_block_id`.
   - Relationship rule: every id listed in topic `related_entities` must exist in `entity_registry`, and that entity's `owner_block_id` must match the topic's block.
19. After confirmation, rerun route assertion once before persistence:
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/assert-workflow-route.py" --skill-name ideator --project-root "$PROJECT_ROOT"`.
   - If assertion fails, stop and surface the exact error.
20. After confirmation, persist ideation programmatically:
   - Create a JSON payload file at `"$PROJECT_ROOT/.cadence/ideation_payload.json"`.
   - Write the full finalized ideation object to that file using the contract above.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/prepare-ideation-research.py" --file "$PROJECT_ROOT/.cadence/ideation_payload.json"`.
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file "$PROJECT_ROOT/.cadence/ideation_payload.json" --completion-state complete` (this injects ideation and deletes the payload file on success).
21. Verify persistence by running `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/get-ideation.py"`.
22. Mention that granular research queries are available via `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/query-ideation-research.py"`.
23. Mention that research execution runs in a separate `researcher` phase.
24. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope ideator --checkpoint ideation-completed --paths .`.
25. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
26. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
27. If the user requests revisions later, regenerate the payload, rerun `prepare-ideation-research.py`, and rerun `inject-ideation.py` from `PROJECT_ROOT`.
