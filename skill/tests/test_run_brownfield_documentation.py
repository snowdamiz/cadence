import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workflow_state import default_data, reconcile_workflow_state, set_workflow_item_status

RUN_DOC_SCRIPT = SCRIPTS_DIR / "run-brownfield-documentation.py"
RUN_RESEARCH_PASS_SCRIPT = SCRIPTS_DIR / "run-research-pass.py"


def build_doc_ready_state() -> dict:
    data = default_data()
    state = data.setdefault("state", {})
    state["project-mode"] = "brownfield"
    for task_id in ("task-scaffold", "task-prerequisite-gate", "task-brownfield-intake"):
        data, found = set_workflow_item_status(
            data,
            item_id=task_id,
            status="complete",
            cadence_dir_exists=True,
        )
        if not found:
            raise RuntimeError(f"Missing workflow item in fixture: {task_id}")
    return reconcile_workflow_state(data, cadence_dir_exists=True)


def build_brownfield_payload() -> dict:
    return {
        "objective": "Improve reliability and delivery speed of the existing product platform.",
        "core_outcome": "A documented and research-ready plan aligned to current system constraints.",
        "target_audience": ["Engineering leadership", "Platform team"],
        "core_experience": "Stabilize core workflows without disrupting active product delivery.",
        "in_scope": ["architecture mapping", "operational risk analysis", "delivery sequencing"],
        "out_of_scope": ["net-new product ideation"],
        "implementation_approach": {
            "method": "Evidence-first brownfield analysis grounded in current repository behavior."
        },
        "milestones": ["baseline captured", "research agenda validated", "research phase kickoff"],
        "constraints": ["maintain service continuity", "respect existing stack and ownership boundaries"],
        "risks": ["hidden coupling between services", "unknown CI/CD gaps"],
        "success_signals": ["clear topic backlog", "traceable entity ownership", "research handoff readiness"],
        "research_agenda": {
            "blocks": [
                {
                    "block_id": "architecture-current-state",
                    "title": "Current Architecture",
                    "rationale": "Understand current boundaries before planning downstream changes.",
                    "tags": ["architecture"],
                    "topics": [
                        {
                            "topic_id": "service-boundaries",
                            "title": "Service Boundaries",
                            "category": "architecture",
                            "priority": "high",
                            "why_it_matters": "Boundaries define ownership and change risk.",
                            "research_questions": [
                                "Which modules are current system entrypoints?",
                                "Where are the strongest coupling points?",
                            ],
                            "keywords": ["entrypoint", "service", "module"],
                            "tags": ["current-state"],
                            "related_entities": ["api-service"],
                        }
                    ],
                }
            ],
            "entity_registry": [
                {
                    "entity_id": "api-service",
                    "label": "API Service",
                    "kind": "service",
                    "aliases": ["api"],
                    "owner_block_id": "architecture-current-state",
                }
            ],
            "topic_index": {},
        },
    }


def build_sparse_research_only_payload() -> dict:
    return {
        "research_agenda": {
            "blocks": [
                {
                    "title": "Architecture Overview",
                    "topics": [{"title": "Entrypoints and Boundaries"}],
                }
            ]
        }
    }


def build_cross_block_entity_payload() -> dict:
    return {
        "research_agenda": {
            "blocks": [
                {
                    "block_id": "block-product",
                    "title": "Product",
                    "topics": [
                        {
                            "topic_id": "topic-one",
                            "title": "Topic One",
                            "related_entities": ["shared-stack"],
                        }
                    ],
                },
                {
                    "block_id": "block-backend",
                    "title": "Backend",
                    "topics": [
                        {
                            "topic_id": "topic-two",
                            "title": "Topic Two",
                            "related_entities": ["shared-stack"],
                        }
                    ],
                },
            ],
            "entity_registry": [
                {
                    "entity_id": "shared-stack",
                    "label": "Shared Stack",
                    "kind": "capability",
                    "owner_block_id": "block-product",
                }
            ],
            "topic_index": {},
        }
    }


