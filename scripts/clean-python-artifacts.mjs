import { existsSync } from "node:fs";
import { readdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const skillRoot = path.join(repoRoot, "skill");

function isPythonArtifact(name) {
  return name.endsWith(".pyc") || name.endsWith(".pyo") || name.endsWith(".pyd");
}

async function walkAndClean(dir, removedPaths) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "__pycache__") {
        await rm(fullPath, { recursive: true, force: true });
        removedPaths.push(path.relative(repoRoot, fullPath));
        continue;
      }
      await walkAndClean(fullPath, removedPaths);
      continue;
    }

    if (entry.isFile() && isPythonArtifact(entry.name)) {
      await rm(fullPath, { force: true });
      removedPaths.push(path.relative(repoRoot, fullPath));
    }
  }
}

export async function cleanPythonArtifacts() {
  const removedPaths = [];
  const volatilePath = path.join(skillRoot, "scripts", ".last-project-root");

  if (existsSync(skillRoot)) {
    await walkAndClean(skillRoot, removedPaths);
  }

  if (existsSync(volatilePath)) {
    await rm(volatilePath, { force: true });
    removedPaths.push(path.relative(repoRoot, volatilePath));
  }

  return removedPaths.sort();
}

const isMainModule = process.argv[1] && path.resolve(process.argv[1]) === __filename;

if (isMainModule) {
  const removedPaths = await cleanPythonArtifacts();
  if (removedPaths.length === 0) {
    console.log("No Python artifacts found.");
  } else {
    console.log(`Removed ${removedPaths.length} Python artifact(s):`);
    for (const entry of removedPaths) {
      console.log(`- ${entry}`);
    }
  }
}
