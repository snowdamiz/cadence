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

RUN_PROJECT_OVERVIEW_SCRIPT = SCRIPTS_DIR / "run-project-overview.py"


def build_state_with_progress() -> dict:
    data = default_data()
    state = data.setdefault("state", {})
    state["project-mode"] = "greenfield"
    state["ideation-completed"] = False
    state["research-completed"] = False

    for task_id in (
        "task-scaffold",
        "task-prerequisite-gate",
        "task-brownfield-intake",
    ):
        data, found = set_workflow_item_status(
            data,
            item_id=task_id,
            status="complete",
            cadence_dir_exists=True,
        )
        if not found:
            raise RuntimeError(f"Missing workflow item in fixture: {task_id}")

    ideation = data.setdefault("ideation", {})
    ideation["objective"] = "Launch MVP"
    ideation["core_outcome"] = "Deliver the first production-ready release"

    data["planning"] = {
        "version": 1,
        "status": "pending",
        "detail_level": "milestone_phase_v1",
        "decomposition_pending": True,
        "created_at": "",
        "updated_at": "",
        "summary": "Initial roadmap draft.",
        "assumptions": ["2 engineers", "existing API"],
        "milestones": [
            {
                "milestone_id": "milestone-alpha",
                "title": "Alpha",
                "phases": [
                    {"phase_id": "phase-foundation", "title": "Foundation"},
                    {"phase_id": "phase-validation", "title": "Validation"},
                ],
            }
        ],
    }
    return data


def write_state(project_root: Path, state: dict) -> None:
    cadence_dir = project_root / ".cadence"
    cadence_dir.mkdir(parents=True, exist_ok=True)
    cadence_json = cadence_dir / "cadence.json"
    cadence_json.write_text(json.dumps(state, indent=4) + "\n", encoding="utf-8")


class RunProjectOverviewTests(unittest.TestCase):
    def test_returns_full_roadmap_rows_and_current_position(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(project_root, build_state_with_progress())

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_PROJECT_OVERVIEW_SCRIPT),
                    "--project-root",
                    str(project_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload.get("status"), "ok")
            self.assertEqual(payload.get("action"), "overview")
            self.assertEqual(payload["project_summary"]["project_mode"], "greenfield")

            rows = payload.get("roadmap_rows", [])
            self.assertGreaterEqual(len(rows), 1)
            self.assertTrue(all("milestone" in row and "phase" in row and "wave" in row and "task" in row for row in rows))

            current_rows = [row for row in rows if row.get("is_current")]
            self.assertEqual(len(current_rows), 1)
            self.assertEqual(payload["current_position"]["task_id"], current_rows[0]["task_id"])

            level_rows = payload.get("roadmap_level_summary", [])
            level_map = {row.get("level"): row for row in level_rows if isinstance(row, dict)}
            self.assertIn("milestone", level_map)
            self.assertIn("phase", level_map)
            self.assertIn("wave", level_map)
            self.assertIn("task", level_map)
            self.assertGreater(level_map["task"]["total"], 0)

            planning_outline = payload.get("planning_outline", [])
            self.assertEqual(len(planning_outline), 1)
            self.assertEqual(planning_outline[0]["milestone_title"], "Alpha")
            self.assertIn("Foundation", planning_outline[0]["phase_names"])

    def test_reports_workflow_complete_position(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            data = build_state_with_progress()

            for task_id in (
                "task-ideation",
                "task-research",
                "task-roadmap-planning",
            ):
                data, found = set_workflow_item_status(
                    data,
                    item_id=task_id,
                    status="complete",
                    cadence_dir_exists=True,
                )
                if not found:
                    raise RuntimeError(f"Missing workflow item in fixture: {task_id}")

            write_state(project_root, data)

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_PROJECT_OVERVIEW_SCRIPT),
                    "--project-root",
                    str(project_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["current_position"]["task_id"], "complete")
            self.assertEqual(payload["current_position"]["task"], "Workflow Complete")


if __name__ == "__main__":
    unittest.main()
