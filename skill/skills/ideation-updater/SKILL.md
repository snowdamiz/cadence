---
name: ideation-updater
description: Discuss, audit, and update existing project ideation in .cadence/cadence.json while preserving full-project context. Use when the user wants to add missing aspects, revise assumptions, remove scope, or explore tradeoffs within an already defined project idea.
---

# Ideation Updater

1. Invoke this skill only when user intent is to discuss or modify already-saved ideation.
2. Route first-time concept discovery to Cadence new-chat handoff: `now make a new chat and say "help me define my project" or provide a project brief.`
3. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py` and store stdout in `CADENCE_SCRIPTS_DIR`.
4. First message behavior in this skill conversation:
   - Run `python3 "$CADENCE_SCRIPTS_DIR/expose-ideation.py"` and use the JSON output as active AI context.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/render-ideation-summary.py"` and show that human-readable summary to the user.
   - Ask one intent-setting question: discussion only, add, change, or remove.
5. Run the conversation one step at a time:
   - Ask exactly one question per turn.
   - Keep the full current project idea in mind while focusing on the selected area.
   - After each user answer, restate what changed and what remains unchanged.
6. Support deep-dive updates for missing aspects:
   - If user says they forgot a topic, zoom into that topic and drill until clear.
   - Adapt topic depth to domain context (for example mechanics/systems, audience, scope boundaries, tech/process, risks, success criteria).
   - Avoid hard-coded question trees; derive next question from current context.
7. Distinguish interaction modes clearly:
   - Discussion mode: analyze options and tradeoffs, do not persist.
   - Add or modify mode: prepare a minimal patch payload and merge.
   - Remove mode: rebuild the full ideation object without removed fields and replace.
8. Before any write, present a short change plan with:
   - Fields to add
   - Fields to update
   - Fields to remove
   - Fields unchanged
9. Persist only after user confirmation.
10. For add or modify mode:
   - Write changed fields to `.cadence/ideation_payload.json`.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file .cadence/ideation_payload.json --merge --completion-state keep`.
11. For remove mode or structural rewrites:
   - Write the complete updated ideation object to `.cadence/ideation_payload.json`.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file .cadence/ideation_payload.json --completion-state keep`.
12. After persistence, confirm result by running `python3 "$CADENCE_SCRIPTS_DIR/render-ideation-summary.py"`.
13. Ask whether to continue refining another aspect or stop.
