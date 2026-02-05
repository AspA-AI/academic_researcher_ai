"""
Literature Review Agent Prompts

Prompt templates for the Literature Review Agent.
"""

from typing import List, Dict, Any
from api.agents.agent_prompts.base_prompts import BaseAgentPrompts

class RetriverValidationPrompts:
    """
    Prompt templates for the Retriver Validation Agent.
    """
    
    @staticmethod
    def build_retriver_validation_prompt(documents: List[Dict[str, Any]], research_domain: str = "General", 
                                     query=None) -> str:
        """
        Build the Retriver Validation Agent.
        """
        # Format document content
        content_parts = BaseAgentPrompts.format_document_content(documents, research_domain)
        user_query = query
        prompt = f"""You are a Retrieval Validation Agent for an academic research system.

                Your job is to evaluate whether retrieved documents are relevant to a user's query
                AND whether the user's query is academically valid.

                User Query:
                {user_query}

                Retrieved Documents:
                {content_parts}

                Return ONLY valid JSON.
                Response should be:
                {{
                    "retrieval_validation": {{
                        "is_related": true,
                        "relevance_confidence": 0.0,
                        "reason": "string",
                        "failure_type": "none | weak_match | unrelated_content"
                    }},
                    "academic_feasibility": {{
                        "is_academic_query": true,
                        "academic_probability": 0.0,
                        "reason": "string",
                        "likely_sources": ["arXiv", "CoreAPI", "PubMed", "Other"]
                    }},
                    "system_recommendation": {{
                        "action": "proceed_to_literature_review | retry_retrieval | trigger_data_extraction | stop_non_academic | stop_no_results",
                        "explanation": "string"
                    }}
                }}
                """

        
        return prompt 