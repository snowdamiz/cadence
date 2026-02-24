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

RUN_SCRIPT = SCRIPTS_DIR / "run-prerequisite-gate.py"


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


class RunPrerequisiteGateTests(unittest.TestCase):
    @staticmethod
    def write_cadence_state(project_root: Path) -> None:
        (project_root / ".cadence").mkdir(parents=True, exist_ok=True)
        (project_root / ".cadence" / "cadence.json").write_text(
            json.dumps(build_prerequisite_ready_state(), indent=4) + "\n",
            encoding="utf-8",
        )

    def test_passes_and_reports_runtime_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            self.write_cadence_state(project_root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--scripts-dir",
                    str(SCRIPTS_DIR),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertTrue(payload["prerequisites_pass"])
            self.assertEqual(payload["runtime_assets"], "ok")
            self.assertIn(payload["source"], {"fresh-check", "cache"})

    def test_fails_when_runtime_assets_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as scripts_dir:
            project_root = Path(tmp_dir)
            self.write_cadence_state(project_root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--scripts-dir",
                    scripts_dir,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING_CADENCE_RUNTIME_ASSET", result.stderr)


if __name__ == "__main__":
    unittest.main()
