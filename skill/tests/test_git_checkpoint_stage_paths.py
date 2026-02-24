import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "git-checkpoint.py"
SPEC = importlib.util.spec_from_file_location("git_checkpoint_module", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load git-checkpoint.py for tests")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

list_staged_files = MODULE.list_staged_files
stage_paths = MODULE.stage_paths


def run_git(repo_root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "UNKNOWN_GIT_ERROR"
        raise AssertionError(f"git {' '.join(args)} failed: {detail}")


class GitCheckpointStagePathsTests(unittest.TestCase):
    def init_repo(self, repo_root: Path) -> None:
        run_git(repo_root, "init")
        run_git(repo_root, "config", "user.email", "cadence-tests@example.com")
        run_git(repo_root, "config", "user.name", "Cadence Tests")

    def test_stage_paths_skips_ignored_files_and_stages_other_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self.init_repo(repo_root)

            (repo_root / ".gitignore").write_text(".cadence/\n", encoding="utf-8")
            (repo_root / ".cadence").mkdir()
            (repo_root / ".cadence" / "cadence.json").write_text("{}\n", encoding="utf-8")
            (repo_root / "README.md").write_text("# Cadence\n", encoding="utf-8")

            stage_paths(repo_root, [".cadence/cadence.json", "README.md"])

            self.assertEqual(list_staged_files(repo_root), ["README.md"])

    def test_stage_paths_keeps_tracked_files_even_when_ignored_by_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self.init_repo(repo_root)

            (repo_root / ".gitignore").write_text(".cadence/\n", encoding="utf-8")
            (repo_root / ".cadence").mkdir()
            tracked_file = repo_root / ".cadence" / "cadence.json"
            tracked_file.write_text('{"state": 1}\n', encoding="utf-8")

            run_git(repo_root, "add", ".gitignore")
            run_git(repo_root, "add", "-f", ".cadence/cadence.json")
            run_git(repo_root, "commit", "-m", "seed tracked cadence state")

            tracked_file.write_text('{"state": 2}\n', encoding="utf-8")
            stage_paths(repo_root, [".cadence/cadence.json"])

            self.assertEqual(list_staged_files(repo_root), [".cadence/cadence.json"])


if __name__ == "__main__":
    unittest.main()
