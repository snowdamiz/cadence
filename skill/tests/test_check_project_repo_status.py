import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
CHECK_REPO_SCRIPT = SCRIPTS_DIR / "check-project-repo-status.py"


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


class CheckProjectRepoStatusTests(unittest.TestCase):
    def test_any_remote_policy_enables_non_github_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            run(["git", "init"], project_root)
            run(["git", "remote", "add", "origin", "git@gitlab.com:acme/repo.git"], project_root)

            result = run(
                [
                    sys.executable,
                    str(CHECK_REPO_SCRIPT),
                    "--project-root",
                    str(project_root),
                ],
                project_root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertTrue(payload["git_initialized"])
            self.assertTrue(payload["remote_configured"])
            self.assertTrue(payload["repo_enabled_detected"])
            self.assertFalse(payload["github_remote_configured"])

    def test_github_policy_requires_github_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            run(["git", "init"], project_root)
            run(["git", "remote", "add", "origin", "git@gitlab.com:acme/repo.git"], project_root)

            result = run(
                [
                    sys.executable,
                    str(CHECK_REPO_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--remote-policy",
                    "github",
                ],
                project_root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["remote_policy"], "github")
            self.assertFalse(payload["repo_enabled_detected"])


if __name__ == "__main__":
    unittest.main()
