import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ideation_research import normalize_ideation_research, reset_research_execution
from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status

RUN_RESEARCH_PASS_SCRIPT = SCRIPTS_DIR / "run-research-pass.py"


def build_cadence_state(
    *,
    pass_queue: list[dict[str, Any]] | None = None,
    planning_overrides: dict[str, Any] | None = None,
    topic_status_overrides: dict[str, dict[str, Any]] | None = None,
    pass_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data = default_data()
    data.setdefault("state", {})["project-mode"] = "greenfield"
    for task_id in (
        "task-scaffold",
        "task-prerequisite-gate",
        "task-brownfield-intake",
        "task-brownfield-documentation",
        "task-ideation",
    ):
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
    if pass_queue is None:
        pass_queue = [
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
    execution["pass_queue"] = pass_queue
    if planning_overrides:
        execution.setdefault("planning", {}).update(planning_overrides)
    if pass_history is not None:
        execution["pass_history"] = pass_history

    topic_status = execution.get("topic_status", {})
    if topic_status_overrides:
        for topic_id, updates in topic_status_overrides.items():
            existing = topic_status.get(topic_id)
            if not isinstance(existing, dict):
                continue
            existing.update(updates)

    execution["status"] = "in_progress"
    data["ideation"] = ideation
    data.setdefault("state", {})["ideation-completed"] = True
    data["state"]["research-completed"] = False
    return reconcile_workflow_state(data, cadence_dir_exists=True)


def write_state(project_root: Path, state: dict[str, Any]) -> Path:
    cadence_dir = project_root / ".cadence"
    cadence_dir.mkdir(parents=True, exist_ok=True)
    cadence_json = cadence_dir / "cadence.json"
    cadence_json.write_text(json.dumps(state, indent=4) + "\n", encoding="utf-8")
    return cadence_json


def run_complete(project_root: Path, *, pass_id: str, payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUN_RESEARCH_PASS_SCRIPT),
            "--project-root",
            str(project_root),
            "complete",
            "--pass-id",
            pass_id,
            "--json",
            json.dumps(payload),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def run_start(project_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUN_RESEARCH_PASS_SCRIPT),
            "--project-root",
            str(project_root),
            "start",
            "--ack-handoff",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class RunResearchPassValidationTests(unittest.TestCase):
    def test_complete_requires_result_for_every_topic_in_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(project_root, build_cadence_state())

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

            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 2)
            self.assertIn("PASS_RESULT_MISSING_TOPICS", result.stderr)
            self.assertIn("topic-two", result.stderr)

    def test_does_not_replan_queue_mid_round_after_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        },
                        {
                            "pass_id": "pass-r1-02",
                            "round": 1,
                            "status": "pending",
                            "topic_ids": ["topic-two"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "",
                        },
                    ]
                ),
            )

            payload = {
                "pass_summary": "Topic one needs one more pass.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "needs_followup",
                        "summary": "Need one more clarification.",
                        "confidence": "medium",
                        "unresolved_questions": ["Open question"],
                        "sources": [{"url": "https://example.com/1"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["summary"]["next_pass_id"], "pass-r1-02")

            state = json.loads((project_root / ".cadence" / "cadence.json").read_text(encoding="utf-8"))
            queue = state["ideation"]["research_execution"]["pass_queue"]
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["pass_id"], "pass-r1-02")
            self.assertEqual(queue[0]["topic_ids"], ["topic-two"])

    def test_replans_when_round_queue_drains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        }
                    ],
                    topic_status_overrides={"topic-two": {"status": "complete"}},
                ),
            )

            payload = {
                "pass_summary": "Topic one still needs follow-up.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "needs_followup",
                        "summary": "Need one more clarification.",
                        "confidence": "medium",
                        "unresolved_questions": ["Open question"],
                        "sources": [{"url": "https://example.com/2"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["summary"]["next_pass_id"], "pass-r2-01")

            state = json.loads((project_root / ".cadence" / "cadence.json").read_text(encoding="utf-8"))
            queue = state["ideation"]["research_execution"]["pass_queue"]
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["pass_id"], "pass-r2-01")
            self.assertEqual(queue[0]["topic_ids"], ["topic-one"])

    def test_complete_with_unresolved_questions_becomes_complete_with_caveats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        }
                    ],
                    topic_status_overrides={"topic-two": {"status": "complete"}},
                ),
            )

            payload = {
                "pass_summary": "Topic one finalized with caveats.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "complete",
                        "summary": "Primary recommendation stands.",
                        "confidence": "high",
                        "unresolved_questions": ["Need direct vendor confirmation"],
                        "sources": [{"url": "https://example.com/3"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertTrue(output["research_complete"])

            state = json.loads((project_root / ".cadence" / "cadence.json").read_text(encoding="utf-8"))
            topic_one = state["ideation"]["research_execution"]["topic_status"]["topic-one"]
            self.assertEqual(topic_one["status"], "complete_with_caveats")
            self.assertTrue(state["state"]["research-completed"])

    def test_topic_pass_cap_converts_followup_to_complete_with_caveats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        }
                    ],
                    planning_overrides={"max_passes_per_topic": 2},
                    topic_status_overrides={
                        "topic-one": {"passes_attempted": 1},
                        "topic-two": {"status": "complete"},
                    },
                ),
            )

            payload = {
                "pass_summary": "Reached cap on topic one.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "needs_followup",
                        "summary": "Best available recommendation captured.",
                        "confidence": "high",
                        "unresolved_questions": ["Need commercial confirmation"],
                        "sources": [{"url": "https://example.com/4"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertTrue(output["research_complete"])

            state = json.loads((project_root / ".cadence" / "cadence.json").read_text(encoding="utf-8"))
            topic_one = state["ideation"]["research_execution"]["topic_status"]["topic-one"]
            self.assertEqual(topic_one["status"], "complete_with_caveats")
            self.assertGreaterEqual(topic_one["passes_attempted"], 2)
            self.assertEqual(state["ideation"]["research_execution"]["summary"]["pass_pending"], 0)

    def test_total_pass_cap_finishes_remaining_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        },
                        {
                            "pass_id": "pass-r1-02",
                            "round": 1,
                            "status": "pending",
                            "topic_ids": ["topic-two"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "",
                        },
                    ],
                    planning_overrides={"max_total_passes": 1},
                    pass_history=[
                        {
                            "pass_id": "pass-r0-01",
                            "round": 0,
                            "completed_at": "2026-01-01T00:00:00Z",
                            "pass_summary": "Previous pass",
                            "topics": [],
                            "source_ids": [],
                        }
                    ],
                ),
            )

            payload = {
                "pass_summary": "Hit global cap.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "needs_followup",
                        "summary": "Sufficient for now.",
                        "confidence": "medium",
                        "unresolved_questions": ["Could investigate more"],
                        "sources": [{"url": "https://example.com/5"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertTrue(output["research_complete"])

            state = json.loads((project_root / ".cadence" / "cadence.json").read_text(encoding="utf-8"))
            execution = state["ideation"]["research_execution"]
            self.assertEqual(execution["summary"]["pass_pending"], 0)
            self.assertEqual(execution["topic_status"]["topic-one"]["status"], "complete_with_caveats")
            self.assertEqual(execution["topic_status"]["topic-two"]["status"], "complete_with_caveats")

    def test_start_prioritizes_pending_topics_before_repeat_followups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[],
                    planning_overrides={"max_topics_per_pass": 1, "target_effort_per_pass": 10},
                    topic_status_overrides={
                        "topic-one": {"status": "needs_followup", "passes_attempted": 5},
                        "topic-two": {"status": "pending", "passes_attempted": 0},
                    },
                ),
            )

            result = run_start(project_root)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["pass"]["topic_ids"], ["topic-two"])

    def test_incomplete_pass_stays_in_chat_when_context_budget_not_reached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        }
                    ],
                    planning_overrides={
                        "context_window_tokens": 100000,
                        "handoff_context_threshold_percent": 70,
                        "estimated_fixed_tokens_per_chat": 0,
                        "estimated_tokens_in_overhead_per_pass": 0,
                        "estimated_tokens_out_overhead_per_pass": 0,
                        "max_passes_per_chat": 10,
                    },
                    topic_status_overrides={"topic-two": {"status": "complete"}},
                ),
            )

            payload = {
                "pass_summary": "Need one more pass for topic one.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "needs_followup",
                        "summary": "More validation needed.",
                        "confidence": "medium",
                        "unresolved_questions": ["Need one more source"],
                        "sources": [{"url": "https://example.com/context-low"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertFalse(output["research_complete"])
            self.assertFalse(output["handoff_required"])
            self.assertEqual(output["handoff_reason"], "")
            self.assertLess(output["summary"]["context_percent_estimate"], 70.0)

    def test_incomplete_pass_requires_handoff_when_context_budget_reached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        }
                    ],
                    planning_overrides={
                        "context_window_tokens": 2000,
                        "handoff_context_threshold_percent": 50,
                        "estimated_fixed_tokens_per_chat": 900,
                        "estimated_tokens_in_overhead_per_pass": 0,
                        "estimated_tokens_out_overhead_per_pass": 0,
                        "max_passes_per_chat": 10,
                    },
                    topic_status_overrides={"topic-two": {"status": "complete"}},
                ),
            )

            payload = {
                "pass_summary": "Need one more pass for topic one.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "needs_followup",
                        "summary": "Still unresolved.",
                        "confidence": "medium",
                        "unresolved_questions": ["Need one more source"],
                        "sources": [{"url": "https://example.com/context-high"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertFalse(output["research_complete"])
            self.assertTrue(output["handoff_required"])
            self.assertEqual(output["handoff_reason"], "context_budget")
            self.assertGreaterEqual(output["summary"]["context_percent_estimate"], 50.0)

    def test_incomplete_pass_requires_handoff_when_chat_pass_cap_reached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            write_state(
                project_root,
                build_cadence_state(
                    pass_queue=[
                        {
                            "pass_id": "pass-r1-01",
                            "round": 1,
                            "status": "in_progress",
                            "topic_ids": ["topic-one"],
                            "planned_effort": 2,
                            "created_at": "2026-01-01T00:00:00Z",
                            "started_at": "2026-01-01T00:00:01Z",
                        }
                    ],
                    planning_overrides={
                        "context_window_tokens": 200000,
                        "handoff_context_threshold_percent": 90,
                        "estimated_fixed_tokens_per_chat": 0,
                        "estimated_tokens_in_overhead_per_pass": 0,
                        "estimated_tokens_out_overhead_per_pass": 0,
                        "max_passes_per_chat": 1,
                    },
                    topic_status_overrides={"topic-two": {"status": "complete"}},
                ),
            )

            payload = {
                "pass_summary": "Need one more pass for topic one.",
                "topics": [
                    {
                        "topic_id": "topic-one",
                        "status": "needs_followup",
                        "summary": "Still unresolved.",
                        "confidence": "medium",
                        "unresolved_questions": ["Need one more source"],
                        "sources": [{"url": "https://example.com/pass-cap"}],
                    }
                ],
            }
            result = run_complete(project_root, pass_id="pass-r1-01", payload=payload)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertFalse(output["research_complete"])
            self.assertTrue(output["handoff_required"])
            self.assertEqual(output["handoff_reason"], "pass_cap")


if __name__ == "__main__":
    unittest.main()
