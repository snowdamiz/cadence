import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
RUN_SCRIPT = SCRIPTS_DIR / "query-ideation-research.py"


def build_ideation_payload() -> dict:
    return {
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
                            "priority": "medium",
                            "why_it_matters": "",
                            "research_questions": ["q1"],
                            "keywords": [],
                            "tags": [],
                            "related_entities": [],
                        }
                    ],
                }
            ],
            "entity_registry": [],
            "topic_index": {},
        }
    }


class QueryIdeationResearchTests(unittest.TestCase):
    def test_project_root_uses_default_cadence_state_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(
                json.dumps({"ideation": build_ideation_payload()}, indent=4) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--topic-id",
                    "topic-one",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["source_type"], "cadence")
            self.assertEqual(Path(payload["path"]).resolve(), cadence_json.resolve())
            self.assertEqual(payload["summary"]["matched_topics"], 1)
            self.assertEqual(payload["results"]["topics"][0]["topic_id"], "topic-one")

    def test_file_override_supports_raw_ideation_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload_path = Path(tmp_dir) / "ideation.json"
            payload_path.write_text(json.dumps(build_ideation_payload(), indent=4) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_SCRIPT),
                    "--file",
                    str(payload_path),
                    "--topic-id",
                    "topic-one",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["source_type"], "ideation")
            self.assertEqual(Path(payload["path"]).resolve(), payload_path.resolve())
            self.assertEqual(payload["summary"]["matched_topics"], 1)


if __name__ == "__main__":
    unittest.main()
