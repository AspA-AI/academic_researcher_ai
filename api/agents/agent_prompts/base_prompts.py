"""
Base Agent Prompts

Common prompt components and tone guidelines used across all agents.
"""

class BaseAgentPrompts:
    """
    Base prompt components and guidelines for all agents.
    """
    
    @staticmethod
    def get_academic_tone_guidelines() -> str:
        """
        Get the standard academic tone guidelines used across all agents.
        """
        return """The tone should be academic but casual and spartan. Down to earth. Avoid Jargon. Generously use expressions like: "More often than not", "It can be argued that", "In effect", "Ideally", "We can infer", etc. Equally use expressions like "Generally speaking," or "We can infer that..." when introducing insights, while remaining faithful to the literature."""
    
    @staticmethod
    def get_harvard_citation_guidelines() -> str:
        """
        Get Harvard-style citation guidelines.
        """
        return """**Use the following format for Harvard-style citations:**

**In-text citation examples:**
- Narrative: According to Mason (2020), transparency is central to building trust in blockchain ecosystems.
- Parenthetical: Transparency is often linked to user empowerment in decentralized systems (O'Reilly, 2019).

**Reference List format (used at the end of the paper):**
- Mason, J. (2020). *The Role of Trust in Blockchain Technology*. Journal of Digital Innovation, 12(3), pp.45–58.
- O'Reilly, T. (2019). *The Open Future: Transparency in a Decentralized Internet*. Web3 Journal, 7(1), pp.12–29.

Ensure that all in-text citations match entries that would be added to the reference list."""
    
    @staticmethod
    def get_common_transitional_phrases() -> str:
        """
        Get common transitional phrases for academic writing.
        """
        return """Use transitional phrases such as: "Furthermore", "Ideally", "We can infer", "It is to say that", and "In effect" to enhance clarity, scholarly tone, and readability."""
    
    @staticmethod
    def format_document_content(documents: list, research_domain: str) -> str:
        """
        Format document content for prompts.
        """
        content_parts = [
            f"Research Domain: {research_domain}",
            f"Number of Papers Analyzed: {len(documents)}",
            "\n=== PAPERS AND CONTENT ===\n"
        ]
        
        for i, paper in enumerate(documents, 1):
            authors = paper.get('authors', [])
            if isinstance(authors, list):
                author_names = []
                for author in authors:
                    if isinstance(author, dict):
                        author_names.append(author.get('name', str(author)))
                    else:
                        author_names.append(str(author))
                authors_str = ', '.join(author_names)
            else:
                authors_str = str(authors)
            
            content_parts.extend([
                f"Paper {i}:",
                f"Title: {paper.get('title', 'Unknown')}",
                f"Authors: {authors_str}",
                f"Year: {paper.get('year', 'Unknown')}",
                f"Abstract: {paper.get('abstract', 'No abstract available')}",
                f"Content Length: {len(paper.get('extracted_content', ''))} chars",
                f"Extracted Content: {paper.get('extracted_content', 'No content extracted')[:2000]}...",
                "\n" + "="*50 + "\n"
            ])
        
        return chr(10).join(content_parts)
    
    @staticmethod
    def format_meaning_units(meaning_units: list, research_domain: str) -> str:
        """
        Format meaning units for coding prompts.
        """
        content_parts = [
            f"Research Domain: {research_domain}",
            f"Number of Meaning Units to Code: {len(meaning_units)}",
            "\n=== MEANING UNITS FOR CODING ===\n"
        ]
        
        for i, unit in enumerate(meaning_units, 1):
            authors_str = ', '.join(unit.source_authors)
            content_parts.extend([
                f"Unit {i} (ID: {unit.unit_id}):",
                f"Source: {unit.source_paper}",
                f"Authors: {authors_str}",
                f"Year: {unit.source_year}",
                f"Content: {unit.content}",
                "\n" + "-"*40 + "\n"
            ])
        
        return chr(10).join(content_parts)
    
    @staticmethod
    def format_codes_for_analysis(codes: list, research_domain: str) -> str:
        """
        Format codes for thematic analysis prompts.
        """
        code_parts = [
            f"Research Domain: {research_domain}",
            f"Number of Unique Codes to Analyze: {len(codes)}",
            "\n=== CODES FOR THEMATIC ANALYSIS ===\n"
        ]
        
        # Sort codes by frequency for better analysis
        sorted_codes = sorted(codes, key=lambda x: x.frequency, reverse=True)
        
        for i, code in enumerate(sorted_codes, 1):
            citations_str = ', '.join(code.source_citations) if code.source_citations else 'No citations'
            code_parts.extend([
                f"Code {i}: {code.name}",
                f"   Definition: {code.definition}",
                f"   Category: {code.category}",
                f"   Frequency: {code.frequency}",
                f"   Confidence: {code.confidence}",
                f"   Citations: {citations_str}",
                "\n" + "-"*40 + "\n"
            ])
        
        return chr(10).join(code_parts)
    
    @staticmethod
    def get_supervisor_feedback_section(supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Build supervisor feedback section for enhanced prompts.
        """
        if not supervisor_feedback:
            return ""
        
        # Handle both string (enhanced context) and object (full supervisor feedback) cases
        if isinstance(supervisor_feedback, str):
            # Enhanced context string from retry service
            supervisor_section = f"""
**SUPERVISOR FEEDBACK:**
Status: REVISE
Quality Score: Needs improvement
Purpose Alignment: Needs improvement
Issues Found: Quality below acceptable threshold
Improvement Suggestions: {supervisor_feedback}
Enhanced Context: {supervisor_feedback}
"""
        else:
            # Full supervisor feedback object from supervisor agent
            supervisor_section = f"""
**SUPERVISOR FEEDBACK:**
Status: {supervisor_feedback.status}
Quality Score: {supervisor_feedback.quality_score}
Purpose Alignment: {supervisor_feedback.purpose_alignment_score}
Issues Found: {', '.join(supervisor_feedback.issues_found)}
Improvement Suggestions: {', '.join(supervisor_feedback.improvement_suggestions)}
Enhanced Context: {supervisor_feedback.enhanced_context_prompt}
"""
        
        # Build previous attempts analysis
        if previous_attempts and isinstance(previous_attempts, dict):
            previous_analysis = f"""
**PREVIOUS ATTEMPT ISSUES:**
{previous_attempts.get('issues', 'None identified')}

**WHAT NEEDS IMPROVEMENT:**
{previous_attempts.get('improvements_needed', 'None specified')}
"""
        else:
            previous_analysis = ""
        
        # Build attempt information
        if isinstance(supervisor_feedback, str):
            # For string feedback, use it directly as improvement requirement
            improvement_requirements = f"- {supervisor_feedback}"
        else:
            # For object feedback, use improvement suggestions
            improvement_requirements = chr(10).join([f"- {suggestion}" for suggestion in supervisor_feedback.improvement_suggestions]) if supervisor_feedback.improvement_suggestions else "None specified"
        
        attempt_info = f"""
**ATTEMPT:** {attempt_number}/{max_attempts}

**IMPROVEMENT REQUIREMENTS:**
{improvement_requirements}
"""
        
        return f"{supervisor_section}{previous_analysis}{attempt_info}" 