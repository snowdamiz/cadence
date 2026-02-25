import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
IDEATOR_SKILL = SKILL_ROOT / "skills" / "ideator" / "SKILL.md"
IDEATOR_AGENT = SKILL_ROOT / "skills" / "ideator" / "agents" / "openai.yaml"


class IdeatorTopicReviewPromptTests(unittest.TestCase):
    def test_skill_requires_early_topic_checkpoint(self) -> None:
        content = IDEATOR_SKILL.read_text(encoding="utf-8")

        self.assertIn(
            "Run a mandatory early research-topic checkpoint once the main concept and domain are clear:",
            content,
        )
        self.assertIn(
            "Generate the most extensive research-topic list possible from everything known so far.",
            content,
        )
        self.assertIn(
            "Checkpoint edits: Continue, add topics, or remove topics? (continue/add/remove)",
            content,
        )

    def test_skill_requires_full_topic_review_before_persistence(self) -> None:
        content = IDEATOR_SKILL.read_text(encoding="utf-8")

        self.assertIn(
            "Return every identified `research_agenda.blocks[].topics[]` item to the user in the final pre-persistence review.",
            content,
        )
        self.assertIn(
            "Topic edits needed: Add or remove any topics before persistence? (add/remove/no changes)",
            content,
        )
        self.assertIn(
            "Confirmation needed: Persist this ideation package to .cadence/cadence.json? (yes/no)",
            content,
        )

    def test_agent_prompt_reinforces_topic_review_gate(self) -> None:
        content = IDEATOR_AGENT.read_text(encoding="utf-8")

        self.assertIn(
            "Once the main concept and domain are clear, generate the most extensive research-topic list possible,",
            content,
        )
        self.assertIn(
            "show the full list, and ask whether to continue/add/remove topics before continuing discovery.",
            content,
        )
        self.assertIn(
            "Before persistence, always return the full research topic list and let the user add/remove topics.",
            content,
        )
        self.assertIn(
            "Only after explicit topic approval and explicit yes/no persistence confirmation,",
            content,
        )


if __name__ == "__main__":
    unittest.main()
