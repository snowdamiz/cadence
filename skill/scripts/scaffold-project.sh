#!/usr/bin/env bash
set -euo pipefail

TARGET_PATH=".cadence/cadence.json"

if [ -f "${TARGET_PATH}" ]; then
  echo "scaffold-skipped"
  exit 0
fi

mkdir -p ".cadence"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="${SCRIPT_DIR}/../assets/cadence.json"

if [ -f "${TEMPLATE_PATH}" ]; then
  cp "${TEMPLATE_PATH}" "${TARGET_PATH}"
else
  cat > "${TARGET_PATH}" <<'JSON'
{
    "prerequisites-pass": false,
    "state": {
        "ideation-completed": false,
        "research-completed": false,
        "cadence-scripts-dir": "",
        "repo-enabled": false,
        "project-mode": "unknown",
        "brownfield-intake-completed": false,
        "brownfield-documentation-completed": false
    },
    "workflow": {
        "schema_version": 6,
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
                                        "id": "task-brownfield-intake",
                                        "kind": "task",
                                        "title": "Capture project mode and baseline",
                                        "route": {
                                            "skill_name": "brownfield-intake",
                                            "skill_path": "skills/brownfield-intake/SKILL.md",
                                            "reason": "Project mode and existing codebase baseline have not been captured yet."
                                        }
                                    },
                                    {
                                        "id": "task-brownfield-documentation",
                                        "kind": "task",
                                        "title": "Document existing project context",
                                        "route": {
                                            "skill_name": "brownfield-documenter",
                                            "skill_path": "skills/brownfield-documenter/SKILL.md",
                                            "reason": "Brownfield project context has not been documented into ideation yet."
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
                                    },
                                    {
                                        "id": "task-research",
                                        "kind": "task",
                                        "title": "Research ideation agenda",
                                        "route": {
                                            "skill_name": "researcher",
                                            "skill_path": "skills/researcher/SKILL.md",
                                            "reason": "Ideation research agenda has not been completed yet."
                                        }
                                    },
                                    {
                                        "id": "task-roadmap-planning",
                                        "kind": "task",
                                        "title": "Plan project roadmap",
                                        "route": {
                                            "skill_name": "planner",
                                            "skill_path": "skills/planner/SKILL.md",
                                            "reason": "Project roadmap planning has not been completed yet."
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
    "project-details": {
        "mode": "unknown",
        "brownfield_baseline": {}
    },
    "ideation": {
        "research_agenda": {
            "version": 1,
            "summary": {
                "block_count": 0,
                "topic_count": 0,
                "entity_count": 0
            },
            "blocks": [],
            "entity_registry": [],
            "topic_index": {}
        },
        "research_execution": {
            "version": 1,
            "status": "pending",
            "planning": {
                "target_effort_per_pass": 12,
                "max_topics_per_pass": 4,
                "max_passes_per_topic": 3,
                "max_total_passes": 120,
                "max_passes_per_chat": 6,
                "context_window_tokens": 128000,
                "handoff_context_threshold_percent": 70,
                "estimated_fixed_tokens_per_chat": 12000,
                "estimated_tokens_in_overhead_per_pass": 1200,
                "estimated_tokens_out_overhead_per_pass": 400,
                "latest_round": 0
            },
            "summary": {
                "topic_total": 0,
                "topic_complete": 0,
                "topic_caveated": 0,
                "topic_needs_followup": 0,
                "topic_pending": 0,
                "pass_pending": 0,
                "pass_complete": 0,
                "next_pass_id": "",
                "context_budget_tokens": 128000,
                "context_threshold_tokens": 89600,
                "context_threshold_percent": 70,
                "context_tokens_in": 0,
                "context_tokens_out": 0,
                "context_tokens_total": 12000,
                "context_percent_estimate": 9.38,
                "context_passes_completed": 0
            },
            "topic_status": {},
            "pass_queue": [],
            "pass_history": [],
            "source_registry": [],
            "chat_context": {
                "session_index": 0,
                "passes_completed": 0,
                "estimated_tokens_fixed": 12000,
                "estimated_tokens_in": 0,
                "estimated_tokens_out": 0,
                "estimated_tokens_total": 12000,
                "estimated_context_percent": 9.38,
                "budget_tokens": 128000,
                "threshold_tokens": 89600,
                "threshold_percent": 70,
                "last_reset_at": "",
                "last_updated_at": "",
                "last_pass_id": "",
                "last_pass_tokens_in": 0,
                "last_pass_tokens_out": 0
            },
            "handoff_required": false,
            "handoff_message": "Start a new chat and say \"continue research\".",
            "handoff_reason": ""
        }
    },
    "planning": {
        "version": 1,
        "status": "pending",
        "detail_level": "",
        "decomposition_pending": true,
        "created_at": "",
        "updated_at": "",
        "summary": "",
        "assumptions": [],
        "milestones": []
    }
}
JSON
fi

echo "scaffold-created"
