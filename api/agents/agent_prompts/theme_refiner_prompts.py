"""
Theme Refiner Agent Prompts

Prompt templates for the Theme Refiner Agent.
"""

from typing import List, Dict, Any
from api.agents.agent_prompts.base_prompts import BaseAgentPrompts

class ThemeRefinerPrompts:
    """
    Prompt templates for the Theme Refiner Agent.
    """
    
    @staticmethod
    def build_refinement_prompt(themes: List[Dict[str, Any]], research_domain: str = "General",
                               supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Build the theme refinement prompt with optional supervisor feedback integration.
        """
        # Prepare themes data
        themes_data = ThemeRefinerPrompts._prepare_themes_for_refinement(themes)
        
        # Build supervisor feedback section if provided
        supervisor_section = BaseAgentPrompts.get_supervisor_feedback_section(
            supervisor_feedback, previous_attempts, attempt_number, max_attempts
        )
        
        prompt = f"""As the Theme Definition & Refinement Agent, you will finalize the themes by articulating them in formal academic language. Your deliverable includes refined theme names, clear definitions, scope boundaries, and illustrative quotes with Harvard-style citations.

{BaseAgentPrompts.get_academic_tone_guidelines()}
Use an academic tone enriched with contextual phrases like "More often than not…", "To unpack…", and "It can be argued that…"

---

**Objectives:**

1. **Precise Theme Definitions:** Write concise and clear academic definitions of each theme.
2. **Evocative Naming:** Title themes with compelling, conceptually accurate labels. You must **preserve and refine** each theme’s original name; never replace it with a bare number (e.g., "1", "2") or other meaningless placeholder.
3. **Boundary Setting:** Delimit the scope of each theme to prevent overlap.
4. **Quotations:**  You MUST provide at least two strong academic quotes or paraphrases (with citations) to exemplify each theme.

---

**Refinement Guidelines (naming & grounding):**

- **Academic Precision:** Use formal academic language while maintaining accessibility
- **Conceptual Clarity:** Ensure each theme has a clear, distinct conceptual focus
- **Scope Definition:** Clearly define what is included and excluded from each theme
- **Citation Rigor:** Provide at least 2 supporting quotes with proper Harvard-style citations
- **Grounding:** Draw all quotes and citations from the material implied by the input themes and their underlying coded units. Do **not** invent generic placeholders such as "Source A" or fictitious author names/years; if you lack precise citation details, reuse or adapt the citation patterns already present in the themes.
- **Theoretical Grounding:** Connect themes to relevant theoretical frameworks
- **Research Implications:** Highlight how each theme contributes to the research domain

**Output Format:**
For each theme, provide:
1. Refined theme name (evocative and precise)
2. Precise academic definition
3. Scope boundaries (what's included/excluded)
4. At least 2 supporting academic quotes with citations
5. Key concepts within the theme
6. Theoretical framework connections
7. Research implications

**Research Domain:** {research_domain}

{supervisor_section}

**Based on the following themes, perform refinement:**

{themes_data}

Please provide structured theme refinement results, following the guidelines above."""
        
        return prompt
    
    @staticmethod
    def _prepare_themes_for_refinement(themes: List[Dict[str, Any]]) -> str:
        """
        Prepare themes data for refinement prompt.
        """
        themes_data = []
        
        for i, theme in enumerate(themes, 1):
            theme_name = theme.get('theme_name', f'Themes {i}')
            description = theme.get('description', 'No description available')
            codes = theme.get('codes', [])
            
            # Format codes
            codes_str = ""
            if codes:
                codes_str = "\n   Codes included:\n"
                for code in codes:
                    if isinstance(code, dict):
                        code_name = code.get('name', 'Unknown code')
                        code_def = code.get('definition', 'No definition')
                        codes_str += f"   - {code_name}: {code_def}\n"
                    else:
                        codes_str += f"   - {str(code)}\n"
            
            # Format illustrative quotes
            quotes = theme.get('illustrative_quotes', [])
            quotes_str = ""
            if quotes:
                quotes_str = "\n   Illustrative quotes:\n"
                for quote in quotes:
                    quotes_str += f"   - {quote}\n"
            
            theme_data = f"""=== THEME {i}: {theme_name} ===
Description: {description}{codes_str}{quotes_str}
"""
            themes_data.append(theme_data)
        
        return "\n".join(themes_data) 