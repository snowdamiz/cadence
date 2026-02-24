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


if __name__ == "__main__":
    unittest.main()
