"""
Data Extractor Agent Prompts

Prompt templates for the Data Extractor Agent.
Note: The data extractor currently uses API calls rather than LLM prompts,
but this structure is prepared for future enhancements.
"""

from typing import List, Dict, Any
from api.agents.agent_prompts.base_prompts import BaseAgentPrompts

class DataExtractorPrompts:
    """
    Prompt templates for the Data Extractor Agent.
    """
    
    @staticmethod
    def build_search_query_prompt(user_query: str, research_domain: str = "General",
                                 supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Build a prompt for optimizing search queries (future enhancement).
        """
        # Build supervisor feedback section if provided
        supervisor_section = BaseAgentPrompts.get_supervisor_feedback_section(
            supervisor_feedback, previous_attempts, attempt_number, max_attempts
        )
        
        prompt = f"""As the Data Extractor Agent, your task is to optimize search queries for academic document retrieval.

**Original Query:** {user_query}
**Research Domain:** {research_domain}

**Objectives:**
1. **Query Optimization**: Enhance the search query for better academic document retrieval
2. **Domain-Specific Terms**: Add relevant academic terminology
3. **Search Strategy**: Suggest search parameters and filters
4. **Source Selection**: Recommend academic databases and sources

{supervisor_section}

**Please provide optimized search parameters and strategies for academic document retrieval.**"""
        
        return prompt
    
    @staticmethod
    def build_document_filtering_prompt(documents: List[Dict[str, Any]], research_domain: str = "General",
                                       supervisor_feedback=None, previous_attempts=None, attempt_number=1, max_attempts=3) -> str:
        """
        Build a prompt for filtering and ranking documents (future enhancement).
        """
        # Build supervisor feedback section if provided
        supervisor_section = BaseAgentPrompts.get_supervisor_feedback_section(
            supervisor_feedback, previous_attempts, attempt_number, max_attempts
        )
        
        # Format documents for review
        docs_info = []
        for i, doc in enumerate(documents, 1):
            docs_info.append(f"""Document {i}:
Title: {doc.get('title', 'Unknown')}
Authors: {', '.join(doc.get('authors', []))}
Year: {doc.get('year', 'Unknown')}
Abstract: {doc.get('abstract', 'No abstract')[:200]}...
Source: {doc.get('source', 'Unknown')}
""")
        
        docs_text = "\n".join(docs_info)
        
        prompt = f"""As the Data Extractor Agent, your task is to filter and rank retrieved documents for relevance and quality.

**Research Domain:** {research_domain}
**Number of Documents:** {len(documents)}

**Objectives:**
1. **Relevance Assessment**: Evaluate how well each document matches the research query
2. **Quality Filtering**: Assess the academic quality and credibility of sources
3. **Ranking**: Order documents by relevance and importance
4. **Diversity**: Ensure coverage of different aspects and perspectives

{supervisor_section}

**Documents to Evaluate:**
{docs_text}

**Please provide relevance scores and filtering recommendations for each document.**"""
        
        return prompt 