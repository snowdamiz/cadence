---
name: scaffold
description: Initialize Cadence project scaffolding for first-time setup. Use when the target project root does not yet contain a .cadence directory and Cadence must create initial state files before other workflow gates run.
---

# Scaffold

1. Resolve project root by running `python3 ../../scripts/resolve-project-root.py` and store stdout in `PROJECT_ROOT`.
2. Run `python3 ../../scripts/assert-workflow-route.py --skill-name scaffold --project-root "$PROJECT_ROOT"` and parse the JSON response.
3. If route assertion fails, stop and surface the exact error to the user.
4. Run `python3 ../../scripts/run-scaffold-gate.py --project-root "$PROJECT_ROOT"` (resolve this relative path from this sub-skill directory) and parse the JSON response.
5. If the script errors, stop and surface the exact error to the user.
6. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
7. Run `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and parse the JSON output. Treat `repo_enabled` as the authoritative push mode (`false` means local-only commits).
8. If `repo_enabled` is false, ask the user: `No GitHub remote is configured yet. Do you want to initialize a GitHub repo now? (yes/no)`.
9. If the user answers yes:
   - If `git_initialized` is false, run `cd "$PROJECT_ROOT" && git init`.
   - Ask for repo name and visibility, then run `cd "$PROJECT_ROOT" && gh repo create <name> --source . --remote origin --<public|private>`.
   - Rerun `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and verify `repo_enabled` is true.
   - If repo setup still fails, stop and surface the exact failure to the user.
10. If the user answers no:
   - If `git_initialized` is false, run `cd "$PROJECT_ROOT" && git init` so local commits can be stored.
   - Run `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT" --set-local-only` to persist `state.repo-enabled=false`.
   - Continue in local-only commit mode until the user configures a GitHub repo later.
11. Ask the user: `Do you want .cadence tracked in git history? (yes/no)`.
12. If the user answers yes:
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/configure-cadence-gitignore.py" --mode track`.
   - At end of this skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope scaffold --checkpoint cadence-tracked --paths .`.
13. If the user answers no:
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/configure-cadence-gitignore.py" --mode ignore`.
   - At end of this skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope scaffold --checkpoint cadence-ignored --paths .`.
14. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
15. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
16. Execute scaffold actions serially. Do not run this flow in parallel with other setup gates.
17. In user-facing replies, summarize only the result. Do not expose internal command lines, skill chains, or execution traces unless explicitly requested.
