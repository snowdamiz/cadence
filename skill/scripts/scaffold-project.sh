#!/usr/bin/env bash
set -euo pipefail

if [ -d ".cadence" ]; then
  echo "scaffold-skipped"
  exit 0
fi

mkdir -p ".cadence"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="${SCRIPT_DIR}/../assets/cadence.json"
TARGET_PATH=".cadence/cadence.json"

if [ -f "${TEMPLATE_PATH}" ]; then
  cp "${TEMPLATE_PATH}" "${TARGET_PATH}"
else
  cat > "${TARGET_PATH}" <<'JSON'
{
    "prerequisites-pass": false,
    "state": {
        "ideation-completed": false,
        "cadence-scripts-dir": ""
    },
    "workflow": {
        "schema_version": 2,
        "plan": [
            {
                "id": "milestone-foundation",
                "kind": "milestone",
                "title": "Foundation",
                "children": [
                    {
                        "id": "phase-project-setup",
                        "kind": "phase",
                        "title": "Project Setup",
                        "children": [
                            {
                                "id": "wave-initialize-cadence",
                                "kind": "wave",
                                "title": "Initialize Cadence",
                                "children": [
                                    {
                                        "id": "task-scaffold",
                                        "kind": "task",
                                        "title": "Scaffold project",
                                        "route": {
                                            "skill_name": "scaffold",
                                            "skill_path": "skills/scaffold/SKILL.md",
                                            "reason": "Project scaffolding has not completed yet."
                                        }
                                    },
                                    {
                                        "id": "task-prerequisite-gate",
                                        "kind": "task",
                                        "title": "Run prerequisite gate",
                                        "route": {
                                            "skill_name": "prerequisite-gate",
                                            "skill_path": "skills/prerequisite-gate/SKILL.md",
                                            "reason": "Prerequisite gate has not passed yet."
                                        }
                                    },
                                    {
                                        "id": "task-ideation",
                                        "kind": "task",
                                        "title": "Complete ideation",
                                        "route": {
                                            "skill_name": "ideator",
                                            "skill_path": "skills/ideator/SKILL.md",
                                            "reason": "Ideation has not been completed yet."
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "project-details": {},
    "ideation": {}
}
JSON
fi

echo "scaffold-created"
