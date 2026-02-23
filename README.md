# Cadence Skill Installer

Install this repository's `skill/` contents into one or more AI tool skill paths (`.../skills/cadence/`) using `npx`.

## Run

```bash
npx cadence-skill-installer
```

The installer shows a multi-select prompt (comma-separated choices) so you can install into multiple tools in one run.
If a selected tool already has Cadence installed, the installer prints an update notice and warns that files will be overwritten.
In TTY terminals, selection is a real interactive TUI: use arrow keys (or `j`/`k`) to move, `space` to toggle, `a` to toggle all, and `enter` to confirm.

## Non-interactive examples

```bash
# Install to all supported tools
npx cadence-skill-installer --all --yes

# Install to specific tools
npx cadence-skill-installer --tools codex,claude,gemini --yes
```

## Supported tool keys

- `codex`
- `agents`
- `claude`
- `gemini`
- `copilot`
- `github-copilot`
- `windsurf`
- `opencode`

## CI/CD Trusted Publishing (recommended)

This repo includes `/Users/sn0w/Documents/dev/cadence/.github/workflows/publish.yml` for npm trusted publishing (OIDC).

1. Push this repo to GitHub.
2. In npm package settings for `cadence-skill-installer`, add a Trusted Publisher:
   - Provider: GitHub Actions
   - Repository: your owner/repo
   - Workflow file: `.github/workflows/publish.yml`
   - Environment: leave empty unless you use one
3. Trigger the workflow manually (`workflow_dispatch`) or push a tag like `v0.1.0`.

No `NPM_TOKEN` secret is required in GitHub Actions when trusted publishing is configured.
