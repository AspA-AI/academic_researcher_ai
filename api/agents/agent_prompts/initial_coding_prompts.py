"""
Initial Coding Agent Prompts

Prompt templates for the Initial Coding Agent.
"""

from typing import List, Dict, Any
from api.agents.agent_prompts.base_prompts import BaseAgentPrompts

class InitialCodingPrompts:
    """
    Prompt templates for the Initial Coding Agent.
    """
    
    @staticmethod
    def build_coding_prompt(meaning_units: List[Any], research_domain: str = "General",
                           supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Build the initial coding prompt with optional supervisor feedback integration.
        """
        # Format meaning units
        content_parts = BaseAgentPrompts.format_meaning_units(meaning_units, research_domain)
        
        # Build supervisor feedback section if provided
        supervisor_section = BaseAgentPrompts.get_supervisor_feedback_section(
            supervisor_feedback, previous_attempts, attempt_number, max_attempts
        )
        
        prompt = f"""As the Initial Coding Agent, your task is to conduct open coding on the retrieved academic literature. Break down the text into meaningful units and assign descriptive codes that capture the essence of each idea, concept, or argument.

Ensure each code is linked to a specific source with Harvard-style in-text citation (e.g., Smith, 2022). Highlight patterns, disagreements, emerging concepts, and foundational premises.

Maintain an academic-conversational tone. Use expressions like "Generally speaking," or "We can infer that..." when introducing insights, while remaining faithful to the literature.
{BaseAgentPrompts.get_academic_tone_guidelines()}

**Objectives:**

1. **Comprehensive Familiarization:** Read all academic data to extract significant ideas.
2. **Code Identification:** Assign clear, descriptive labels to individual meaning units in the text.
3. **Academic Rigor:** Ensure all codes are traceable to original scholarly sources using Harvard-style in-text citations.
4. **Structured Output:** Present data segments alongside their codes and source citations for further processing.

**Coding Guidelines:**
- Use descriptive, plain-English codes that fit the actual topic and documents you see (e.g., for methods: "convolutional neural networks", "preprocessing techniques"; for other domains: "stakeholder engagement", "training data quality").
- Create both primary codes (main concepts) and sub-codes (specific aspects)
- Provide clear definitions for each code
- Assess confidence in your coding (0.0-1.0)
- Be consistent with similar concepts across units
- Focus on what the text is about, not your interpretation
- Do **not** use placeholder code names such as "Sub-:" or "Definition:". Every code name must be a meaningful phrase a human researcher could reuse as a label.

**Output Format:**
For each meaning unit, provide:
1. Unit ID
2. Primary codes with definitions
3. Sub-codes with definitions  
4. Harvard-style citations
5. Key insights or patterns
6. Confidence scores

{supervisor_section}

**Based on the following meaning units, perform open coding:**

{content_parts}

Please provide structured coding results for each meaning unit, following the guidelines above."""
        
        return prompt 