"""
Literature Review Agent Prompts

Prompt templates for the Literature Review Agent.
"""

from typing import List, Dict, Any
from api.agents.agent_prompts.base_prompts import BaseAgentPrompts

class LiteratureReviewPrompts:
    """
    Prompt templates for the Literature Review Agent.
    """
    
    @staticmethod
    def build_literature_review_prompt(documents: List[Dict[str, Any]], research_domain: str = "General", 
                                     supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Build the literature review prompt with optional supervisor feedback integration.
        """
        # Format document content
        content_parts = BaseAgentPrompts.format_document_content(documents, research_domain)
        
        # Build supervisor feedback section if provided
        supervisor_section = BaseAgentPrompts.get_supervisor_feedback_section(
            supervisor_feedback, previous_attempts, attempt_number, max_attempts
        )
        
        prompt = f"""You are the Literature Reviewer Agent. Your task is to synthesize and evaluate the key academic publications retrieved by the Data Retrieval Agent to produce a formal **Literature Review** section.

Your analysis must stay strictly focused on the **given research domain and the supplied documents**. Do **not** introduce external domains (such as blockchain, Web3, or unrelated technologies) unless they explicitly appear in the provided papers.

{BaseAgentPrompts.get_academic_tone_guidelines()}

---

**Objectives:**

1. **Contextual Framing:** Situate the user’s research topic within existing academic debates in the specified research domain: "{research_domain}".
2. **Comparative Synthesis:** Compare how the authors of the retrieved papers conceptualize and operationalize key ideas, including areas of agreement, disagreement, and evolution over time.
3. **Identify Gaps:** Point out theoretical, empirical, or methodological gaps that justify a deeper thematic analysis.
4. **Citations (GROUNDING REQUIREMENT):** Use Harvard-style in-text citations **only for papers that actually appear in the provided document list**. Do **not** invent placeholder sources (e.g., "Source A", "Author X") or cite works that are not present in the input.
5. **Deliverable:** Output a self-contained Literature Review section that can feed directly into the final report for this specific topic.

---

{BaseAgentPrompts.get_harvard_citation_guidelines()}

Additional grounding rules:
- When referring to evidence or examples, tie them explicitly to the titles, authors, and years present in the supplied documents.
- If a document is missing author names or a year, you may refer to it by title only, but you must **not** fabricate missing metadata.
- Do not introduce blockchain, Web3, governance, or other unrelated domains unless they clearly appear in the supplied content.

{supervisor_section}

**Based on the following academic papers and their content, generate a comprehensive literature review:**

{content_parts}

Please provide a structured literature review that addresses the objectives above, using the specified tone and citation format."""
        
        return prompt 