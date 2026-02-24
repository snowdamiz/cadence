---
name: ideator
description: Guide users from a rough concept to a fully defined project idea through adaptive, one-question-at-a-time discovery. Use when users want to shape or refine what they want to build, write, or create across any domain, then persist final ideation into .cadence/cadence.json.
---

# Ideator

1. Keep user-facing responses focused on ideation content. Do not expose internal skill-routing, command output, or execution traces unless the user explicitly asks.
   - Never manually edit `.cadence/cadence.json`; all Cadence state writes must go through Cadence scripts.
2. Run shared skill entry gates once at conversation start:
   - `python3 ../../scripts/run-skill-entry-gate.py --require-cadence --assert-skill-name ideator`
   - Parse JSON and store `PROJECT_ROOT` from `project_root`, `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
   - If route assertion fails, stop and surface the exact error to the user.
3. Do not rerun entry gates between normal ideation Q/A turns in the same conversation.
4. Start from the user's input and briefly restate your understanding.
5. Accept two input modes:
   - Conversational discovery from a rough idea.
   - Project brief or project document provided up front.
6. If the user provides a project brief or document:
   - Extract the explicit requirements into a working ideation object.
   - Judge whether the brief is execution-ready across the relevant dimensions below.
   - If information is sufficient, present the final ideation summary and ask for confirmation.
   - If information is missing or ambiguous, ask exactly one highest-leverage follow-up question.
7. Ask exactly one question at a time. Never ask a batch of questions in a single turn.
8. After each user answer:
   - Summarize what changed in one short sentence.
   - Decide the next highest-leverage unknown.
   - Ask one natural follow-up question.
9. Keep discovery domain-agnostic and adaptive:
   - Derive the question path from the user's domain, any provided document, and prior answers.
   - Do not force fixed templates or hard-coded checklists during discovery.
   - Drill deep where ambiguity remains; move on when the topic is clear.
10. Build understanding until the idea is execution-ready. Cover the relevant dimensions for the domain, including:
   - objective and core outcome
   - target audience or user
   - core experience or structure (for example mechanics, flow, chapters, systems)
   - scope boundaries (in-scope vs out-of-scope)
   - implementation approach (for example tools, tech stack, process, platforms)
   - delivery shape (milestones, sequencing, constraints, risks, success signals)
   - assume execution is AI-driven by default; if timeline expectations are discussed, calibrate estimates to roughly 10-100x faster than human-only delivery.
   - do not force timeline-specific prompts just to apply this assumption.
11. Build a complete later-phase research agenda from the ideation conversation:
   - Infer all relevant research topics that should be explored in later phases.
   - Keep the agenda domain-agnostic and driven by what the user discussed.
   - Group topics into coherent `research_agenda.blocks`.
   - Track concrete entities (for example technologies, methods, standards, regulations, tools, audiences, channels) in `research_agenda.entity_registry`.
   - Ensure entity relationships are block-consistent: if a topic references an entity, that topic must be in the entity's owner block.
12. Do not hard-code assumptions. If you infer something, label it explicitly and ask for confirmation.
13. When coverage is deep enough, present a final ideation summary and ask for confirmation.
14. Use this canonical ideation payload contract and do not inspect Cadence scripts to infer shape during normal operation:
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
15. After confirmation, rerun route assertion once before persistence:
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/assert-workflow-route.py" --skill-name ideator --project-root "$PROJECT_ROOT"`.
   - If assertion fails, stop and surface the exact error.
16. After confirmation, persist ideation programmatically:
   - Create a JSON payload file at `"$PROJECT_ROOT/.cadence/ideation_payload.json"`.
   - Write the full finalized ideation object to that file using the contract above.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/prepare-ideation-research.py" --file "$PROJECT_ROOT/.cadence/ideation_payload.json"`.
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file "$PROJECT_ROOT/.cadence/ideation_payload.json" --completion-state complete` (this injects ideation and deletes the payload file on success).
17. Verify persistence by running `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/get-ideation.py"`.
18. Mention that granular research queries are available via `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/query-ideation-research.py"`.
19. Mention that research execution runs in a separate `researcher` phase.
20. End successful ideation completion replies with this exact line: `Start a new chat with a new agent and say "plan my project".`
21. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope ideator --checkpoint ideation-completed --paths .`.
22. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
23. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
24. If the user requests revisions later, regenerate the payload, rerun `prepare-ideation-research.py`, and rerun `inject-ideation.py` from `PROJECT_ROOT`.