class RunBrownfieldDocumentationTests(unittest.TestCase):
    def test_discover_is_read_only_and_returns_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_doc_ready_state(), indent=4) + "\n", encoding="utf-8")
            (project_root / "README.md").write_text("# App\n\nExisting brownfield project.\n", encoding="utf-8")
            (project_root / "docs").mkdir(parents=True, exist_ok=True)
            (project_root / "docs" / "architecture.md").write_text("Service map.\n", encoding="utf-8")
            (project_root / "package.json").write_text(
                json.dumps({"name": "app", "scripts": {"test": "vitest"}, "dependencies": {"react": "^18.0.0"}})
                + "\n",
                encoding="utf-8",
            )
            (project_root / "src").mkdir(parents=True, exist_ok=True)
            (project_root / "src" / "index.ts").write_text("export const ok = true;\n", encoding="utf-8")

            before = cadence_json.read_text(encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_DOC_SCRIPT),
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
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["action"], "discover")
            self.assertEqual(payload["mode"], "brownfield")
            context = payload.get("context", {})
            self.assertGreater(int(context.get("scan", {}).get("scanned_file_count", 0)), 0)
            manifests = context.get("inventory", {}).get("manifests", [])
            self.assertIn("package.json", manifests)

            after = cadence_json.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertFalse((project_root / ".cadence" / "tasks").exists())
            cadence_files = sorted(path.name for path in cadence_dir.iterdir() if path.is_file())
            self.assertEqual(cadence_files, ["cadence.json"])

    def test_complete_allows_omitted_planning_fields_and_research_still_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_doc_ready_state(), indent=4) + "\n", encoding="utf-8")

            complete = subprocess.run(
                [
                    sys.executable,
                    str(RUN_DOC_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "complete",
                    "--json",
                    json.dumps(build_sparse_research_only_payload()),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(complete.returncode, 0, msg=complete.stderr or complete.stdout)

            updated = json.loads(cadence_json.read_text(encoding="utf-8"))
            ideation = updated.get("ideation", {})
            for optional_field in (
                "objective",
                "core_outcome",
                "in_scope",
                "out_of_scope",
                "implementation_approach",
                "milestones",
                "constraints",
            ):
                self.assertNotIn(optional_field, ideation)

            agenda = ideation.get("research_agenda", {})
            summary = agenda.get("summary", {})
            self.assertEqual(int(summary.get("block_count", 0)), 1)
            self.assertEqual(int(summary.get("topic_count", 0)), 1)

            block = agenda.get("blocks", [])[0]
            topic = block.get("topics", [])[0]
            self.assertEqual(topic.get("category"), "general")
            self.assertEqual(topic.get("priority"), "medium")
            self.assertEqual(topic.get("related_entities"), [])

            route = updated.get("workflow", {}).get("next_route", {})
            self.assertEqual(route.get("skill_name"), "researcher")
            state = updated.get("state", {})
            self.assertTrue(state.get("ideation-completed"))
            self.assertTrue(state.get("brownfield-documentation-completed"))

            status = subprocess.run(
                [
                    sys.executable,
                    str(RUN_RESEARCH_PASS_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "status",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, msg=status.stderr or status.stdout)
            status_payload = json.loads(status.stdout)
            self.assertEqual(status_payload.get("status"), "ok")

            start = subprocess.run(
                [
                    sys.executable,
                    str(RUN_RESEARCH_PASS_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "start",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(start.returncode, 0, msg=start.stderr or start.stdout)
            start_payload = json.loads(start.stdout)
            self.assertEqual(start_payload.get("status"), "ok")
            self.assertEqual(start_payload.get("action"), "start")

            topic_ids = start_payload.get("pass", {}).get("topic_ids", [])
            self.assertEqual(len(topic_ids), 1)

    def test_complete_auto_repairs_cross_block_entity_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_doc_ready_state(), indent=4) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_DOC_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "complete",
                    "--json",
                    json.dumps(build_cross_block_entity_payload()),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload.get("status"), "ok")
            repairs = payload.get("payload_repairs", {})
            self.assertTrue(bool(repairs.get("applied", False)))
            self.assertGreaterEqual(int(repairs.get("cross_block_relinks", 0)), 1)

            updated = json.loads(cadence_json.read_text(encoding="utf-8"))
            agenda = updated.get("ideation", {}).get("research_agenda", {})
            topic_index = agenda.get("topic_index", {})
            topic_one = topic_index.get("topic-one", {})
            topic_two = topic_index.get("topic-two", {})
            topic_one_entities = topic_one.get("related_entities", [])
            topic_two_entities = topic_two.get("related_entities", [])

            self.assertEqual(len(topic_one_entities), 1)
            self.assertEqual(len(topic_two_entities), 1)
            self.assertNotEqual(topic_one_entities[0], topic_two_entities[0])

            owners = {
                str(entity.get("entity_id")): str(entity.get("owner_block_id"))
                for entity in agenda.get("entity_registry", [])
                if isinstance(entity, dict)
            }
            self.assertEqual(owners.get(topic_one_entities[0]), topic_one.get("block_id"))
            self.assertEqual(owners.get(topic_two_entities[0]), topic_two.get("block_id"))

    def test_complete_persists_ideation_and_routes_to_research(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            cadence_dir = project_root / ".cadence"
            cadence_dir.mkdir(parents=True, exist_ok=True)
            cadence_json = cadence_dir / "cadence.json"
            cadence_json.write_text(json.dumps(build_doc_ready_state(), indent=4) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUN_DOC_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "complete",
                    "--json",
                    json.dumps(build_brownfield_payload()),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["action"], "complete")
            self.assertEqual(payload["mode"], "brownfield")
            self.assertEqual(payload.get("next_route", {}).get("skill_name"), "researcher")

            updated = json.loads(cadence_json.read_text(encoding="utf-8"))
            state = updated.get("state", {})
            self.assertEqual(state.get("project-mode"), "brownfield")
            self.assertTrue(state.get("brownfield-documentation-completed"))
            self.assertTrue(state.get("ideation-completed"))
            self.assertFalse(state.get("research-completed"))

            route = updated.get("workflow", {}).get("next_route", {})
            self.assertEqual(route.get("skill_name"), "researcher")

            ideation = updated.get("ideation", {})
            self.assertEqual(
                ideation.get("objective"),
                "Improve reliability and delivery speed of the existing product platform.",
            )

            agenda = ideation.get("research_agenda", {})
            summary = agenda.get("summary", {})
            self.assertEqual(int(summary.get("block_count", 0)), 1)
            self.assertEqual(int(summary.get("topic_count", 0)), 1)
            self.assertEqual(int(summary.get("entity_count", 0)), 1)
            self.assertIn("service-boundaries", agenda.get("topic_index", {}))

            execution = ideation.get("research_execution", {})
            self.assertEqual(execution.get("status"), "pending")
            self.assertIn("service-boundaries", execution.get("topic_status", {}))

            self.assertFalse((project_root / ".cadence" / "tasks").exists())
            cadence_files = sorted(path.name for path in cadence_dir.iterdir() if path.is_file())
            self.assertEqual(cadence_files, ["cadence.json"])


if __name__ == "__main__":
    unittest.main()
