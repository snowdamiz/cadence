---
name: scaffold
description: Initialize Cadence project scaffolding for first-time setup. Use when the target project root does not yet contain a .cadence directory and Cadence must create initial state files before other workflow gates run.
---

# Scaffold

1. Run this only from the target project root.
2. Run `python3 ../../scripts/run-scaffold-gate.py` (resolve this relative path from this sub-skill directory).
3. If the script reports `scaffold-skipped`, treat scaffold as already satisfied and continue.
4. If it errors, stop and surface the exact error to the user.
5. Execute scaffold gate serially. Do not run it in parallel with other setup gates.
