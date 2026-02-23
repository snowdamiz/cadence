---
name: prerequisite-gate
description: Run and persist Cadence prerequisite checks for Python availability. Use when Cadence starts work after scaffolding and must confirm prerequisites before lifecycle or delivery commands.
---

# Prerequisite Gate

1. Run this only after scaffold routing from `skills/scaffold/SKILL.md`.
2. Run `python3 ../../scripts/run-prerequisite-gate.py` (resolve this relative path from this sub-skill directory).
3. If the script reports `MISSING_PYTHON3`, stop and ask the user for confirmation to install prerequisites.
4. Do not continue Cadence lifecycle or delivery execution while prerequisites are missing.
5. Surface script failures verbatim instead of adding custom fallback logic.
