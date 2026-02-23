---
name: prerequisite-gate
description: Run and persist Cadence prerequisite checks for Python availability. Use when Cadence starts work after scaffolding and must confirm prerequisites before lifecycle or delivery commands.
---

# Prerequisite Gate

1. Run this only after scaffold routing from `skills/scaffold/SKILL.md`.
2. Resolve Cadence helper scripts directory before execution:
```bash
if [ -n "${CADENCE_SCRIPTS_DIR:-}" ] && [ -f "${CADENCE_SCRIPTS_DIR}/handle-prerequisite-state.py" ]; then
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
    if [ -f "$candidate/handle-prerequisite-state.py" ]; then
      CADENCE_SCRIPTS_DIR="$candidate"
      break
    fi
  done
fi
[ -n "$CADENCE_SCRIPTS_DIR" ] || { echo "MISSING_CADENCE_SCRIPTS_DIR"; exit 1; }
```
3. Read cached prerequisite state from `.cadence/cadence.json`:
```bash
python3 "$CADENCE_SCRIPTS_DIR/handle-prerequisite-state.py"
```
4. If the command returns `true`, return pass and skip further checks.
5. If it returns `false` or errors, run:
```bash
command -v python3 >/dev/null 2>&1 || echo "MISSING_PYTHON3"
```
6. If Python is missing, stop and ask the user for confirmation to install prerequisites.
7. Do not continue Cadence lifecycle or delivery execution while prerequisites are missing.
8. When Python is available, persist pass state:
```bash
python3 "$CADENCE_SCRIPTS_DIR/handle-prerequisite-state.py" 1
```
