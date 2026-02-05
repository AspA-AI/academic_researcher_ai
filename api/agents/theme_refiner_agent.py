import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
import sys
import os
# Add the api directory to the path
from api.utils.llm_backends import get_llm_backend

@dataclass
class RefinedTheme:
    """Represents a refined theme with academic polish"""
    original_name: str
    refined_name: str
    precise_definition: str
    scope_boundaries: str
    academic_quotes: List[Dict[str, str]]  # List of {quote: str, citation: str}
    key_concepts: List[str]
    theoretical_framework: str
    research_implications: str

class ThemeRefinerAgent:
    """
    Finalizes each theme by writing a precise definition, scope, evocative title, and supporting academic quotes.
    """
    def __init__(self, llm_backend=None):
        # Initialize with OpenAI backend by default
        self.llm_backend = llm_backend or get_llm_backend("openai")

    def _prepare_themes_for_refinement(self, themes: List[Dict[str, Any]]) -> str:
        """
        Prepare themes data for the refinement prompt.
        """
        theme_parts = []
        
        for i, theme in enumerate(themes, 1):
            theme_parts.extend([
                f"=== THEME {i} ===",
                f"Original Name: {theme.get('theme_name', 'Unknown')}",
                f"Description: {theme.get('description', 'No description')}",
                f"Codes Included: {len(theme.get('codes', []))}",
                f"Codes: {[code.get('name', '') for code in theme.get('codes', [])]}",
                f"Justification: {theme.get('justification', 'No justification')}",
                f"Cross-cutting Ideas: {theme.get('cross_cutting_ideas', [])}",
                f"Academic Reasoning: {theme.get('academic_reasoning', 'No reasoning')}",
                "\n" + "="*50 + "\n"
            ])
        
        return "\n".join(theme_parts)

    def _build_refinement_prompt(self, themes: List[Dict[str, Any]], research_domain: str = "General",
                                supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Construct a prompt for the LLM to perform theme refinement.
        """
        from api.agents.agent_prompts.theme_refiner_prompts import ThemeRefinerPrompts
        
        return ThemeRefinerPrompts.build_refinement_prompt(
            themes=themes,
            research_domain=research_domain,
            supervisor_feedback=supervisor_feedback,
            previous_attempts=previous_attempts,
            attempt_number=attempt_number,
            max_attempts=max_attempts
        )

    def _parse_refinement_response(self, response: str, themes: List[Dict[str, Any]]) -> List[RefinedTheme]:
        """
        Parse the LLM response into structured refined themes.
        """
        refined_themes = []
        
        # Try different section splitting patterns for themes
        section_patterns = [
            "### Theme ",  # Markdown format
            "Theme ",      # Plain format
            "Theme:",      # With colon
            "=== THEME ",  # Alternative format
        ]
        
        sections = []
        for pattern in section_patterns:
            if pattern in response:
                sections = response.split(pattern)
                break
        
        if not sections:
            print(f"[WARNING] No theme sections found in response")
            return refined_themes
        
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            try:
                lines = section.split('\n')
                first_line = lines[0].strip()
                
                # Extract refined theme name
                if ':' in first_line:
                    label, value = first_line.split(':', 1)
                    # If the left-hand side looks like a generic label ("Name", "Theme"), use the right-hand side
                    if any(tok in label.lower() for tok in ["name", "theme", "title"]):
                        refined_name = value.strip()
                    else:
                        refined_name = first_line.strip()
                else:
                    refined_name = first_line.strip()
                
                # Parse theme content
                precise_definition = ""
                scope_boundaries = ""
                academic_quotes = []
                key_concepts = []
                theoretical_framework = ""
                research_implications = ""
                
                current_section = None
                
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Detect section headers
                    if any(keyword in line.lower() for keyword in ['definition', 'precise']):
                        current_section = 'definition'
                    elif any(keyword in line.lower() for keyword in ['scope', 'boundary', 'boundaries']):
                        current_section = 'scope'
                    elif any(keyword in line.lower() for keyword in ['quote', 'citation', 'evidence']):
                        current_section = 'quotes'
                    elif any(keyword in line.lower() for keyword in ['concept', 'key']):
                        current_section = 'concepts'
                    elif any(keyword in line.lower() for keyword in ['theoretical', 'framework']):
                        current_section = 'framework'
                    elif any(keyword in line.lower() for keyword in ['implication', 'research']):
                        current_section = 'implications'
                    elif current_section and line:
                        # Add content to current section
                        if current_section == 'definition':
                            precise_definition += line + " "
                        elif current_section == 'scope':
                            scope_boundaries += line + " "
                        elif current_section == 'quotes':
                            # Extract quotes and citations
                            quote_data = self._extract_quotes_and_citations(line)
                            academic_quotes.extend(quote_data)
                        elif current_section == 'concepts':
                            # Extract key concepts
                            concepts = self._extract_key_concepts(line)
                            key_concepts.extend(concepts)
                        elif current_section == 'framework':
                            theoretical_framework += line + " "
                        elif current_section == 'implications':
                            research_implications += line + " "
                
                # Clean up text fields
                precise_definition = precise_definition.strip()
                scope_boundaries = scope_boundaries.strip()
                theoretical_framework = theoretical_framework.strip()
                research_implications = research_implications.strip()
                
                # Get original theme data
                original_theme = themes[i-1] if i-1 < len(themes) else {"theme_name": "Unknown"}

                # If refined_name is empty or a generic placeholder, fall back to the original theme name
                if not refined_name or refined_name.lower() in {"name", "theme", "title"}:
                    refined_name = str(original_theme.get("theme_name", "Unknown"))
                
                # Create RefinedTheme object
                refined_theme = RefinedTheme(
                    original_name=original_theme.get("theme_name", "Unknown"),
                    refined_name=refined_name,
                    precise_definition=precise_definition,
                    scope_boundaries=scope_boundaries,
                    academic_quotes=academic_quotes,
                    key_concepts=key_concepts,
                    theoretical_framework=theoretical_framework,
                    research_implications=research_implications
                )
                
                refined_themes.append(refined_theme)
                print(f"[DEBUG] Successfully parsed refined theme: {refined_name}")
                
            except Exception as e:
                print(f"[WARNING] Failed to parse theme section {i}: {e}")
                continue
        
        return refined_themes

    def _extract_quotes_and_citations(self, text: str) -> List[Dict[str, str]]:
        """
        Extract quotes and citations from text.
        """
        quotes = []
        
        # Look for quoted text with citations
        import re
        
        # Pattern for quotes with citations: "quote" (Author, Year)
        quote_patterns = [
            r'"([^"]+)"\s*\(([^)]+)\)',
            r'([^"]+)\s*\(([^)]+)\)',  # Fallback for unquoted text
        ]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    quote_text = match[0].strip()
                    citation = match[1].strip()
                    if quote_text and citation:
                        quotes.append({
                            "quote": quote_text,
                            "citation": citation
                        })
        
        return quotes

    def _extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract key concepts from text.
        """
        concepts = []
        
        # Look for bullet points, numbered lists, or comma-separated concepts
        import re
        
        # Split by common separators
        parts = re.split(r'[,;•\-\d+\.]', text)
        
        for part in parts:
            concept = part.strip()
            if concept and len(concept) > 2:
                concepts.append(concept)
        
        return concepts[:5]  # Limit to top 5 concepts

    def _create_refinement_summary(self, refined_themes: List[RefinedTheme]) -> Dict[str, Any]:
        """
        Create a summary of the theme refinement process.
        """
        total_quotes = sum(len(theme.academic_quotes) for theme in refined_themes)
        total_concepts = sum(len(theme.key_concepts) for theme in refined_themes)
        
        return {
            "total_themes_refined": len(refined_themes),
            "total_academic_quotes": total_quotes,
            "total_key_concepts": total_concepts,
            "average_quotes_per_theme": total_quotes / len(refined_themes) if refined_themes else 0,
            "average_concepts_per_theme": total_concepts / len(refined_themes) if refined_themes else 0,
            "themes_with_framework": len([t for t in refined_themes if t.theoretical_framework]),
            "themes_with_implications": len([t for t in refined_themes if t.research_implications])
        }

    async def run(self, themes: List[Dict[str, Any]], research_domain: str = "General",
                 supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> Dict[str, Any]:
        """
        Main entry point for theme refinement.
        Args:
            themes (List[Dict]): List of raw themes from Thematic Grouping Agent.
            research_domain (str): The research domain/topic.
        Returns:
            Dict: Structured refined themes with definitions, quotes, and academic polish.
        """
        if not themes:
            return {"error": "No themes provided for refinement."}
        
        print(f"[DEBUG] ThemeRefinerAgent.run called with {len(themes)} themes")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        try:
            # Step 1: Build refinement prompt
            print(f"[DEBUG] Step 1: Building refinement prompt...")
            prompt = self._build_refinement_prompt(themes, research_domain, supervisor_feedback, previous_attempts, attempt_number, max_attempts)
            print(f"[DEBUG] Generated prompt length: {len(prompt)} characters")
            
            if not self.llm_backend:
                return {"error": "No LLM backend provided."}
            
            print(f"[DEBUG] Using LLM backend: {self.llm_backend.get_model_info()}")
            
            # Step 2: Perform theme refinement using LLM
            print(f"[DEBUG] Step 2: Performing theme refinement...")
            llm_response = await self.llm_backend.generate(prompt)
            print(f"[DEBUG] LLM response received, length: {len(llm_response)} characters")
            
            if not llm_response:
                return {"error": "LLM generation failed: No response received."}
            
            # Step 3: Parse refinement results
            print(f"[DEBUG] Step 3: Parsing refinement results...")
            print(f"[DEBUG] LLM Response preview: {llm_response[:500]}...")
            refined_themes = self._parse_refinement_response(llm_response, themes)
            print(f"[DEBUG] Parsed {len(refined_themes)} refined themes")
            
            # Step 4: Create refinement summary
            print(f"[DEBUG] Step 4: Creating refinement summary...")
            refinement_summary = self._create_refinement_summary(refined_themes)
            
            # Step 5: Prepare final result
            final_result = {
                "refinement_summary": refinement_summary,
                "refined_themes": [
                    {
                        "original_name": theme.original_name,
                        "refined_name": theme.refined_name,
                        "precise_definition": theme.precise_definition,
                        "scope_boundaries": theme.scope_boundaries,
                        "academic_quotes": theme.academic_quotes,
                        "key_concepts": theme.key_concepts,
                        "theoretical_framework": theme.theoretical_framework,
                        "research_implications": theme.research_implications
                    } for theme in refined_themes
                ],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "themes_refined": len(themes),
                "research_domain": research_domain
            }
            
            print(f"[DEBUG] Theme refinement completed successfully!")
            print(f"[DEBUG] Final result contains {len(refined_themes)} refined themes")
            
            return final_result
            
        except Exception as e:
            print(f"[ERROR] Theme refinement failed: {e}")
            return {"error": f"Theme refinement failed: {str(e)}"} 