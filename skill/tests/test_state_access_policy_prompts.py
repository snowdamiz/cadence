import re
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
STATE_ACCESS_PATTERN = re.compile(r"Never read or edit [`]?\.cadence/cadence\.json[`]? directly")


def target_files() -> list[Path]:
    files: list[Path] = [
        SKILL_ROOT / "SKILL.md",
        SKILL_ROOT / "agents" / "openai.yaml",
        SKILL_ROOT / "assets" / "AGENTS.md",
    ]

    for skill_md in sorted((SKILL_ROOT / "skills").glob("*/SKILL.md")):
        files.append(skill_md)

    for agent_yaml in sorted((SKILL_ROOT / "skills").glob("*/agents/openai.yaml")):
        files.append(agent_yaml)

    return files


class StateAccessPolicyPromptTests(unittest.TestCase):
    def test_all_skill_prompts_forbid_direct_cadence_json_reads_and_edits(self) -> None:
        missing_policy: list[str] = []

        for path in target_files():
            content = path.read_text(encoding="utf-8")
            if STATE_ACCESS_PATTERN.search(content) is None:
                missing_policy.append(str(path.relative_to(SKILL_ROOT.parent)))

        self.assertEqual(
            missing_policy,
            [],
            msg=(
                "Missing direct cadence.json read/edit prohibition in: "
                + ", ".join(missing_policy)
            ),
        )


if __name__ == "__main__":
    unittest.main()
