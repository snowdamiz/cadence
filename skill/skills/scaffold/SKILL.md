---
name: scaffold
description: Initialize Cadence project scaffolding for first-time setup. Use when the target project root does not yet contain a .cadence directory and Cadence must create initial state files before other workflow gates run.
---

# Scaffold

1. Run this only from the target project root.
2. Run `python3 ../../scripts/assert-workflow-route.py --skill-name scaffold` and parse the JSON response.
3. If route assertion fails, stop and surface the exact error to the user.
4. Run `python3 ../../scripts/run-scaffold-gate.py` (resolve this relative path from this sub-skill directory) and parse the JSON response.
5. If the script errors, stop and surface the exact error to the user.
6. Run `python3 ../../scripts/check-project-repo-status.py` and parse the JSON output.
7. If `repo_enabled` is false, ask the user: `No GitHub remote is configured yet. Do you want to initialize a GitHub repo now? (yes/no)`.
8. If the user answers yes:
   - If `git_initialized` is false, run `git init`.
   - Ask for repo name and visibility, then run `gh repo create <name> --source . --remote origin --<public|private>`.
   - Rerun `python3 ../../scripts/check-project-repo-status.py` and verify `repo_enabled` is true.
   - If repo setup still fails, stop and surface the exact failure to the user.
9. If the user answers no:
   - If `git_initialized` is false, run `git init` so local commits can be stored.
   - Run `python3 ../../scripts/check-project-repo-status.py --set-local-only` to persist `state.repo-enabled=false`.
   - Continue in local-only commit mode until the user configures a GitHub repo later.
10. Ask the user: `Do you want .cadence tracked in git history? (yes/no)`.
11. If the user answers yes:
   - Run `python3 ../../scripts/configure-cadence-gitignore.py --mode track`.
   - At end of this skill conversation, run `python3 ../../scripts/finalize-skill-checkpoint.py --scope scaffold --checkpoint cadence-tracked --paths .`.
12. If the user answers no:
   - Run `python3 ../../scripts/configure-cadence-gitignore.py --mode ignore`.
   - At end of this skill conversation, run `python3 ../../scripts/finalize-skill-checkpoint.py --scope scaffold --checkpoint cadence-ignored --paths .`.
13. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
14. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
15. Execute scaffold actions serially. Do not run this flow in parallel with other setup gates.
16. In user-facing replies, summarize only the result. Do not expose internal command lines, skill chains, or execution traces unless explicitly requested.
