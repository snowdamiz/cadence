---
name: ideation-updater
description: Discuss, audit, and update existing project ideation in .cadence/cadence.json while preserving full-project context. Use when the user wants to add missing aspects, revise assumptions, remove scope, or explore tradeoffs within an already defined project idea.
---

# Ideation Updater

1. Keep user-facing responses focused on ideation content. Do not expose internal skill-routing, command output, or execution traces unless the user explicitly asks.
2. Invoke this skill only when user intent is to discuss or modify already-saved ideation.
3. Route first-time concept discovery to Cadence new-chat handoff: `Start a new chat and either say "help me define my project" or share your project brief.`
4. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --require-cadence` and store stdout in `PROJECT_ROOT`.
5. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
6. First message behavior in this skill conversation:
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/expose-ideation.py"` and use the JSON output as active AI context.
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/render-ideation-summary.py"` and show that human-readable summary to the user.
   - Ask one intent-setting question: discussion only, add, change, or remove.
7. Run the conversation one step at a time:
   - Ask exactly one question per turn.
   - Keep the full current project idea in mind while focusing on the selected area.
   - After each user answer, restate what changed and what remains unchanged.
8. Support deep-dive updates for missing aspects:
   - If user says they forgot a topic, zoom into that topic and drill until clear.
   - Adapt topic depth to domain context (for example mechanics/systems, audience, scope boundaries, tech/process, risks, success criteria).
   - Avoid hard-coded question trees; derive next question from current context.
9. Keep `research_agenda` synchronized with ideation updates:
   - Re-infer and update research topics when scope, domain, audience, implementation approach, constraints, or risks change.
   - Keep entity ownership relationships valid: topics referencing an entity must stay in that entity's owner block.
   - Preserve untouched research blocks and entities when they remain relevant.
10. Distinguish interaction modes clearly:
   - Discussion mode: analyze options and tradeoffs, do not persist.
   - Add/modify/remove mode: build the full updated ideation object before persistence.
11. Before any write, present a short change plan with:
   - Fields to add
   - Fields to update
   - Fields to remove
   - Fields unchanged
   - Research blocks/entities/topics affected
12. Persist only after user confirmation.
13. Use this canonical ideation payload contract and do not inspect Cadence scripts to infer shape during normal operation:
   - Payload root must be a JSON object representing the full updated `ideation` object.
   - Preserve unchanged fields and update only confirmed changes; avoid dropping existing keys unless user asked to remove them.
   - Keep core ideation fields explicit where relevant, including:
     - `objective`, `core_outcome`, `target_audience`, `core_experience`
     - `in_scope`, `out_of_scope`, `implementation_approach`
     - `milestones`, `constraints`, `risks`, `success_signals`, `assumptions`
   - `research_agenda` should include:
     - `blocks` (array)
     - `entity_registry` (array)
     - `topic_index` (object, set to `{}` in payload; it is rebuilt during normalization)
   - Each block should include `block_id`, `title`, `rationale`, `tags`, and `topics`.
   - Each topic should include `topic_id`, `title`, `category`, `priority` (`low|medium|high`), `why_it_matters`, `research_questions`, `keywords`, `tags`, and `related_entities`.
   - Each entity should include `entity_id`, `label`, `kind`, `aliases`, and `owner_block_id`.
   - If `state.ideation-completed` is currently true, keep at least one research topic in `blocks` because injection with `--completion-state keep` still enforces non-empty topics.
   - Relationship rule: every id listed in topic `related_entities` must exist in `entity_registry`, and that entity's `owner_block_id` must match the topic's block.
14. For any persistence mode (add, modify, or remove):
   - Write the complete updated ideation object to `"$PROJECT_ROOT/.cadence/ideation_payload.json"` using the contract above.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/prepare-ideation-research.py" --file "$PROJECT_ROOT/.cadence/ideation_payload.json" --allow-empty`.
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file "$PROJECT_ROOT/.cadence/ideation_payload.json" --completion-state keep`.
15. After persistence, confirm result by running `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/render-ideation-summary.py"`.
16. Mention that granular research queries are available via `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/query-ideation-research.py"`.
17. Mention that ideation persistence resets research execution so researcher passes can be replanned from the updated agenda.
18. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope ideation-updater --checkpoint ideation-updated --paths .`.
19. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
20. Ask whether to continue refining another aspect or stop.
