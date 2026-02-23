---
name: prerequisite-gate
description: Run and persist Cadence prerequisite checks for Python availability. Use when Cadence starts work after scaffolding and must confirm prerequisites before lifecycle or delivery commands.
---

# Prerequisite Gate

1. Run this only after scaffold routing from `skills/scaffold/SKILL.md`.
2. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --require-cadence` and store stdout in `PROJECT_ROOT`.
3. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
4. Run `python3 "$CADENCE_SCRIPTS_DIR/assert-workflow-route.py" --skill-name prerequisite-gate --project-root "$PROJECT_ROOT"` and parse the JSON response.
5. If route assertion fails, stop and surface the exact error to the user.
6. Run `python3 "$CADENCE_SCRIPTS_DIR/run-prerequisite-gate.py" --project-root "$PROJECT_ROOT"`.
7. If the script reports `MISSING_PYTHON3`, stop and ask the user for confirmation to install prerequisites.
8. Do not continue Cadence lifecycle or delivery execution while prerequisites are missing.
9. At end of this successful skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope prerequisite-gate --checkpoint prerequisites-passed --paths .`.
10. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
11. Surface script failures verbatim instead of adding custom fallback logic.
12. In normal user-facing updates, share the prerequisite outcome without raw command traces or internal routing details unless explicitly requested.
