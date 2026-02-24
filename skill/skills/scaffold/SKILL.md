---
name: scaffold
description: Initialize Cadence project scaffolding for first-time setup. Use when the target project root does not yet contain a .cadence directory and Cadence must create initial state files before other workflow gates run.
---

# Scaffold

1. Resolve project root by running `python3 ../../scripts/resolve-project-root.py --project-root "$PWD"` and store stdout in `PROJECT_ROOT`.
   - Never manually edit `.cadence/cadence.json`; all Cadence state writes must go through Cadence scripts.
2. Run `python3 ../../scripts/run-scaffold-gate.py --project-root "$PROJECT_ROOT"` (resolve this relative path from this sub-skill directory) and parse the JSON response.
3. `run-scaffold-gate.py` performs workflow route assertion internally; if it errors, stop and surface the exact error to the user.
4. Run shared skill entry gates after scaffold initialization:
   - `python3 ../../scripts/run-skill-entry-gate.py --project-root "$PROJECT_ROOT" --require-cadence`
   - Parse JSON and store `CADENCE_SCRIPTS_DIR` from `cadence_scripts_dir`, and push mode from `repo_enabled` (`false` means local-only commits).
5. If `repo_enabled` is false, ask the user: `No qualifying git remote is configured yet. Do you want to configure one now? (yes/no)`.
6. If the user answers yes:
   - If `git_initialized` is false, run `cd "$PROJECT_ROOT" && git init`.
   - Ask whether they want GitHub auto-creation (`gh repo create`) or to provide an existing remote URL.
   - For GitHub auto-creation: ask for repo name and visibility, then run `cd "$PROJECT_ROOT" && gh repo create <name> --source . --remote origin --<public|private>`.
   - For an existing remote URL: run `cd "$PROJECT_ROOT" && git remote add origin <remote-url>` (or update remote URL if `origin` already exists).
   - Rerun `python3 "$CADENCE_SCRIPTS_DIR/check-project-repo-status.py" --project-root "$PROJECT_ROOT"` and verify `repo_enabled` is true.
   - If repo setup still fails, stop and surface the exact failure to the user.
7. If the user answers no:
   - If `git_initialized` is false, run `cd "$PROJECT_ROOT" && git init` so local commits can be stored.
   - Keep local-only mode (`state.repo-enabled=false`) and continue until the user configures a GitHub repo later.
8. Ask the user: `Do you want .cadence tracked in git history? (yes/no)`.
9. If the user answers yes:
   - Run `python3 "$CADENCE_SCRIPTS_DIR/configure-cadence-gitignore.py" --mode track --gitignore-path "$PROJECT_ROOT/.gitignore"`.
   - At end of this skill conversation, run `python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope scaffold --checkpoint cadence-tracked --paths . --project-root "$PROJECT_ROOT"`.
10. If the user answers no:
   - Run `python3 "$CADENCE_SCRIPTS_DIR/configure-cadence-gitignore.py" --mode ignore --gitignore-path "$PROJECT_ROOT/.gitignore"`.
   - At end of this skill conversation, run `python3 "$CADENCE_SCRIPTS_DIR/finalize-skill-checkpoint.py" --scope scaffold --checkpoint cadence-ignored --paths . --project-root "$PROJECT_ROOT"`.
11. Argument contract guardrail:
   - `configure-cadence-gitignore.py` accepts `--mode` and optional `--gitignore-path`; do not pass `--project-root`.
   - `finalize-skill-checkpoint.py` supports `--project-root`; always pass it explicitly.
12. If `finalize-skill-checkpoint.py` returns `status=no_changes`, continue without failure.
13. If `finalize-skill-checkpoint.py` reports an error, stop and surface it verbatim.
14. Execute scaffold actions serially. Do not run this flow in parallel with other setup gates.
15. In user-facing replies, summarize only the result. Do not expose internal command lines, skill chains, or execution traces unless explicitly requested.
