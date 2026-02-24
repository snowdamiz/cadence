import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "git-checkpoint.py"
SPEC = importlib.util.spec_from_file_location("git_checkpoint_module", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load git-checkpoint.py for tests")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

build_commit_message = MODULE.build_commit_message
CheckpointError = MODULE.CheckpointError


class GitCheckpointMessageTests(unittest.TestCase):
    def test_long_summary_is_truncated_to_subject_limit(self) -> None:
        config = {
            "commit_type": "cadence",
            "subject_max_length": 72,
            "scopes": {
                "brownfield-documenter": {
                    "checkpoints": {
                        "documentation-captured": "persist brownfield ideation documentation from existing codebase"
                    }
                }
            },
        }

        message = build_commit_message(
            config,
            scope="brownfield-documenter",
            checkpoint="documentation-captured",
            message_suffix="[skills]",
        )
        self.assertLessEqual(len(message), 72)
        self.assertTrue(message.startswith("cadence(brownfield-documenter): "))
        self.assertIn("...", message)

    def test_suffix_is_trimmed_when_present(self) -> None:
        config = {
            "commit_type": "cadence",
            "subject_max_length": 72,
            "scopes": {"ideator": {"checkpoints": {"ideation-completed": "persist finalized ideation"}}},
        }

        message = build_commit_message(
            config,
            scope="ideator",
            checkpoint="ideation-completed",
            message_suffix="[this-is-an-extremely-long-suffix-for-batch-tagging-that-must-be-trimmed]",
        )
        self.assertLessEqual(len(message), 72)
        self.assertIn("[", message)
        self.assertTrue(message.endswith("]"))

    def test_suffix_with_newline_is_rejected(self) -> None:
        config = {
            "commit_type": "cadence",
            "subject_max_length": 72,
            "scopes": {"ideator": {"checkpoints": {"ideation-completed": "persist finalized ideation"}}},
        }
        with self.assertRaises(CheckpointError):
            build_commit_message(
                config,
                scope="ideator",
                checkpoint="ideation-completed",
                message_suffix="bad\nsuffix",
            )

    def test_prefix_too_long_raises_deterministic_error(self) -> None:
        config = {
            "commit_type": "cadence",
            "subject_max_length": 20,
            "scopes": {"very-long-scope-name": {"checkpoints": {"x": "summary"}}},
        }
        with self.assertRaises(CheckpointError):
            build_commit_message(
                config,
                scope="very-long-scope-name",
                checkpoint="x",
            )


if __name__ == "__main__":
    unittest.main()
