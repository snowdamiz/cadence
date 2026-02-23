export const VERSION = '0.2.12'

export const REPO_URL = 'https://github.com/snowdamiz/cadence'
export const NPM_URL = 'https://www.npmjs.com/package/cadence-skill-installer'

export const INSTALL_COMMANDS = [
  { label: 'npx', command: 'npx cadence-skill-installer' },
  { label: 'All tools', command: 'npx cadence-skill-installer --all --yes' },
  { label: 'Select tools', command: 'npx cadence-skill-installer --tools codex,claude,gemini' },
] as const

export const TOOLS = [
  { name: 'Codex', key: 'codex' },
  { name: 'Agents', key: 'agents' },
  { name: 'Claude', key: 'claude' },
  { name: 'Gemini', key: 'gemini' },
  { name: 'Copilot', key: 'copilot' },
  { name: 'GitHub Copilot', key: 'github-copilot' },
  { name: 'Windsurf', key: 'windsurf' },
  { name: 'OpenCode', key: 'opencode' },
] as const

export const TERMINAL_LINES = [
  { prompt: true, text: 'npx cadence-skill-installer' },
  { prompt: false, text: '' },
  { prompt: false, text: '  ██████╗ █████╗ ██████╗ ███████╗███╗   ██╗ ██████╗███████╗' },
  { prompt: false, text: ' ██╔════╝██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝██╔════╝' },
  { prompt: false, text: ' ██║     ███████║██║  ██║█████╗  ██╔██╗ ██║██║     █████╗' },
  { prompt: false, text: ' ██║     ██╔══██║██║  ██║██╔══╝  ██║╚██╗██║██║     ██╔══╝' },
  { prompt: false, text: ' ╚██████╗██║  ██║██████╔╝███████╗██║ ╚████║╚██████╗███████╗' },
  { prompt: false, text: '  ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚══════╝' },
  { prompt: false, text: '' },
  { prompt: false, text: ' ✓ Installed to ~/.codex/skills/cadence' },
  { prompt: false, text: ' ✓ Installed to ~/.claude/skills/cadence' },
  { prompt: false, text: ' ✓ Installed to ~/.gemini/skills/cadence' },
  { prompt: false, text: '' },
  { prompt: false, text: ' Done — 3 tools configured.' },
] as const
