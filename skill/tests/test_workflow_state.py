import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status


def find_item(items: list[dict], item_id: str) -> dict | None:
    for item in items:
        if item.get("id") == item_id:
            return item
        nested = find_item(item.get("children", []), item_id)
        if nested is not None:
            return nested
    return None


class WorkflowStateStatusTests(unittest.TestCase):
    def test_default_plan_includes_brownfield_phases_before_ideation(self) -> None:
        data = default_data()
        wave = find_item(data["workflow"]["plan"], "wave-initialize-cadence")
        self.assertIsNotNone(wave)

        children = wave.get("children", [])
        order = [child.get("id") for child in children if isinstance(child, dict)]
        self.assertIn("task-brownfield-intake", order)
        self.assertIn("task-brownfield-documentation", order)
        self.assertIn("task-roadmap-planning", order)
        self.assertLess(order.index("task-prerequisite-gate"), order.index("task-brownfield-intake"))
        self.assertLess(order.index("task-brownfield-intake"), order.index("task-brownfield-documentation"))
        self.assertLess(order.index("task-brownfield-documentation"), order.index("task-ideation"))
        self.assertLess(order.index("task-research"), order.index("task-roadmap-planning"))

    def test_brownfield_mode_routes_to_documenter_not_ideator(self) -> None:
        data = default_data()
        state = data.setdefault("state", {})
        state["project-mode"] = "brownfield"
        data, found = set_workflow_item_status(
            data,
            item_id="task-scaffold",
            status="complete",
            cadence_dir_exists=True,
        )
        self.assertTrue(found)
        data, found = set_workflow_item_status(
            data,
            item_id="task-prerequisite-gate",
            status="complete",
            cadence_dir_exists=True,
        )
        self.assertTrue(found)
        data, found = set_workflow_item_status(
            data,
            item_id="task-brownfield-intake",
            status="complete",
            cadence_dir_exists=True,
        )
        self.assertTrue(found)

        route = data["workflow"]["next_route"]
        self.assertEqual(route.get("skill_name"), "brownfield-documenter")

    def test_non_binary_legacy_task_statuses_are_preserved(self) -> None:
        for status in ("in_progress", "blocked", "skipped"):
            with self.subTest(status=status):
                data = default_data()
                updated, found = set_workflow_item_status(
                    data,
                    item_id="task-prerequisite-gate",
                    status=status,
                    cadence_dir_exists=True,
                )
                self.assertTrue(found)
                item = find_item(updated["workflow"]["plan"], "task-prerequisite-gate")
                self.assertIsNotNone(item)
                self.assertEqual(item["status"], status)

    def test_legacy_completion_flags_still_promote_pending_items(self) -> None:
        data = default_data()
        updated, found = set_workflow_item_status(
            data,
            item_id="task-research",
            status="pending",
            cadence_dir_exists=True,
        )
        self.assertTrue(found)
        scaffold = find_item(updated["workflow"]["plan"], "task-scaffold")
        self.assertIsNotNone(scaffold)
        self.assertEqual(scaffold["status"], "complete")

    def test_missing_brownfield_legacy_flag_falls_back_to_ideation_completion(self) -> None:
        data = default_data()
        state = data.setdefault("state", {})
        state.pop("brownfield-intake-completed", None)
        state["ideation-completed"] = True
        updated = reconcile_workflow_state(data, cadence_dir_exists=True)

        intake = find_item(updated["workflow"]["plan"], "task-brownfield-intake")
        self.assertIsNotNone(intake)
        self.assertEqual(intake["status"], "complete")

    def test_greenfield_routes_to_planner_after_research(self) -> None:
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
            self.assertTrue(found)

        route = data["workflow"]["next_route"]
        self.assertEqual(route.get("skill_name"), "planner")

    def test_brownfield_skips_planner(self) -> None:
        data = default_data()
        state = data.setdefault("state", {})
        state["project-mode"] = "brownfield"

        for task_id in (
            "task-scaffold",
            "task-prerequisite-gate",
            "task-brownfield-intake",
            "task-brownfield-documentation",
            "task-research",
        ):
            data, found = set_workflow_item_status(
                data,
                item_id=task_id,
                status="complete",
                cadence_dir_exists=True,
            )
            self.assertTrue(found)

        updated = reconcile_workflow_state(data, cadence_dir_exists=True)
        planner_task = find_item(updated["workflow"]["plan"], "task-roadmap-planning")
        self.assertIsNotNone(planner_task)
        self.assertEqual(planner_task["status"], "skipped")
        self.assertEqual(updated["workflow"]["next_item"]["id"], "complete")


if __name__ == "__main__":
    unittest.main()
