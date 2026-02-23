---
name: ideation-updater
description: Discuss, audit, and update existing project ideation in .cadence/cadence.json while preserving full-project context. Use when the user wants to add missing aspects, revise assumptions, remove scope, or explore tradeoffs within an already defined project idea.
---

# Ideation Updater

1. Keep user-facing responses focused on ideation content. Do not expose internal skill-routing, command output, or execution traces unless the user explicitly asks.
2. Invoke this skill only when user intent is to discuss or modify already-saved ideation.
3. Route first-time concept discovery to Cadence new-chat handoff: `Start a new chat and either say "help me define my project" or share your project brief.`
4. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py` and store stdout in `CADENCE_SCRIPTS_DIR`.
5. First message behavior in this skill conversation:
   - Run `python3 "$CADENCE_SCRIPTS_DIR/expose-ideation.py"` and use the JSON output as active AI context.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/render-ideation-summary.py"` and show that human-readable summary to the user.
   - Ask one intent-setting question: discussion only, add, change, or remove.
6. Run the conversation one step at a time:
   - Ask exactly one question per turn.
   - Keep the full current project idea in mind while focusing on the selected area.
   - After each user answer, restate what changed and what remains unchanged.
7. Support deep-dive updates for missing aspects:
   - If user says they forgot a topic, zoom into that topic and drill until clear.
   - Adapt topic depth to domain context (for example mechanics/systems, audience, scope boundaries, tech/process, risks, success criteria).
   - Avoid hard-coded question trees; derive next question from current context.
8. Distinguish interaction modes clearly:
   - Discussion mode: analyze options and tradeoffs, do not persist.
   - Add or modify mode: prepare a minimal patch payload and merge.
   - Remove mode: rebuild the full ideation object without removed fields and replace.
9. Before any write, present a short change plan with:
   - Fields to add
   - Fields to update
   - Fields to remove
   - Fields unchanged
10. Persist only after user confirmation.
11. For add or modify mode:
   - Write changed fields to `.cadence/ideation_payload.json`.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file .cadence/ideation_payload.json --merge --completion-state keep`.
12. For remove mode or structural rewrites:
   - Write the complete updated ideation object to `.cadence/ideation_payload.json`.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file .cadence/ideation_payload.json --completion-state keep`.
13. After persistence, confirm result by running `python3 "$CADENCE_SCRIPTS_DIR/render-ideation-summary.py"`.
14. At end of this successful skill conversation, run `python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope ideation-updater --checkpoint ideation-updated --paths .`.
15. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
16. Ask whether to continue refining another aspect or stop.
