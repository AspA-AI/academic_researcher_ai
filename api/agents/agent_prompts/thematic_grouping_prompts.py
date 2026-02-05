"""
Thematic Grouping Agent Prompts

Prompt templates for the Thematic Grouping Agent.
"""

from typing import List, Dict, Any
from api.agents.agent_prompts.base_prompts import BaseAgentPrompts

class ThematicGroupingPrompts:
    """
    Prompt templates for the Thematic Grouping Agent.
    """
    
    @staticmethod
    def build_thematic_prompt(codes: List[Any], research_domain: str = "General",
                             supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Build the thematic grouping prompt with optional supervisor feedback integration.
        """
        # Format codes for analysis
        code_parts = BaseAgentPrompts.format_codes_for_analysis(codes, research_domain)
        
        # Build supervisor feedback section if provided
        supervisor_section = BaseAgentPrompts.get_supervisor_feedback_section(
            supervisor_feedback, previous_attempts, attempt_number, max_attempts
        )
        
        prompt = f"""As the Thematic Grouping Agent, your role is to synthesize the initial codes and identify conceptual patterns. You will propose broad academic themes and justify how the codes cluster meaningfully.

{BaseAgentPrompts.get_academic_tone_guidelines()}

---

**Objectives:**

1. **Code Pattern Recognition:** Analyze codes to detect cross-cutting motifs and patterns.
2. **Theme Proposal:** Generate preliminary themes that capture conceptual relationships between codes.
3. **Justification:** Clearly explain why certain codes were grouped under a specific theme.
4. **Scholarly Framing:** Support each theme with illustrative quotes using language that reflects academic reasoning and includes citation signals.

---

**Thematic Analysis Guidelines:**

- **Identify Conceptual Relationships:** Look for codes that share underlying concepts, theoretical frameworks, or practical applications.
- **Create Meaningful Clusters:** Group codes that, when combined, represent a coherent academic theme or research area.
- **Justify Groupings:** Provide clear academic reasoning for why codes belong together, referencing the original definitions and contexts.
- **Highlight Cross-Cutting Ideas:** Identify concepts that appear across multiple themes or that bridge different thematic areas.
- **Maintain Academic Rigor:** Use appropriate citation signals and academic language while keeping the tone accessible.

**Output Format (naming & grounding rules):**
For each theme, provide:
1. Theme name (descriptive and academic). Do **not** use purely numeric names like "1" or "Theme 1". Each theme name must be a meaningful phrase grounded in the actual codes (e.g., "Advancements in CNN Applications").
2. Theme description (what it encompasses)
3. Codes included in the theme
4. Justification for the grouping
5. Illustrative quotes or examples
6. Cross-cutting ideas or connections to other themes

{supervisor_section}

**Based on the following codes, perform thematic grouping:**

{code_parts}

Please provide structured thematic analysis results, following the guidelines above."""
        
        return prompt 