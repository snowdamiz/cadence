---
name: ideator
description: Guide users from a rough concept to a fully defined project idea through adaptive, one-question-at-a-time discovery. Use when users want to shape or refine what they want to build, write, or create across any domain, then persist final ideation into .cadence/cadence.json.
---

# Ideator

1. Keep user-facing responses focused on ideation content. Do not expose internal skill-routing, command output, or execution traces unless the user explicitly asks.
2. Start from the user's input and briefly restate your understanding.
3. Accept two input modes:
   - Conversational discovery from a rough idea.
   - Project brief or project document provided up front.
4. If the user provides a project brief or document:
   - Extract the explicit requirements into a working ideation object.
   - Judge whether the brief is execution-ready across the relevant dimensions below.
   - If information is sufficient, present the final ideation summary and ask for confirmation.
   - If information is missing or ambiguous, ask exactly one highest-leverage follow-up question.
5. Ask exactly one question at a time. Never ask a batch of questions in a single turn.
6. After each user answer:
   - Summarize what changed in one short sentence.
   - Decide the next highest-leverage unknown.
   - Ask one natural follow-up question.
7. Keep discovery domain-agnostic and adaptive:
   - Derive the question path from the user's domain, any provided document, and prior answers.
   - Do not force fixed templates or hard-coded checklists during discovery.
   - Drill deep where ambiguity remains; move on when the topic is clear.
8. Build understanding until the idea is execution-ready. Cover the relevant dimensions for the domain, including:
   - objective and core outcome
   - target audience or user
   - core experience or structure (for example mechanics, flow, chapters, systems)
   - scope boundaries (in-scope vs out-of-scope)
   - implementation approach (for example tools, tech stack, process, platforms)
   - delivery shape (milestones, sequencing, constraints, risks, success signals)
9. Do not hard-code assumptions. If you infer something, label it explicitly and ask for confirmation.
10. When coverage is deep enough, present a final ideation summary and ask for confirmation.
11. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py` and store stdout in `CADENCE_SCRIPTS_DIR`.
12. After confirmation, persist ideation programmatically:
   - Create a JSON payload file at `.cadence/ideation_payload.json`.
   - Write the full finalized ideation object to that file.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/inject-ideation.py" --file .cadence/ideation_payload.json --completion-state complete` (this injects ideation and deletes `.cadence/ideation_payload.json` on success).
13. Verify persistence by running `python3 "$CADENCE_SCRIPTS_DIR/get-ideation.py"`.
14. At end of this successful skill conversation, run `python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope ideator --checkpoint ideation-completed --paths .`.
15. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
16. If the user requests revisions later, regenerate the payload and rerun `inject-ideation.py`.
