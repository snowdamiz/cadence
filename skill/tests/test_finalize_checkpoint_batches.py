import importlib.util
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
FINALIZE_SCRIPT = SCRIPTS_DIR / "finalize-skill-checkpoint.py"

spec = importlib.util.spec_from_file_location("finalize_skill_checkpoint", FINALIZE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load finalize-skill-checkpoint.py")
finalize_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finalize_module)


class FinalizeCheckpointBatchTests(unittest.TestCase):
    def test_build_batches_groups_and_chunks_deterministically(self) -> None:
        config = {
            "atomic": {
                "max_files_per_commit": 2,
                "group_order": ["docs", "scripts"],
                "groups": {
                    "docs": {
                        "tag": "docs",
                        "label": "documentation",
                        "patterns": ["**/*.md", "*.md"],
                    },
                    "scripts": {
                        "tag": "scripts",
                        "label": "automation scripts",
                        "patterns": ["scripts/**"],
                    },
                },
            }
        }
        paths = [
            "README.md",
            "docs/guide.md",
            "scripts/a.py",
            "scripts/b.py",
            "scripts/c.py",
        ]

        batches = finalize_module.build_batches(paths, config)
        self.assertEqual(len(batches), 3)

        self.assertEqual(batches[0]["group_key"], "docs")
        self.assertEqual(batches[0]["message_suffix"], "[docs]")
        self.assertEqual(sorted(batches[0]["paths"]), ["README.md", "docs/guide.md"])

        self.assertEqual(batches[1]["group_key"], "scripts")
        self.assertEqual(batches[1]["message_suffix"], "[scripts1/2]")
        self.assertEqual(sorted(batches[1]["paths"]), ["scripts/a.py", "scripts/b.py"])

        self.assertEqual(batches[2]["group_key"], "scripts")
        self.assertEqual(batches[2]["message_suffix"], "[scripts2/2]")
        self.assertEqual(batches[2]["paths"], ["scripts/c.py"])

    def test_filter_paths_supports_glob_specs(self) -> None:
        filtered = finalize_module.filter_paths(
            ["docs/readme.md", "scripts/run.sh", "src/main.ts"],
            ["docs/**", "scripts/**"],
        )
        self.assertEqual(filtered, ["docs/readme.md", "scripts/run.sh"])

    def test_parse_status_paths_skips_ignored_entries(self) -> None:
        status_output = "\n".join(
            [
                "?? .gitignore",
                "!! .cadence/",
                " M README.md",
            ]
        )
        parsed = finalize_module.parse_status_paths(status_output)
        self.assertEqual(parsed, [".gitignore", "README.md"])

    def test_normalize_requested_pathspecs_scopes_to_project_root(self) -> None:
        repo_root = Path("/tmp/repo")
        project_root = repo_root / "apps" / "service-a"

        scoped = finalize_module.normalize_requested_pathspecs(
            requested_pathspecs=[".", "src", "docs/**"],
            project_root=project_root,
            repo_root=repo_root,
        )
        self.assertEqual(
            scoped,
            ["apps/service-a", "apps/service-a/src", "apps/service-a/docs/**"],
        )

    def test_normalize_requested_pathspecs_rejects_parent_escape(self) -> None:
        repo_root = Path("/tmp/repo")
        project_root = repo_root / "apps" / "service-a"

        with self.assertRaises(finalize_module.FinalizeError):
            finalize_module.normalize_requested_pathspecs(
                requested_pathspecs=["../shared"],
                project_root=project_root,
                repo_root=repo_root,
            )


if __name__ == "__main__":
    unittest.main()
