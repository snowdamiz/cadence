---
name: scaffold
description: Initialize Cadence project scaffolding for first-time setup. Use when the target project root does not yet contain a .cadence directory and Cadence must create initial state files before other workflow gates run.
---

# Scaffold

1. Resolve project root by running `python3 ../../scripts/resolve-project-root.py` and store stdout in `PROJECT_ROOT`.
2. Run `python3 ../../scripts/run-scaffold-gate.py --project-root "$PROJECT_ROOT"` (resolve this relative path from this sub-skill directory) and parse the JSON response.
3. `run-scaffold-gate.py` performs workflow route assertion internally; if it errors, stop and surface the exact error to the user.
4. Resolve helper scripts dir by running `python3 ../../scripts/resolve-project-scripts-dir.py --project-root "$PROJECT_ROOT"` and store stdout in `CADENCE_SCRIPTS_DIR`.
5. Run `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and parse the JSON output. Treat `repo_enabled` as the authoritative push mode (`false` means local-only commits).
6. If `repo_enabled` is false, ask the user: `No GitHub remote is configured yet. Do you want to initialize a GitHub repo now? (yes/no)`.
7. If the user answers yes:
   - If `git_initialized` is false, run `cd "$PROJECT_ROOT" && git init`.
   - Ask for repo name and visibility, then run `cd "$PROJECT_ROOT" && gh repo create <name> --source . --remote origin --<public|private>`.
   - Rerun `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and verify `repo_enabled` is true.
   - If repo setup still fails, stop and surface the exact failure to the user.
8. If the user answers no:
   - If `git_initialized` is false, run `cd "$PROJECT_ROOT" && git init` so local commits can be stored.
   - Keep local-only mode (`state.repo-enabled=false`) and continue until the user configures a GitHub repo later.
9. Ask the user: `Do you want .cadence tracked in git history? (yes/no)`.
10. If the user answers yes:
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/configure-cadence-gitignore.py" --mode track`.
   - At end of this skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope scaffold --checkpoint cadence-tracked --paths .`.
11. If the user answers no:
   - Run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/configure-cadence-gitignore.py" --mode ignore`.
   - At end of this skill conversation, run `cd "$PROJECT_ROOT" && python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope scaffold --checkpoint cadence-ignored --paths .`.
12. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
13. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
14. Execute scaffold actions serially. Do not run this flow in parallel with other setup gates.
15. In user-facing replies, summarize only the result. Do not expose internal command lines, skill chains, or execution traces unless explicitly requested.
