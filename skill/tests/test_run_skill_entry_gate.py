import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workflow_state import default_data, set_workflow_item_status

RUN_SCRIPT = SCRIPTS_DIR / "run-skill-entry-gate.py"


def build_prerequisite_ready_state() -> dict:
    data = default_data()
    data, found = set_workflow_item_status(
        data,
        item_id="task-scaffold",
        status="complete",
        cadence_dir_exists=True,
    )
    if not found:
        raise RuntimeError("Missing task-scaffold in workflow fixture")
    return data


class RunSkillEntryGateTests(unittest.TestCase):
    def test_returns_project_context_repo_status_and_workflow_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            (project_root / ".cadence").mkdir(parents=True, exist_ok=True)
            cadence_json = project_root / ".cadence" / "cadence.json"
            cadence_json.write_text(
                json.dumps(build_prerequisite_ready_state(), indent=4) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--require-cadence",
                    "--include-workflow-state",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(Path(payload["project_root"]).resolve(), project_root.resolve())
            self.assertTrue(payload["cadence_scripts_dir"])
            self.assertIn("repo_status", payload)
            self.assertIn("workflow_state", payload)
            self.assertFalse(payload["repo_enabled"])
            self.assertEqual(payload["workflow_state"]["route"]["skill_name"], "prerequisite-gate")

    def test_assert_skill_name_fails_on_route_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            (project_root / ".cadence").mkdir(parents=True, exist_ok=True)
            cadence_json = project_root / ".cadence" / "cadence.json"
            cadence_json.write_text(
                json.dumps(build_prerequisite_ready_state(), indent=4) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--require-cadence",
                    "--assert-skill-name",
                    "ideator",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("WORKFLOW_ROUTE_MISMATCH", result.stderr)


if __name__ == "__main__":
    unittest.main()
