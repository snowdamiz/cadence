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
  { name: 'Antigravity', key: 'antigravity' },
  { name: 'Claude', key: 'claude' },
  { name: 'Gemini', key: 'gemini' },
  { name: 'Copilot', key: 'copilot' },
  { name: 'GitHub Copilot', key: 'github-copilot' },
  { name: 'Windsurf', key: 'windsurf' },
  { name: 'OpenCode', key: 'opencode' },
] as const

export type ToolKey = (typeof TOOLS)[number]['key']

// Original ASCII banner from the installer (scripts/install-cadence-skill.mjs)
// The installer splits each line into thirds and colors: white | salmon | periwinkle
export const BANNER_LINES = [
  ' ██████╗ █████╗ ██████╗ ███████╗███╗   ██╗ ██████╗███████╗',
  '██╔════╝██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝██╔════╝',
  '██║     ███████║██║  ██║█████╗  ██╔██╗ ██║██║     █████╗  ',
  '██║     ██╔══██║██║  ██║██╔══╝  ██║╚██╗██║██║     ██╔══╝  ',
  '╚██████╗██║  ██║██████╔╝███████╗██║ ╚████║╚██████╗███████╗',
  ' ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚══════╝',
] as const

export const TERMINAL_LINES: readonly { type: 'prompt' | 'blank' | 'banner' | 'check' | 'done'; text?: string }[] = [
  { type: 'prompt', text: 'npx cadence-skill-installer' },
  { type: 'blank' },
  { type: 'banner' },
  { type: 'blank' },
  { type: 'check', text: 'Installed to ~/.codex/skills/cadence' },
  { type: 'check', text: 'Installed to ~/.claude/skills/cadence' },
  { type: 'check', text: 'Installed to ~/.gemini/skills/cadence' },
  { type: 'blank' },
  { type: 'done', text: 'Done — 3 tools configured.' },
] as const
