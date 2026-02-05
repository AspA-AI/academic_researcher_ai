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
class MeaningUnit:
    """Represents a meaningful unit of text for coding"""
    content: str
    source_paper: str
    source_authors: List[str]
    source_year: int
    unit_id: str
    context: str = ""
    start_position: int = 0
    end_position: int = 0

@dataclass
class Code:
    """Represents a code assigned to a meaning unit"""
    code_name: str
    definition: str
    confidence: float
    category: str = "primary"

@dataclass
class CodedUnit:
    """Represents a meaning unit with its assigned codes"""
    meaning_unit: MeaningUnit
    codes: List[Code]
    harvard_citation: str
    insights: List[str] = None

class InitialCodingAgent:
    """
    Conducts open coding on the retrieved academic text to break down content into meaningful units and assign descriptive labels (codes) with citations.
    """
    def __init__(self, llm_backend=None):
        # Initialize with OpenAI backend by default
        self.llm_backend = llm_backend or get_llm_backend("openai")
        self.code_dictionary = {}  # Track codes for consistency
        self.citation_database = {}  # Track citations

    def _segment_documents(self, documents: List[Dict[str, Any]]) -> List[MeaningUnit]:
        """
        Segment documents into meaningful units for coding.
        """
        meaning_units = []
        unit_counter = 0
        
        for doc in documents:
            content = doc.get('extracted_content', '') or doc.get('content', '')
            if not content:
                continue
            
            # Handle authors
            authors = doc.get('authors', [])
            if isinstance(authors, list):
                author_names = []
                for author in authors:
                    if isinstance(author, dict):
                        author_names.append(author.get('name', str(author)))
                    else:
                        author_names.append(str(author))
            else:
                author_names = [str(authors)]
            
            # Segment content into meaningful units (paragraphs or concept blocks)
            paragraphs = self._split_into_paragraphs(content)
            
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) < 50:  # Skip very short paragraphs
                    continue
                
                unit_id = f"unit_{unit_counter:04d}"
                unit_counter += 1
                
                meaning_unit = MeaningUnit(
                    content=paragraph.strip(),
                    source_paper=doc.get('title', 'Unknown'),
                    source_authors=author_names,
                    source_year=doc.get('year', 2024),
                    unit_id=unit_id,
                    context=f"Paragraph {i+1} from {doc.get('title', 'Unknown')}",
                    start_position=content.find(paragraph),
                    end_position=content.find(paragraph) + len(paragraph)
                )
                
                meaning_units.append(meaning_unit)
        
        print(f"[DEBUG] Segmented {len(documents)} documents into {len(meaning_units)} meaning units")
        return meaning_units

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """
        Split content into meaningful paragraphs or concept blocks.
        """
        # Split by double newlines first (paragraphs)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # If paragraphs are too long, split by single newlines
        refined_paragraphs = []
        for paragraph in paragraphs:
            if len(paragraph) > 1000:  # If paragraph is too long
                lines = [line.strip() for line in paragraph.split('\n') if line.strip()]
                refined_paragraphs.extend(lines)
            else:
                refined_paragraphs.append(paragraph)
        
        return refined_paragraphs

    def _build_coding_prompt(self, meaning_units: List[MeaningUnit], research_domain: str = "General",
                            supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Construct a prompt for the LLM to perform open coding.
        """
        from api.agents.agent_prompts.initial_coding_prompts import InitialCodingPrompts
        
        return InitialCodingPrompts.build_coding_prompt(
            meaning_units=meaning_units,
            research_domain=research_domain,
            supervisor_feedback=supervisor_feedback,
            previous_attempts=previous_attempts,
            attempt_number=attempt_number,
            max_attempts=max_attempts
        )

    def _parse_coding_response(self, response: str, meaning_units: List[MeaningUnit]) -> List[CodedUnit]:
        """
        Parse the LLM response into structured coded units.
        """
        coded_units = []
        
        # Try different section splitting patterns
        section_patterns = [
            "### Unit ",  # Markdown format
            "Unit ",      # Plain format
            "Unit:",      # With colon
            "**Unit ID**",  # Bold format
            "Unit ID",    # Plain format
        ]
        
        sections = []
        for pattern in section_patterns:
            if pattern in response:
                sections = response.split(pattern)
                break
        
        if not sections:
            print(f"[WARNING] No unit sections found in response")
            return coded_units
        
        for section in sections[1:]:  # Skip first empty section
            try:
                # Extract unit ID - try multiple patterns
                lines = section.split('\n')
                first_line = lines[0].strip()
                print(f"[DEBUG] Processing first line: '{first_line}'")
                
                unit_id = None
                
                # First, try to find unit_XXXX pattern in the entire section
                import re
                section_text = section.strip()
                unit_match = re.search(r'unit_\d+', section_text)
                if unit_match:
                    unit_id = unit_match.group()
                    print(f"[DEBUG] Extracted unit_id from section regex: '{unit_id}'")
                else:
                    # Try different ID extraction patterns from first line
                    if '(' in first_line and ')' in first_line:
                        # Extract content between parentheses
                        content_in_parens = first_line.split('(')[1].split(')')[0]
                        print(f"[DEBUG] Content in parentheses: '{content_in_parens}'")
                        
                        # If it contains "ID:", extract the unit ID
                        if 'ID:' in content_in_parens:
                            unit_id = content_in_parens.split('ID:')[1].strip()
                            print(f"[DEBUG] Extracted unit_id from parentheses with ID: '{unit_id}'")
                        else:
                            unit_id = content_in_parens
                            print(f"[DEBUG] Extracted unit_id from parentheses: '{unit_id}'")
                    elif 'ID:' in first_line:
                        # Handle format like "**Unit ID:** unit_0000"
                        if '**' in first_line:
                            # Extract everything after the last **
                            parts = first_line.split('**')
                            if len(parts) >= 3:
                                unit_id = parts[-1].strip()
                                # Clean up any remaining colons or spaces
                                unit_id = unit_id.replace(':', '').strip()
                                print(f"[DEBUG] Extracted unit_id from markdown ID pattern: '{unit_id}' from line: '{first_line}'")
                            else:
                                # Handle case where we have "ID:** unit_0000"
                                unit_id = first_line.split('ID:')[1].strip()
                                # Remove any extra text after the unit ID
                                if ' ' in unit_id:
                                    unit_id = unit_id.split(' ')[0]
                                # Clean up any remaining ** or other markdown
                                unit_id = unit_id.replace('**', '').replace('*', '').strip()
                                print(f"[DEBUG] Extracted unit_id from 'ID:' pattern: '{unit_id}' from line: '{first_line}'")
                        else:
                            unit_id = first_line.split('ID:')[1].strip()
                            # Remove any extra text after the unit ID
                            if ' ' in unit_id:
                                unit_id = unit_id.split(' ')[0]
                            print(f"[DEBUG] Extracted unit_id from 'ID:' pattern: '{unit_id}' from line: '{first_line}'")
                    elif 'unit_' in first_line:
                        # Extract unit_XXXX pattern
                        match = re.search(r'unit_\d+', first_line)
                        if match:
                            unit_id = match.group()
                            print(f"[DEBUG] Extracted unit_id from regex pattern: '{unit_id}'")
                    elif '**Unit ID**' in first_line:
                        # Handle bold format: **Unit ID**: unit_0000
                        if ':' in first_line:
                            unit_id = first_line.split(':')[1].strip()
                            print(f"[DEBUG] Extracted unit_id from bold format: '{unit_id}'")
                    else:
                        print(f"[DEBUG] No ID pattern matched for line: '{first_line}'")
                
                if not unit_id:
                    print(f"[WARNING] Could not extract unit ID from: {first_line}")
                    continue
                
                # Find corresponding meaning unit
                meaning_unit = next((mu for mu in meaning_units if mu.unit_id == unit_id), None)
                if not meaning_unit:
                    print(f"[WARNING] Could not find meaning unit for ID: {unit_id}")
                    continue
                
                # Parse codes and citations from the section
                codes = self._extract_codes_from_section(section)
                
                # Fallback: if no codes extracted, try to extract from the full section content
                if not codes:
                    print(f"[DEBUG] No codes extracted from section, trying fallback extraction...")
                    codes = self._extract_codes_fallback(section)
                
                harvard_citation = self._generate_harvard_citation(meaning_unit)
                insights = self._extract_insights_from_section(section)
                
                coded_unit = CodedUnit(
                    meaning_unit=meaning_unit,
                    codes=codes,
                    harvard_citation=harvard_citation,
                    insights=insights
                )
                
                coded_units.append(coded_unit)
                print(f"[DEBUG] Successfully parsed unit {unit_id} with {len(codes)} codes")
                
            except Exception as e:
                print(f"[WARNING] Failed to parse section for unit: {e}")
                continue
        
        return coded_units

    def _extract_codes_from_section(self, section: str) -> List[Code]:
        """
        Extract codes from a section of the LLM response.
        """
        codes = []
        lines = section.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for code patterns - handle both markdown and plain formats
            if any(keyword in line.lower() for keyword in ['code', 'concept', 'theme', 'primary', 'sub', 'governance', 'consensus', 'decentralized']):
                try:
                    # Handle markdown format: **Primary Code:** definition
                    if '**' in line and ':**' in line:
                        # Extract code name from markdown
                        code_part = line.split('**')[1].split(':**')[0]
                        definition_part = line.split(':**')[1].strip() if ':**' in line else ""
                        
                        # Clean up code name - remove common prefixes
                        code_name = code_part
                        if 'Primary Code' in code_name:
                            code_name = code_name.replace('Primary Code', '').strip()
                        elif 'Sub-code' in code_name:
                            code_name = code_name.replace('Sub-code', '').strip()
                        elif 'Code' in code_name:
                            code_name = code_name.replace('Code', '').strip()
                        
                        # If code_name is empty or just whitespace, skip this line
                        if not code_name or code_name.strip() == '':
                            continue
                        
                        definition = definition_part
                        
                        print(f"[DEBUG] Markdown parsing - code_part: '{code_part}', code_name: '{code_name}', definition: '{definition[:50]}...'")
                        
                    # Handle plain format: Code: definition
                    elif ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            code_name = parts[0].replace('Code:', '').replace('Primary Code:', '').replace('Sub-code:', '').strip()
                            definition = parts[1].strip()
                        else:
                            continue
                    else:
                        continue
                    
                    # Additional fallback: if we still don't have a proper code name, try to extract from the line
                    if not code_name or code_name.strip() == '' or code_name.strip() == ':':
                        # Try to extract a meaningful code name from the definition
                        if definition:
                            # Take the first few words as the code name
                            words = definition.split()[:3]
                            code_name = ' '.join(words)
                            print(f"[DEBUG] Fallback code name extraction: '{code_name}' from definition")
                        else:
                            continue
                    
                    # Skip if no code name or definition
                    if not code_name or not definition:
                        continue
                    
                    # Extract confidence if present
                    confidence = 0.8  # Default confidence
                    if 'confidence' in line.lower():
                        try:
                            import re
                            conf_match = re.search(r'confidence[:\s]*([0-9.]+)', line.lower())
                            if conf_match:
                                confidence = float(conf_match.group(1))
                        except:
                            pass
                    
                    # Determine category
                    category = "primary" if any(word in line.lower() for word in ["primary", "main"]) else "sub"
                    
                    code = Code(
                        code_name=code_name,
                        definition=definition,
                        confidence=confidence,
                        category=category
                    )
                    codes.append(code)
                    print(f"[DEBUG] Extracted code: '{code_name}' ({category}) - Definition: '{definition[:50]}...'")
                    
                except Exception as e:
                    print(f"[WARNING] Failed to parse code line: {line}, error: {e}")
                    continue
        
        return codes

    def _generate_harvard_citation(self, meaning_unit: MeaningUnit) -> str:
        """
        Generate Harvard-style citation for a meaning unit.
        """
        if not meaning_unit.source_authors:
            return f"({meaning_unit.source_paper}, {meaning_unit.source_year})"
        
        # Use first author's last name
        first_author = meaning_unit.source_authors[0]
        if isinstance(first_author, str):
            # Extract last name (assume it's the last word)
            last_name = first_author.split()[-1] if ' ' in first_author else first_author
        else:
            last_name = str(first_author)
        
        return f"({last_name}, {meaning_unit.source_year})"

    def _extract_insights_from_section(self, section: str) -> List[str]:
        """
        Extract insights from a section of the LLM response.
        """
        insights = []
        lines = section.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for insight patterns
            if any(keyword in line.lower() for keyword in ['insight', 'pattern', 'finding', 'observe', 'note']):
                insights.append(line)
        
        return insights[:3]  # Limit to top 3 insights

    def _extract_codes_fallback(self, section: str) -> List[Code]:
        """
        Fallback method to extract codes from section content when standard parsing fails.
        """
        codes = []
        lines = section.split('\n')
        
        # Look for lines that contain code-like content in a topic-agnostic way
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for simple "Code: definition" style lines or markdown-style labeled lines
            if line.lower().startswith("code") or line.lower().startswith("primary code") or line.lower().startswith("sub-code"):
                try:
                    # Normalize and split on the first colon
                    if ':' in line:
                        label, definition_part = line.split(':', 1)
                        code_name = (
                            label.replace('Primary Code', '')
                                 .replace('Sub-code', '')
                                 .replace('Sub-Code', '')
                                 .replace('Code', '')
                                 .strip()
                        )
                        definition = definition_part.strip()
                    else:
                        continue

                    if not code_name:
                        # Use first few words of the definition as a fallback code name
                        words = definition.split()
                        code_name = ' '.join(words[:3]).strip()

                    if code_name and definition:
                        code = Code(
                            code_name=code_name,
                            definition=definition,
                            confidence=0.8,
                            category="primary" if "primary" in line.lower() else "sub"
                        )
                        codes.append(code)
                        print(f"[DEBUG] Fallback extracted generic code: '{code_name}'")

                except Exception as e:
                    print(f"[WARNING] Fallback code extraction failed for line: {line}, error: {e}")
                    continue
        
        return codes

    def _create_coding_summary(self, coded_units: List[CodedUnit]) -> Dict[str, Any]:
        """
        Create a summary of the coding process and results.
        """
        # Collect all unique codes
        all_codes = []
        for unit in coded_units:
            all_codes.extend(unit.codes)
        
        # Count code frequencies
        code_frequencies = {}
        for code in all_codes:
            code_name = code.code_name
            if code_name in code_frequencies:
                code_frequencies[code_name]['count'] += 1
                code_frequencies[code_name]['confidence_sum'] += code.confidence
            else:
                code_frequencies[code_name] = {
                    'count': 1,
                    'confidence_sum': code.confidence,
                    'definition': code.definition,
                    'category': code.category
                }
        
        # Calculate average confidence for each code
        for code_name, data in code_frequencies.items():
            data['avg_confidence'] = data['confidence_sum'] / data['count']
        
        # Sort codes by frequency
        sorted_codes = sorted(code_frequencies.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return {
            "total_units_coded": len(coded_units),
            "unique_codes_generated": len(code_frequencies),
            "code_frequencies": dict(sorted_codes[:20]),  # Top 20 codes
            "primary_codes": [name for name, data in sorted_codes if data['category'] == 'primary'][:10],
            "sub_codes": [name for name, data in sorted_codes if data['category'] == 'sub'][:10],
            "average_confidence": sum(code.confidence for unit in coded_units for code in unit.codes) / len(all_codes) if all_codes else 0.0
        }

    async def run(self, documents: List[Dict[str, Any]], research_domain: str = "General",
                 supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> Dict[str, Any]:
        """
        Main entry point for initial coding.
        Args:
            documents (List[Dict]): List of academic documents (with extracted content).
            research_domain (str): The research domain/topic.
        Returns:
            Dict: Structured coding results with codes, citations, and summary.
        """
        if not documents:
            return {"error": "No documents provided for initial coding."}
        
        print(f"[DEBUG] InitialCodingAgent.run called with {len(documents)} documents")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        try:
            # Step 1: Segment documents into meaning units
            print(f"[DEBUG] Step 1: Segmenting documents into meaning units...")
            meaning_units = self._segment_documents(documents)
            
            if not meaning_units:
                return {"error": "No meaningful units could be extracted from documents."}
            
            # Step 2: Build coding prompt
            print(f"[DEBUG] Step 2: Building coding prompt...")
            prompt = self._build_coding_prompt(meaning_units, research_domain, supervisor_feedback, previous_attempts, attempt_number, max_attempts)
            print(f"[DEBUG] Generated prompt length: {len(prompt)} characters")
            
            if not self.llm_backend:
                return {"error": "No LLM backend provided."}
            
            print(f"[DEBUG] Using LLM backend: {self.llm_backend.get_model_info()}")
            
            # Step 3: Perform open coding using LLM
            print(f"[DEBUG] Step 3: Performing open coding...")
            llm_response = await self.llm_backend.generate(prompt)
            print(f"[DEBUG] LLM response received, length: {len(llm_response)} characters")
            
            if not llm_response:
                return {"error": "LLM generation failed: No response received."}
            
            # Step 4: Parse coding results
            print(f"[DEBUG] Step 4: Parsing coding results...")
            print(f"[DEBUG] LLM Response preview: {llm_response[:500]}...")
            coded_units = self._parse_coding_response(llm_response, meaning_units)
            print(f"[DEBUG] Parsed {len(coded_units)} coded units")
            
            # Step 5: Create coding summary
            print(f"[DEBUG] Step 5: Creating coding summary...")
            coding_summary = self._create_coding_summary(coded_units)
            
            # Step 6: Prepare final result
            final_result = {
                "coding_summary": coding_summary,
                "coded_units": [
                    {
                        "unit_id": unit.meaning_unit.unit_id,
                        "content": unit.meaning_unit.content,
                        "source": unit.meaning_unit.source_paper,
                        "authors": unit.meaning_unit.source_authors,
                        "year": unit.meaning_unit.source_year,
                        "codes": [
                            {
                                "name": code.code_name,
                                "definition": code.definition,
                                "confidence": code.confidence,
                                "category": code.category
                            } for code in unit.codes
                        ],
                        "harvard_citation": unit.harvard_citation,
                        "insights": unit.insights or []
                    } for unit in coded_units
                ],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "documents_analyzed": len(documents),
                "research_domain": research_domain
            }
            
            print(f"[DEBUG] Initial coding completed successfully!")
            print(f"[DEBUG] Final result contains {len(coded_units)} coded units and {coding_summary['unique_codes_generated']} unique codes")
            
            return final_result
            
        except Exception as e:
            print(f"[ERROR] Initial coding failed: {e}")
            return {"error": f"Initial coding failed: {str(e)}"} 