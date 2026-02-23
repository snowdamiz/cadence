import copy
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ideation_research import ResearchAgendaValidationError, normalize_ideation_research


def base_payload() -> dict:
    return {
        "objective": "test",
        "research_agenda": {
            "blocks": [
                {
                    "block_id": "block-a",
                    "title": "Block A",
                    "rationale": "",
                    "tags": [],
                    "topics": [
                        {
                            "topic_id": "topic-a1",
                            "title": "Topic A1",
                            "category": "general",
                            "priority": "high",
                            "why_it_matters": "",
                            "research_questions": ["q"],
                            "keywords": [],
                            "tags": [],
                            "related_entities": [],
                        }
                    ],
                },
                {
                    "block_id": "block-b",
                    "title": "Block B",
                    "rationale": "",
                    "tags": [],
                    "topics": [
                        {
                            "topic_id": "topic-b1",
                            "title": "Topic B1",
                            "category": "general",
                            "priority": "high",
                            "why_it_matters": "",
                            "research_questions": ["q"],
                            "keywords": [],
                            "tags": [],
                            "related_entities": [],
                        }
                    ],
                },
            ],
            "entity_registry": [],
            "topic_index": {},
        },
    }


class IdeationResearchNormalizationTests(unittest.TestCase):
    def test_alias_inference_does_not_cross_owner_block(self) -> None:
        payload = base_payload()
        payload["research_agenda"]["blocks"][0]["topics"][0]["related_entities"] = ["entity-marketplace-fees"]
        payload["research_agenda"]["blocks"][1]["topics"][0]["keywords"] = ["royalties"]
        payload["research_agenda"]["entity_registry"] = [
            {
                "entity_id": "entity-marketplace-fees",
                "label": "Marketplace fee system",
                "kind": "economy-system",
                "aliases": ["royalties", "platform fees"],
                "owner_block_id": "block-a",
            }
        ]

        normalized = normalize_ideation_research(copy.deepcopy(payload), require_topics=True)
        topics = normalized["research_agenda"]["blocks"]

        self.assertEqual(
            topics[0]["topics"][0]["related_entities"],
            ["entity-marketplace-fees"],
        )
        self.assertEqual(topics[1]["topics"][0]["related_entities"], [])

    def test_alias_inference_does_not_cross_existing_ownerless_block_reference(self) -> None:
        payload = base_payload()
        payload["research_agenda"]["blocks"][0]["topics"][0]["related_entities"] = ["entity-royalties"]
        payload["research_agenda"]["blocks"][1]["topics"][0]["keywords"] = ["royalties"]
        payload["research_agenda"]["entity_registry"] = [
            {
                "entity_id": "entity-royalties",
                "label": "Royalties",
                "kind": "economy-system",
                "aliases": ["royalties"],
                "owner_block_id": "",
            }
        ]

        normalized = normalize_ideation_research(copy.deepcopy(payload), require_topics=True)
        topics = normalized["research_agenda"]["blocks"]
        entity = normalized["research_agenda"]["entity_registry"][0]

        self.assertEqual(topics[1]["topics"][0]["related_entities"], [])
        self.assertEqual(entity["owner_block_id"], "block-a")

    def test_explicit_cross_block_reference_still_fails(self) -> None:
        payload = base_payload()
        payload["research_agenda"]["blocks"][1]["topics"][0]["related_entities"] = ["entity-marketplace-fees"]
        payload["research_agenda"]["entity_registry"] = [
            {
                "entity_id": "entity-marketplace-fees",
                "label": "Marketplace fee system",
                "kind": "economy-system",
                "aliases": ["royalties"],
                "owner_block_id": "block-a",
            }
        ]

        with self.assertRaises(ResearchAgendaValidationError) as ctx:
            normalize_ideation_research(copy.deepcopy(payload), require_topics=True)

        self.assertIn("ENTITY_OWNER_MISMATCH", str(ctx.exception))

    def test_same_block_alias_inference_still_links_entity(self) -> None:
        payload = base_payload()
        payload["research_agenda"]["blocks"][1]["topics"][0]["keywords"] = ["royalties"]
        payload["research_agenda"]["entity_registry"] = [
            {
                "entity_id": "entity-marketplace-fees",
                "label": "Marketplace fee system",
                "kind": "economy-system",
                "aliases": ["royalties"],
                "owner_block_id": "block-b",
            }
        ]

        normalized = normalize_ideation_research(copy.deepcopy(payload), require_topics=True)
        block_b_topic = normalized["research_agenda"]["blocks"][1]["topics"][0]

        self.assertEqual(block_b_topic["related_entities"], ["entity-marketplace-fees"])


if __name__ == "__main__":
    unittest.main()
