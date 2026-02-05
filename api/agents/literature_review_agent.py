import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone
import sys
import os
# Add the api directory to the path
from api.utils.llm_backends import get_llm_backend

class LiteratureReviewAgent:
    """
    Generates a standalone academic-style literature review using the documents retrieved.
    Synthesizes summary, key findings, research gaps, methodologies, etc. using an LLM backend.
    """
    def __init__(self, llm_backend=None):
        # Initialize with OpenAI backend by default
        self.llm_backend = llm_backend or get_llm_backend("openai")

    def _build_prompt(self, documents: List[Dict[str, Any]], research_domain: str = "General", 
                     supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Construct a prompt for the LLM to generate a literature review.
        """
        from api.agents.agent_prompts.literature_review_prompts import LiteratureReviewPrompts
        
        return LiteratureReviewPrompts.build_literature_review_prompt(
            documents=documents,
            research_domain=research_domain,
            supervisor_feedback=supervisor_feedback,
            previous_attempts=previous_attempts,
            attempt_number=attempt_number,
            max_attempts=max_attempts
        )

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into structured literature review format.
        """
        sections = {
            "summary": "",
            "key_findings": [],
            "research_gaps": [],
            "methodologies": [],
            "future_directions": [],
            "full_literature_review": response  # Store the complete response
        }
        
        # Try to extract structured sections from the academic literature review
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for section headers in academic literature review format
            if any(keyword in line.lower() for keyword in ['introduction', 'background', 'context']):
                current_section = 'summary'
            elif any(keyword in line.lower() for keyword in ['key findings', 'main findings', 'insights', 'synthesis']):
                current_section = 'key_findings'
            elif any(keyword in line.lower() for keyword in ['research gaps', 'gaps', 'limitations', 'opportunities']):
                current_section = 'research_gaps'
            elif any(keyword in line.lower() for keyword in ['methodologies', 'methods', 'frameworks', 'approaches']):
                current_section = 'methodologies'
            elif any(keyword in line.lower() for keyword in ['future directions', 'future research', 'recommendations', 'conclusion']):
                current_section = 'future_directions'
            elif current_section and line:
                # Add content to current section
                if current_section == 'summary':
                    sections['summary'] += line + " "
                elif current_section in ['key_findings', 'research_gaps', 'methodologies', 'future_directions']:
                    sections[current_section].append(line)
        
        # Clean up summary
        sections['summary'] = sections['summary'].strip()
        
        # If no structured sections found, use the full response as summary
        if not sections['summary'] and response:
            sections['summary'] = response[:1000] + "..." if len(response) > 1000 else response
        
        # Extract key findings from the full text if not found in sections
        if not sections['key_findings']:
            sections['key_findings'] = self._extract_key_points(response, 'findings')
        
        # Extract research gaps from the full text if not found in sections
        if not sections['research_gaps']:
            sections['research_gaps'] = self._extract_key_points(response, 'gaps')
        
        return sections
    
    def _extract_key_points(self, text: str, point_type: str) -> List[str]:
        """
        Extract key points from the full text using simple heuristics.
        """
        points = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for sentences that might contain key points
            if point_type == 'findings':
                if any(keyword in line.lower() for keyword in ['find', 'discover', 'show', 'demonstrate', 'reveal', 'indicate']):
                    points.append(line)
            elif point_type == 'gaps':
                if any(keyword in line.lower() for keyword in ['gap', 'missing', 'lack', 'need', 'future', 'limitation']):
                    points.append(line)
        
        return points[:5]  # Limit to top 5 points

    async def run(self, documents: List[Dict[str, Any]], research_domain: str = "General", 
                 supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> Dict[str, Any]:
        """
        Main entry point for literature review generation.
        Args:
            documents (List[Dict]): List of academic documents (with extracted content).
            research_domain (str): The research domain/topic.
        Returns:
            Dict: Structured literature review (summary, key findings, gaps, etc.)
        """
        if not documents:
            return {"error": "No documents provided for literature review."}
        
        print(f"[DEBUG] LiteratureReviewAgent.run called with {len(documents)} documents")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        prompt = self._build_prompt(documents, research_domain, supervisor_feedback, previous_attempts, attempt_number, max_attempts)
        print(f"[DEBUG] Generated prompt length: {len(prompt)} characters")
        
        if not self.llm_backend:
            return {"error": "No LLM backend provided."}
        
        print(f"[DEBUG] Using LLM backend: {self.llm_backend.get_model_info()}")
        
        try:
            llm_response = await self.llm_backend.generate(prompt)
            print(f"[DEBUG] LLM response received, length: {len(llm_response)} characters")
            
            if not llm_response:
                return {"error": "LLM generation failed: No response received."}
            
            structured_result = self._parse_response(llm_response)
            structured_result["generated_at"] = datetime.now(timezone.utc).isoformat()
            structured_result["documents_analyzed"] = len(documents)
            structured_result["research_domain"] = research_domain
            
            print(f"[DEBUG] Structured result created with sections: {list(structured_result.keys())}")
            return structured_result
            
        except Exception as e:
            print(f"[ERROR] Literature review generation failed: {e}")
            return {"error": f"Literature review generation failed: {str(e)}"} 