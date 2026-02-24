import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ideation_research import normalize_ideation_research, reset_research_execution
from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status

RUN_RESEARCH_PASS_SCRIPT = SCRIPTS_DIR / "run-research-pass.py"


def build_cadence_state() -> dict:
    data = default_data()
    for task_id in ("task-scaffold", "task-prerequisite-gate", "task-brownfield-intake", "task-ideation"):
        data, found = set_workflow_item_status(
            data,
            item_id=task_id,
            status="complete",
            cadence_dir_exists=True,
        )
        if not found:
            raise RuntimeError(f"Missing workflow item in test fixture: {task_id}")

    ideation_payload = {
        "research_agenda": {
            "blocks": [
                {
                    "block_id": "block-a",
                    "title": "Block A",
                    "rationale": "",
                    "tags": [],
                    "topics": [
                        {
                            "topic_id": "topic-one",
                            "title": "Topic One",
                            "category": "general",
                            "priority": "high",
                            "why_it_matters": "",
                            "research_questions": ["q1"],
                            "keywords": [],
                            "tags": [],
                            "related_entities": [],
                        },
                        {
                            "topic_id": "topic-two",
                            "title": "Topic Two",
                            "category": "general",
                            "priority": "medium",
                            "why_it_matters": "",
                            "research_questions": ["q2"],
                            "keywords": [],
                            "tags": [],
                            "related_entities": [],
                        },
                    ],
                }
            ],
            "entity_registry": [],
            "topic_index": {},
        }
    }
    ideation = normalize_ideation_research(ideation_payload, require_topics=True)
    ideation = reset_research_execution(ideation)

    execution = ideation.get("research_execution", {})
    execution["pass_queue"] = [
        {
            "pass_id": "pass-r1-01",
            "round": 1,
            "status": "in_progress",
            "topic_ids": ["topic-one", "topic-two"],
            "planned_effort": 4,
            "created_at": "2026-01-01T00:00:00Z",
            "started_at": "2026-01-01T00:00:01Z",
        }
    ]
    execution["status"] = "in_progress"
    data["ideation"] = ideation
    data.setdefault("state", {})["ideation-completed"] = True
    data["state"]["research-completed"] = False
    return reconcile_workflow_state(data, cadence_dir_exists=True)


class RunResearchPassValidationTests(unittest.TestCase):
    def test_complete_requires_result_for_every_topic_in_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_cadence_state(), indent=4) + "\n", encoding="utf-8")

            payload = {
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "complete",
                        "summary": "Covered.",
                        "confidence": "high",
                        "unresolved_questions": [],
                        "sources": [],
                    }
                ]
            }

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_RESEARCH_PASS_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "complete",
                    "--pass-id",
                    "pass-r1-01",
                    "--json",
                    json.dumps(payload),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("PASS_RESULT_MISSING_TOPICS", result.stderr)
            self.assertIn("topic-two", result.stderr)


if __name__ == "__main__":
    unittest.main()
