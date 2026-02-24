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

RUN_INTAKE_SCRIPT = SCRIPTS_DIR / "run-brownfield-intake.py"


def build_intake_ready_state() -> dict:
    data = default_data()
    for task_id in ("task-scaffold", "task-prerequisite-gate"):
        data, found = set_workflow_item_status(
            data,
            item_id=task_id,
            status="complete",
            cadence_dir_exists=True,
        )
        if not found:
            raise RuntimeError(f"Missing workflow item in fixture: {task_id}")
    return data


class RunBrownfieldIntakeTests(unittest.TestCase):
    def test_auto_mode_detects_brownfield_and_persists_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            (project_root / ".cadence").mkdir(parents=True, exist_ok=True)
            cadence_json = project_root / ".cadence" / "cadence.json"
            cadence_json.write_text(json.dumps(build_intake_ready_state(), indent=4) + "\n", encoding="utf-8")
            (project_root / "src").mkdir(parents=True, exist_ok=True)
            (project_root / "src" / "main.py").write_text("print('x')\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_INTAKE_SCRIPT),
                    "--project-root",
                    str(project_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["mode"], "brownfield")
            self.assertEqual(payload["task_status"], "complete")

            updated = json.loads(cadence_json.read_text(encoding="utf-8"))
            self.assertEqual(updated["state"]["project-mode"], "brownfield")
            self.assertTrue(updated["state"]["brownfield-intake-completed"])
            self.assertEqual(updated["project-details"]["mode"], "brownfield")
            self.assertIn("brownfield_baseline", updated["project-details"])
            self.assertEqual(updated["workflow"]["next_route"]["skill_name"], "ideator")

    def test_explicit_greenfield_skips_intake_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            (project_root / ".cadence").mkdir(parents=True, exist_ok=True)
            cadence_json = project_root / ".cadence" / "cadence.json"
            cadence_json.write_text(json.dumps(build_intake_ready_state(), indent=4) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_INTAKE_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--project-mode",
                    "greenfield",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["mode"], "greenfield")
            self.assertEqual(payload["task_status"], "skipped")

            updated = json.loads(cadence_json.read_text(encoding="utf-8"))
            self.assertEqual(updated["state"]["project-mode"], "greenfield")
            self.assertEqual(updated["project-details"]["mode"], "greenfield")
            self.assertEqual(updated["project-details"]["brownfield_baseline"], {})


if __name__ == "__main__":
    unittest.main()
