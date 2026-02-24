import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workflow_state import default_data, set_workflow_item_status


def find_item(items: list[dict], item_id: str) -> dict | None:
    for item in items:
        if item.get("id") == item_id:
            return item
        nested = find_item(item.get("children", []), item_id)
        if nested is not None:
            return nested
    return None


class WorkflowStateStatusTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
