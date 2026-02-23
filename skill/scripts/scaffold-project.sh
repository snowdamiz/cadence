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
    "project-details": {},
    "ideation": {}
}
JSON
fi

echo "scaffold-created"
