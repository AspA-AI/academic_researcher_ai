import os
import sys
import unittest
from typing import Any, Dict, List

# Ensure `import api...` works when tests are executed from repo root.
# The codebase expects `ai_researcher/` to be on PYTHONPATH so that `api/` is importable.
AI_RESEARCHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if AI_RESEARCHER_DIR not in sys.path:
    sys.path.insert(0, AI_RESEARCHER_DIR)


class FakeLLMBackend:
    """A tiny fake backend to avoid real LLM calls in unit tests."""

    def __init__(self, response: str):
        self._response = response

    async def generate(self, prompt: str, **kwargs) -> str:  # noqa: ARG002
        return self._response

    async def generate_with_tools(self, prompt: str, tools: List[Any], **kwargs) -> Dict[str, Any]:  # noqa: ARG002
        return {"content": self._response, "tools_used": [], "model": "fake"}

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": "fake", "model": "fake", "temperature": 0.0, "max_tokens": 1_000_000}


class AgentOutputShapeTests(unittest.IsolatedAsyncioTestCase):
    async def test_literature_review_agent_output_shape(self):
        from api.agents.literature_review_agent import LiteratureReviewAgent

        fake_text = "\n".join(
            [
                "Introduction",
                "This is an intro summary sentence.",
                "Key Findings",
                "- Finding A shows impact.",
                "- Finding B indicates trend.",
                "Research Gaps",
                "- Gap A remains open.",
                "Future Directions",
                "- Direction A.",
            ]
        )

        agent = LiteratureReviewAgent(llm_backend=FakeLLMBackend(fake_text))
        docs = [{"title": "Paper 1", "extracted_content": "Long enough content " * 20, "authors": ["A"], "year": 2024}]
        out = await agent.run(docs, "TestDomain")

        self.assertIn("summary", out)
        self.assertIn("key_findings", out)
        self.assertIn("research_gaps", out)
        self.assertIn("full_literature_review", out)
        self.assertEqual(out["research_domain"], "TestDomain")
        self.assertEqual(out["documents_analyzed"], 1)

    async def test_initial_coding_agent_output_shape(self):
        from api.agents.initial_coding_agent import InitialCodingAgent

        fake_response = "\n".join(
            [
                "### Unit (ID: unit_0000)",
                "**Primary Code:** Transparency Mechanisms:** Mentions mechanisms that improve transparency.",
                "Insight: This suggests traceability improvements.",
            ]
        )

        agent = InitialCodingAgent(llm_backend=FakeLLMBackend(fake_response))
        docs = [
            {
                "title": "Paper 1",
                "extracted_content": ("Paragraph one. " * 100) + "\n\n" + ("Paragraph two. " * 100),
                "authors": ["Author One"],
                "year": 2024,
            }
        ]
        out = await agent.run(docs, "TestDomain")

        self.assertIn("coding_summary", out)
        self.assertIn("coded_units", out)
        self.assertIsInstance(out["coded_units"], list)
        self.assertEqual(out["research_domain"], "TestDomain")

    async def test_thematic_grouping_agent_output_shape(self):
        from api.agents.thematic_grouping_agent import ThematicGroupingAgent

        fake_response = "\n".join(
            [
                "### Theme 1: Governance Transparency",
                "Description",
                "This theme covers transparency mechanisms.",
                "Codes",
                "- Transparency Mechanisms",
                "Justification",
                "These codes cluster around transparency.",
                "Quotes",
                "\"Quote about transparency\" (Author, 2024)",
                "Cross-cutting",
                "Trust and auditability",
                "Reasoning",
                "Grounded in governance theory.",
            ]
        )

        agent = ThematicGroupingAgent(llm_backend=FakeLLMBackend(fake_response))
        coded_units = [
            {
                "unit_id": "unit_0000",
                "content": "Some content",
                "codes": [{"name": "Transparency Mechanisms", "definition": "def", "confidence": 0.8, "category": "primary"}],
                "harvard_citation": "(Author, 2024)",
                "insights": [],
            }
        ]
        out = await agent.run(coded_units, "TestDomain")

        self.assertIn("thematic_summary", out)
        self.assertIn("themes", out)
        self.assertIsInstance(out["themes"], list)
        self.assertEqual(out["research_domain"], "TestDomain")

    async def test_theme_refiner_agent_output_shape(self):
        from api.agents.theme_refiner_agent import ThemeRefinerAgent

        fake_response = "\n".join(
            [
                "### Theme 1: Refined Governance Transparency",
                "Definition",
                "A precise definition.",
                "Scope",
                "Included: A, B. Excluded: C.",
                "Quotes",
                "\"A quote\" (Author, 2024)",
                "Concepts",
                "Accountability, Auditability",
                "Framework",
                "Institutional theory",
                "Implications",
                "More validation studies needed.",
            ]
        )

        agent = ThemeRefinerAgent(llm_backend=FakeLLMBackend(fake_response))
        themes = [
            {
                "theme_name": "Governance Transparency",
                "description": "desc",
                "codes": [{"name": "Transparency Mechanisms"}],
                "justification": "just",
                "cross_cutting_ideas": [],
                "academic_reasoning": "reason",
            }
        ]
        out = await agent.run(themes, "TestDomain")

        self.assertIn("refined_themes", out)
        self.assertIn("refinement_summary", out)
        self.assertEqual(out["research_domain"], "TestDomain")

    async def test_report_generator_agent_json_output_shape(self):
        from api.agents.report_generator_agent import ReportGeneratorAgent

        fake_json = """
        {
          "report": {
            "title": "Test Report",
            "research_domain": "TestDomain",
            "generated_at": "2026-01-01T00:00:00Z",
            "sections": {
              "abstract": "A",
              "introduction": "I",
              "literature_review": "LR",
              "methodology": "M",
              "findings": [
                {
                  "theme_name": "Theme A",
                  "precise_definition": "Def",
                  "scope": {"included": ["x"], "excluded": ["y"]},
                  "supporting_quotes": [{"quote": "q", "citation": "(A, 2024)"}],
                  "key_concepts": ["c1"],
                  "theoretical_frameworks": ["f1"],
                  "research_implications": ["imp1"]
                }
              ],
              "discussion": "D",
              "conclusion": "C"
            },
            "references": [{"full_citation": "A (2024) Title.", "author": "A", "year": "2024", "title": "Title", "doi": "", "url": ""}]
          },
          "rendered": {"markdown": "# Test"}
        }
        """

        agent = ReportGeneratorAgent(llm_backend=FakeLLMBackend(fake_json))
        sections = {"research_domain": "TestDomain", "literature_review": {}, "initial_coding": {}, "thematic_grouping": {}, "theme_refinement": {}}
        out = await agent.run(sections)

        self.assertIn("report", out)
        self.assertIn("rendered", out)
        self.assertIn("report_summary", out)
        self.assertEqual(out["report"]["research_domain"], "TestDomain")


if __name__ == "__main__":
    unittest.main()


