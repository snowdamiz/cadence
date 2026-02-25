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

RUN_PLANNER_SCRIPT = SCRIPTS_DIR / "run-planner.py"


def build_planner_ready_state() -> dict:
    data = default_data()
    state = data.setdefault("state", {})
    state["project-mode"] = "greenfield"

    for task_id in (
        "task-scaffold",
        "task-prerequisite-gate",
        "task-brownfield-intake",
        "task-ideation",
        "task-research",
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
    ideation["objective"] = "Ship an MVP"
    ideation["core_outcome"] = "Deliver an end-to-end first release"
    ideation["in_scope"] = ["core authentication", "dashboard"]
    ideation["out_of_scope"] = ["native mobile"]
    ideation["constraints"] = ["small team", "6-week target"]
    ideation["risks"] = ["scope creep"]
    ideation["success_signals"] = ["first 50 active users"]
    return data


class RunPlannerTests(unittest.TestCase):
    def test_discover_returns_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_planner_ready_state(), indent=4) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_PLANNER_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "discover",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload.get("status"), "ok")
            self.assertEqual(payload.get("action"), "discover")
            self.assertEqual(payload.get("mode"), "greenfield")
            self.assertIn("context", payload)
            self.assertEqual(payload["context"]["planner_payload_contract"]["detail_level"], "milestone_phase_v1")
            self.assertIn("milestone_outline", payload["context"]["existing_plan_summary"])

    def test_complete_persists_milestone_phase_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_planner_ready_state(), indent=4) + "\n", encoding="utf-8")

            planner_payload = {
                "summary": "Roadmap for MVP and launch readiness.",
                "milestones": [
                    {
                        "milestone_id": "milestone-mvp",
                        "title": "MVP",
                        "objective": "Release first usable product.",
                        "success_criteria": ["Core flows complete", "Smoke tests pass"],
                        "phases": [
                            {
                                "phase_id": "phase-foundations",
                                "title": "Foundations",
                                "objective": "Set up architecture and standards.",
                                "deliverables": ["repo setup", "baseline app shell"],
                                "exit_criteria": ["CI green"],
                            }
                        ],
                    }
                ],
            }

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_PLANNER_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "complete",
                    "--json",
                    json.dumps(planner_payload),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload.get("status"), "ok")
            self.assertEqual(payload.get("action"), "complete")
            self.assertEqual(payload["planning_summary"]["milestone_count"], 1)
            self.assertEqual(payload["planning_summary"]["phase_count"], 1)
            self.assertEqual(payload["planning_summary"]["milestone_outline"][0]["title"], "MVP")
            self.assertEqual(payload["planning_summary"]["milestone_outline"][0]["phase_titles"], ["Foundations"])

            updated = json.loads(cadence_json.read_text(encoding="utf-8"))
            self.assertEqual(updated["planning"]["detail_level"], "milestone_phase_v1")
            self.assertEqual(updated["planning"]["status"], "complete")
            self.assertEqual(updated["workflow"]["next_item"]["id"], "complete")

    def test_complete_rejects_waves_in_v1_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_planner_ready_state(), indent=4) + "\n", encoding="utf-8")

            planner_payload = {
                "summary": "Invalid payload with waves.",
                "milestones": [
                    {
                        "title": "MVP",
                        "waves": ["wave-1"],
                        "phases": [{"title": "Phase 1"}],
                    }
                ],
            }

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_PLANNER_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "complete",
                    "--json",
                    json.dumps(planner_payload),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("MILESTONE_WAVES_AND_TASKS_NOT_ALLOWED_IN_V1", result.stderr)


if __name__ == "__main__":
    unittest.main()
