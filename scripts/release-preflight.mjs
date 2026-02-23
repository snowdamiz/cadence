import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { cleanPythonArtifacts } from "./clean-python-artifacts.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

function runGit(args) {
  const result = spawnSync("git", args, {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });

  if (result.status !== 0) {
    const stderr = (result.stderr || "").trim();
    throw new Error(stderr || `git ${args.join(" ")} failed`);
  }
  return (result.stdout || "").trim();
}

function failWithDirtyTree(statusOutput) {
  const lines = statusOutput.split("\n").filter(Boolean);
  console.error("Release preflight failed: working tree is not clean.");
  console.error("Commit or stash changes before running a release bump.");
  console.error("Pending changes:");
  for (const line of lines) {
    console.error(`- ${line}`);
  }
  process.exit(1);
}

const removed = await cleanPythonArtifacts();
if (removed.length > 0) {
  console.log(`Cleaned ${removed.length} generated artifact(s) before release.`);
}

runGit(["rev-parse", "--show-toplevel"]);
const statusOutput = runGit(["status", "--porcelain"]);
if (statusOutput) {
  failWithDirtyTree(statusOutput);
}

console.log("Release preflight passed: working tree is clean.");
