---
name: scaffold
description: Initialize Cadence project scaffolding for first-time setup. Use when the target project root does not yet contain a .cadence directory and Cadence must create initial state files before other workflow gates run.
---

# Scaffold

1. Run this only from the target project root.
2. Check whether `.cadence` exists.
3. If `.cadence` exists, skip all scaffold actions.
4. Resolve Cadence helper scripts directory before execution:
```bash
if [ -n "${CADENCE_SCRIPTS_DIR:-}" ] && [ -f "${CADENCE_SCRIPTS_DIR}/scaffold-project.sh" ]; then
  :
else
  CADENCE_SCRIPTS_DIR=""
  for candidate in \
    "$HOME/.codex/skills/cadence-m/skill/scripts" \
    "$HOME/.codex/skills/cadence/skill/scripts" \
    "$HOME/.agents/skills/cadence-m/skill/scripts" \
    "$HOME/.agents/skills/cadence/skill/scripts" \
    "$HOME/.claude/skills/cadence-m/skill/scripts" \
    "$HOME/.claude/skills/cadence/skill/scripts" \
    "$HOME/.gemini/skills/cadence-m/skill/scripts" \
    "$HOME/.gemini/skills/cadence/skill/scripts" \
    "$HOME/.copilot/skills/cadence-m/skill/scripts" \
    "$HOME/.copilot/skills/cadence/skill/scripts" \
    "$HOME/.config/github-copilot/skills/cadence-m/skill/scripts" \
    "$HOME/.config/github-copilot/skills/cadence/skill/scripts" \
    "$HOME/.codeium/windsurf/skills/cadence-m/skill/scripts" \
    "$HOME/.codeium/windsurf/skills/cadence/skill/scripts" \
    "$HOME/.config/opencode/skills/cadence-m/skill/scripts" \
    "$HOME/.config/opencode/skills/cadence/skill/scripts"
  do
    if [ -f "$candidate/scaffold-project.sh" ]; then
      CADENCE_SCRIPTS_DIR="$candidate"
      break
    fi
  done
fi
[ -n "$CADENCE_SCRIPTS_DIR" ] || { echo "MISSING_CADENCE_SCRIPTS_DIR"; exit 1; }
```
5. If `.cadence` does not exist, create it and seed `.cadence/cadence.json`:
```bash
bash "$CADENCE_SCRIPTS_DIR/scaffold-project.sh"
```
6. Verify `.cadence/cadence.json` exists after scaffold command completes:
```bash
test -f .cadence/cadence.json || { echo "CADENCE_JSON_MISSING"; exit 1; }
```
7. Execute scaffold and verification serially. Do not run them in parallel.
