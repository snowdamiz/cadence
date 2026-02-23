#!/usr/bin/env node

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import readline from "node:readline/promises";
import { fileURLToPath } from "node:url";
import { stdin as input, stdout as output } from "node:process";

const CADENCE_SKILL_NAME = "cadence";

const TOOL_TARGETS = [
  { key: "codex", label: "Codex", relPath: [".codex", "skills", CADENCE_SKILL_NAME] },
  { key: "agents", label: "Agents", relPath: [".agents", "skills", CADENCE_SKILL_NAME] },
  { key: "claude", label: "Claude", relPath: [".claude", "skills", CADENCE_SKILL_NAME] },
  { key: "gemini", label: "Gemini", relPath: [".gemini", "skills", CADENCE_SKILL_NAME] },
  { key: "copilot", label: "Copilot", relPath: [".copilot", "skills", CADENCE_SKILL_NAME] },
  {
    key: "github-copilot",
    label: "GitHub Copilot",
    relPath: [".config", "github-copilot", "skills", CADENCE_SKILL_NAME]
  },
  {
    key: "windsurf",
    label: "Codeium Windsurf",
    relPath: [".codeium", "windsurf", "skills", CADENCE_SKILL_NAME]
  },
  {
    key: "opencode",
    label: "OpenCode",
    relPath: [".config", "opencode", "skills", CADENCE_SKILL_NAME]
  }
];

const SKIP_NAMES = new Set([".DS_Store", "__pycache__"]);

function printHelp(binName) {
  const validTools = TOOL_TARGETS.map((tool) => tool.key).join(",");
  output.write(
    [
      `Usage: ${binName} [options]`,
      "",
      "Options:",
      "  --tools <comma-list>  Install to specific tools (skips interactive selection).",
      "                         Valid keys:",
      `                         ${validTools}`,
      "  --all                  Install to all supported tools.",
      "  --yes                  Skip confirmation prompt.",
      "  --home <path>          Override home directory for destination paths.",
      "  --help                 Show this message."
    ].join("\n") + "\n"
  );
}

function parseArgs(argv) {
  const parsed = {
    all: false,
    yes: false,
    tools: null,
    home: null,
    help: false
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--all") {
      parsed.all = true;
      continue;
    }
    if (arg === "--yes") {
      parsed.yes = true;
      continue;
    }
    if (arg === "--help" || arg === "-h") {
      parsed.help = true;
      continue;
    }
    if (arg === "--tools") {
      parsed.tools = argv[i + 1] ?? "";
      i += 1;
      continue;
    }
    if (arg === "--home") {
      parsed.home = argv[i + 1] ?? "";
      i += 1;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }

  if (parsed.all && parsed.tools) {
    throw new Error("Use either --all or --tools, not both.");
  }

  return parsed;
}

function resolveSourceDir() {
  const scriptPath = fileURLToPath(import.meta.url);
  const scriptDir = path.dirname(scriptPath);
  return path.resolve(scriptDir, "..", "skill");
}

async function ensureSourceDir(sourceDir) {
  let stat;
  try {
    stat = await fs.stat(sourceDir);
  } catch {
    throw new Error(`Missing skill directory: ${sourceDir}`);
  }

  if (!stat.isDirectory()) {
    throw new Error(`Expected a directory at: ${sourceDir}`);
  }
}

function buildTargets(homeDir) {
  return TOOL_TARGETS.map((tool) => ({
    ...tool,
    targetDir: path.join(homeDir, ...tool.relPath)
  }));
}

function parseToolKeyList(toolList) {
  const keys = String(toolList)
    .split(",")
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean);

  if (keys.length === 0) {
    throw new Error("No tool keys provided after --tools.");
  }

  const deduped = [...new Set(keys)];
  const unknown = deduped.filter((key) => !TOOL_TARGETS.some((tool) => tool.key === key));
  if (unknown.length > 0) {
    throw new Error(`Unknown tool keys: ${unknown.join(", ")}`);
  }

  return deduped;
}

