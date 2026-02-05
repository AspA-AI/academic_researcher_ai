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
class Code:
    """Represents a code from the Initial Coding Agent"""
    name: str
    definition: str
    confidence: float
    category: str
    frequency: int = 1
    source_citations: List[str] = None

@dataclass
class Theme:
    """Represents a thematic cluster of codes"""
    theme_name: str
    description: str
    codes: List[Code]
    justification: str
    illustrative_quotes: List[str]
    cross_cutting_ideas: List[str]
    academic_reasoning: str

class ThematicGroupingAgent:
    """
    Clusters individual codes into broader conceptual themes, offering justification for groupings and identifying cross-cutting ideas.
    """
    def __init__(self, llm_backend=None):
        # Initialize with OpenAI backend by default
        self.llm_backend = llm_backend or get_llm_backend("openai")

    def _prepare_codes_for_analysis(self, coded_units: List[Dict[str, Any]]) -> List[Code]:
        """
        Extract and prepare codes from coded units for thematic analysis.
        """
        code_dict = {}  # Track unique codes and their frequencies
        
        for unit in coded_units:
            unit_codes = unit.get('codes', [])
            for code_data in unit_codes:
                code_name = code_data.get('name', '')
                if not code_name:
                    continue
                
                if code_name in code_dict:
                    # Update existing code
                    code_dict[code_name]['frequency'] += 1
                    if unit.get('harvard_citation'):
                        code_dict[code_name]['source_citations'].append(unit['harvard_citation'])
                else:
                    # Create new code entry
                    code_dict[code_name] = {
                        'name': code_name,
                        'definition': code_data.get('definition', ''),
                        'confidence': code_data.get('confidence', 0.8),
                        'category': code_data.get('category', 'primary'),
                        'frequency': 1,
                        'source_citations': [unit.get('harvard_citation', '')] if unit.get('harvard_citation') else []
                    }
        
        # Convert to Code objects
        codes = []
        for code_data in code_dict.values():
            code = Code(
                name=code_data['name'],
                definition=code_data['definition'],
                confidence=code_data['confidence'],
                category=code_data['category'],
                frequency=code_data['frequency'],
                source_citations=code_data['source_citations']
            )
            codes.append(code)
        
        print(f"[DEBUG] Prepared {len(codes)} unique codes for thematic analysis")
        return codes

    def _build_thematic_prompt(self, codes: List[Code], research_domain: str = "General",
                              supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Construct a prompt for the LLM to perform thematic grouping.
        """
        from api.agents.agent_prompts.thematic_grouping_prompts import ThematicGroupingPrompts
        
        return ThematicGroupingPrompts.build_thematic_prompt(
            codes=codes,
            research_domain=research_domain,
            supervisor_feedback=supervisor_feedback,
            previous_attempts=previous_attempts,
            attempt_number=attempt_number,
            max_attempts=max_attempts
        )

    def _parse_thematic_response(self, response: str, codes: List[Code]) -> List[Theme]:
        """
        Parse the LLM response into structured thematic clusters.
        """
        themes = []
        
        # Try different section splitting patterns for themes
        section_patterns = [
            "### Theme ",  # Markdown format
            "Theme ",      # Plain format
            "Theme:",      # With colon
        ]
        
        sections = []
        for pattern in section_patterns:
            if pattern in response:
                sections = response.split(pattern)
                break
        
        if not sections:
            print(f"[WARNING] No theme sections found in response")
            return themes
        
        for section in sections[1:]:  # Skip first empty section
            try:
                lines = section.split('\n')
                first_line = lines[0].strip()
                
                # Extract theme name - handle different formats
                if ':' in first_line:
                    theme_name = first_line.split(':')[1].strip() if len(first_line.split(':')) > 1 else first_line.split(':')[0].strip()
                else:
                    theme_name = first_line.strip()
                
                # Clean up theme name
                if theme_name.startswith('Name'):
                    theme_name = theme_name.replace('Name', '').strip()
                if theme_name.startswith('Theme'):
                    theme_name = theme_name.replace('Theme', '').strip()
                
                # Parse theme content
                theme_description = ""
                included_codes = []
                justification = ""
                illustrative_quotes = []
                cross_cutting_ideas = []
                academic_reasoning = ""
                
                current_section = None
                
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Detect section headers
                    if any(keyword in line.lower() for keyword in ['description', 'what it encompasses']):
                        current_section = 'description'
                    elif any(keyword in line.lower() for keyword in ['codes', 'included']):
                        current_section = 'codes'
                    elif any(keyword in line.lower() for keyword in ['justification', 'why']):
                        current_section = 'justification'
                    elif any(keyword in line.lower() for keyword in ['quotes', 'examples']):
                        current_section = 'quotes'
                    elif any(keyword in line.lower() for keyword in ['cross-cutting', 'connections']):
                        current_section = 'cross_cutting'
                    elif any(keyword in line.lower() for keyword in ['reasoning', 'academic']):
                        current_section = 'reasoning'
                    elif current_section and line:
                        # Add content to current section
                        if current_section == 'description':
                            theme_description += line + " "
                        elif current_section == 'codes':
                            # Extract code names from the line
                            code_names = self._extract_code_names(line)
                            included_codes.extend(code_names)
                            if code_names:
                                print(f"[DEBUG] Extracted codes from line: {code_names}")
                        elif current_section == 'justification':
                            justification += line + " "
                        elif current_section == 'quotes':
                            illustrative_quotes.append(line)
                        elif current_section == 'cross_cutting':
                            cross_cutting_ideas.append(line)
                        elif current_section == 'reasoning':
                            academic_reasoning += line + " "
                
                # Clean up descriptions
                theme_description = theme_description.strip()
                justification = justification.strip()
                academic_reasoning = academic_reasoning.strip()
                
                # Find actual Code objects for included codes
                theme_codes = []
                for code_name in included_codes:
                    matching_code = next((code for code in codes if code.name.lower() in code_name.lower() or code_name.lower() in code.name.lower()), None)
                    if matching_code:
                        theme_codes.append(matching_code)
                
                # Create Theme object
                theme = Theme(
                    theme_name=theme_name,
                    description=theme_description,
                    codes=theme_codes,
                    justification=justification,
                    illustrative_quotes=illustrative_quotes,
                    cross_cutting_ideas=cross_cutting_ideas,
                    academic_reasoning=academic_reasoning
                )
                
                themes.append(theme)
                print(f"[DEBUG] Successfully parsed theme: {theme_name} with {len(theme_codes)} codes")
                
            except Exception as e:
                print(f"[WARNING] Failed to parse theme section: {e}")
                continue
        
        return themes

    def _extract_code_names(self, text: str) -> List[str]:
        """
        Extract code names from text using various patterns.
        """
        code_names = []
        
        # Look for quoted code names
        import re
        quoted_codes = re.findall(r'"([^"]+)"', text)
        code_names.extend(quoted_codes)
        
        # Look for numbered lists (1. Code name)
        numbered_codes = re.findall(r'\d+\.\s*([^,\n]+)', text)
        code_names.extend(numbered_codes)
        
        # Look for bullet points (- Code name)
        bullet_codes = re.findall(r'-\s*([^,\n]+)', text)
        code_names.extend(bullet_codes)
        
        # Look for code names after "Code:" or similar patterns
        code_patterns = [
            r'Code:\s*([^,\n]+)',
            r'Codes:\s*([^,\n]+)',
            r'Included:\s*([^,\n]+)',
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, text)
            code_names.extend(matches)
        
        # Clean up code names
        cleaned_names = []
        for name in code_names:
            name = name.strip()
            # Remove common prefixes/suffixes
            name = re.sub(r'^(Code|Codes|Included):\s*', '', name)
            name = name.strip()
            if name and len(name) > 2:  # Filter out very short names
                cleaned_names.append(name)
        
        return cleaned_names

    def _create_thematic_summary(self, themes: List[Theme]) -> Dict[str, Any]:
        """
        Create a summary of the thematic analysis.
        """
        total_codes_analyzed = sum(len(theme.codes) for theme in themes)
        unique_codes = set()
        for theme in themes:
            for code in theme.codes:
                unique_codes.add(code.name)
        
        # Identify most common themes (by number of codes)
        theme_sizes = [(theme.theme_name, len(theme.codes)) for theme in themes]
        theme_sizes.sort(key=lambda x: x[1], reverse=True)
        
        # Collect cross-cutting ideas
        all_cross_cutting = []
        for theme in themes:
            all_cross_cutting.extend(theme.cross_cutting_ideas)
        
        return {
            "total_themes_generated": len(themes),
            "total_codes_analyzed": total_codes_analyzed,
            "unique_codes_clustered": len(unique_codes),
            "theme_sizes": dict(theme_sizes),
            "cross_cutting_ideas": all_cross_cutting[:10],  # Top 10
            "average_codes_per_theme": total_codes_analyzed / len(themes) if themes else 0
        }

    async def run(self, coded_units: List[Dict[str, Any]], research_domain: str = "General",
                 supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> Dict[str, Any]:
        """
        Main entry point for thematic grouping.
        Args:
            coded_units (List[Dict]): List of coded units from Initial Coding Agent.
            research_domain (str): The research domain/topic.
        Returns:
            Dict: Structured thematic analysis with themes, justifications, and summary.
        """
        if not coded_units:
            return {"error": "No coded units provided for thematic analysis."}
        
        print(f"[DEBUG] ThematicGroupingAgent.run called with {len(coded_units)} coded units")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        try:
            # Step 1: Prepare codes for analysis
            print(f"[DEBUG] Step 1: Preparing codes for thematic analysis...")
            codes = self._prepare_codes_for_analysis(coded_units)
            
            if not codes:
                return {"error": "No codes could be extracted from coded units."}
            
            # Step 2: Build thematic analysis prompt
            print(f"[DEBUG] Step 2: Building thematic analysis prompt...")
            prompt = self._build_thematic_prompt(codes, research_domain, supervisor_feedback, previous_attempts, attempt_number, max_attempts)
            print(f"[DEBUG] Generated prompt length: {len(prompt)} characters")
            
            if not self.llm_backend:
                return {"error": "No LLM backend provided."}
            
            print(f"[DEBUG] Using LLM backend: {self.llm_backend.get_model_info()}")
            
            # Step 3: Perform thematic grouping using LLM
            print(f"[DEBUG] Step 3: Performing thematic grouping...")
            llm_response = await self.llm_backend.generate(prompt)
            print(f"[DEBUG] LLM response received, length: {len(llm_response)} characters")
            
            if not llm_response:
                return {"error": "LLM generation failed: No response received."}
            
            # Step 4: Parse thematic results
            print(f"[DEBUG] Step 4: Parsing thematic results...")
            print(f"[DEBUG] LLM Response preview: {llm_response[:500]}...")
            themes = self._parse_thematic_response(llm_response, codes)
            print(f"[DEBUG] Parsed {len(themes)} themes")
            
            # Step 5: Create thematic summary
            print(f"[DEBUG] Step 5: Creating thematic summary...")
            thematic_summary = self._create_thematic_summary(themes)
            
            # Step 6: Prepare final result
            final_result = {
                "thematic_summary": thematic_summary,
                "themes": [
                    {
                        "theme_name": theme.theme_name,
                        "description": theme.description,
                        "codes": [
                            {
                                "name": code.name,
                                "definition": code.definition,
                                "frequency": code.frequency,
                                "category": code.category,
                                "confidence": code.confidence
                            } for code in theme.codes
                        ],
                        "justification": theme.justification,
                        "illustrative_quotes": theme.illustrative_quotes,
                        "cross_cutting_ideas": theme.cross_cutting_ideas,
                        "academic_reasoning": theme.academic_reasoning
                    } for theme in themes
                ],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "coded_units_analyzed": len(coded_units),
                "research_domain": research_domain
            }
            
            print(f"[DEBUG] Thematic grouping completed successfully!")
            print(f"[DEBUG] Final result contains {len(themes)} themes and {thematic_summary['total_codes_analyzed']} codes analyzed")
            
            return final_result
            
        except Exception as e:
            print(f"[ERROR] Thematic grouping failed: {e}")
            return {"error": f"Thematic grouping failed: {str(e)}"} 