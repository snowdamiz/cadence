---
name: prerequisite-gate
description: Run and persist Cadence prerequisite checks for Python availability. Use when Cadence starts work after scaffolding and must confirm prerequisites before lifecycle or delivery commands.
---

# Prerequisite Gate

1. Run this only after scaffold routing from `skills/scaffold/SKILL.md`.
2. Run `python3 ../../scripts/run-prerequisite-gate.py` (resolve this relative path from this sub-skill directory).
3. If the script reports `MISSING_PYTHON3`, stop and ask the user for confirmation to install prerequisites.
4. Do not continue Cadence lifecycle or delivery execution while prerequisites are missing.
5. At end of this successful skill conversation, run `python3 ../../scripts/finalize-skill-checkpoint.py --scope prerequisite-gate --checkpoint prerequisites-passed --paths .`.
6. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
7. Surface script failures verbatim instead of adding custom fallback logic.
8. In normal user-facing updates, share the prerequisite outcome without raw command traces or internal routing details unless explicitly requested.