function parseInteractiveSelection(selection, targets) {
  const raw = selection.trim().toLowerCase();
  if (!raw) {
    throw new Error("No selection received.");
  }
  if (raw === "all") {
    return targets;
  }

  const values = raw
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);

  if (values.length === 0) {
    throw new Error("No valid selection received.");
  }

  const selectedIndexes = [];
  for (const value of values) {
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 1 || parsed > targets.length) {
      throw new Error(`Invalid selection: ${value}`);
    }
    selectedIndexes.push(parsed - 1);
  }

  const uniqueIndexes = [...new Set(selectedIndexes)];
  return uniqueIndexes.map((idx) => targets[idx]);
}

async function chooseTargets(parsed, targets) {
  if (parsed.all) {
    return targets;
  }

  if (parsed.tools) {
    const selectedKeys = parseToolKeyList(parsed.tools);
    return targets.filter((target) => selectedKeys.includes(target.key));
  }

  const rl = readline.createInterface({ input, output });
  try {
    output.write("Select tools to install Cadence skill into (multi-select).\n");
    output.write("Enter numbers separated by commas, or type 'all'.\n\n");
    targets.forEach((target, idx) => {
      output.write(`${idx + 1}. ${target.label} (${target.targetDir})\n`);
    });
    const answer = await rl.question("\nSelection: ");
    return parseInteractiveSelection(answer, targets);
  } finally {
    rl.close();
  }
}

async function copyEntry(srcPath, destPath) {
  const stat = await fs.lstat(srcPath);

  if (stat.isDirectory()) {
    await fs.mkdir(destPath, { recursive: true });
    const entries = await fs.readdir(srcPath);
    for (const entry of entries) {
      if (SKIP_NAMES.has(entry)) {
        continue;
      }
      await copyEntry(path.join(srcPath, entry), path.join(destPath, entry));
    }
    return;
  }

  if (stat.isSymbolicLink()) {
    const linkTarget = await fs.readlink(srcPath);
    try {
      await fs.unlink(destPath);
    } catch {
      // Ignore if destination does not exist.
    }
    await fs.symlink(linkTarget, destPath);
    return;
  }

  await fs.mkdir(path.dirname(destPath), { recursive: true });
  await fs.copyFile(srcPath, destPath);
}

async function copySkillContents(sourceDir, targetDir) {
  await fs.mkdir(targetDir, { recursive: true });
  const entries = await fs.readdir(sourceDir);
  for (const entry of entries) {
    if (SKIP_NAMES.has(entry)) {
      continue;
    }
    await copyEntry(path.join(sourceDir, entry), path.join(targetDir, entry));
  }
}

async function confirmInstall(parsed, selectedTargets) {
  if (parsed.yes) {
    return true;
  }

  const rl = readline.createInterface({ input, output });
  try {
    output.write("\nInstall Cadence skill into:\n");
    selectedTargets.forEach((target) => output.write(`- ${target.targetDir}\n`));
    const answer = await rl.question("Continue? [y/N]: ");
    return answer.trim().toLowerCase() === "y" || answer.trim().toLowerCase() === "yes";
  } finally {
    rl.close();
  }
}

async function main() {
  const binName = path.basename(process.argv[1] || "cadence-install");
  let parsed;
  try {
    parsed = parseArgs(process.argv.slice(2));
  } catch (error) {
    output.write(`Error: ${error.message}\n\n`);
    printHelp(binName);
    process.exitCode = 1;
    return;
  }

  if (parsed.help) {
    printHelp(binName);
    return;
  }

  const homeDir = parsed.home || os.homedir();
  const sourceDir = resolveSourceDir();
  await ensureSourceDir(sourceDir);
  const targets = buildTargets(homeDir);

  let selectedTargets;
  try {
    selectedTargets = await chooseTargets(parsed, targets);
  } catch (error) {
    output.write(`Error: ${error.message}\n`);
    process.exitCode = 1;
    return;
  }

  if (selectedTargets.length === 0) {
    output.write("No tools selected. Nothing to install.\n");
    return;
  }

  const confirmed = await confirmInstall(parsed, selectedTargets);
  if (!confirmed) {
    output.write("Installation cancelled.\n");
    return;
  }

  for (const target of selectedTargets) {
    await copySkillContents(sourceDir, target.targetDir);
    output.write(`Installed to ${target.label}: ${target.targetDir}\n`);
  }

  output.write("\nCadence skill installation complete.\n");
}

main().catch((error) => {
  output.write(`Installation failed: ${error.message}\n`);
  process.exitCode = 1;
});
