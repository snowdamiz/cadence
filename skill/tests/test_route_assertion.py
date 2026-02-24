import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workflow_state import default_data

ASSERT_ROUTE_SCRIPT = SCRIPTS_DIR / "assert-workflow-route.py"


class RouteAssertionTests(unittest.TestCase):
    def test_assert_route_success_and_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(default_data(), indent=4) + "\n", encoding="utf-8")

            ok = subprocess.run(
                [
                    sys.executable,
                    str(ASSERT_ROUTE_SCRIPT),
                    "--skill-name",
                    "prerequisite-gate",
                    "--project-root",
                    str(project_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(ok.returncode, 0, msg=ok.stderr or ok.stdout)
            ok_payload = json.loads(ok.stdout)
            self.assertEqual(ok_payload["status"], "ok")
            self.assertEqual(ok_payload["expected_skill"], "prerequisite-gate")

            mismatch = subprocess.run(
                [
                    sys.executable,
                    str(ASSERT_ROUTE_SCRIPT),
                    "--skill-name",
                    "ideator",
                    "--project-root",
                    str(project_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(mismatch.returncode, 2)
            self.assertIn("WORKFLOW_ROUTE_MISMATCH", mismatch.stderr)


if __name__ == "__main__":
    unittest.main()
