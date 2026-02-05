"""
Agent Retry Service for handling retries with enhanced context.
"""

import asyncio
from typing import Dict, Any, Optional
from api.agents.data_extractor_agent import DataExtractorAgent
from api.agents.retriever_agent import RetrieverAgent
from api.agents.literature_review_agent import LiteratureReviewAgent
from api.agents.initial_coding_agent import InitialCodingAgent
from api.agents.thematic_grouping_agent import ThematicGroupingAgent
from api.agents.theme_refiner_agent import ThemeRefinerAgent
from api.agents.report_generator_agent import ReportGeneratorAgent


class AgentRetryService:
    """Service for retrying agents with enhanced context."""
    
    def __init__(self):
        """Initialize the retry service."""
        self.agents = {
            "data_extractor": DataExtractorAgent(),
            "retriever": RetrieverAgent(),
            "literature_review": LiteratureReviewAgent(),
            "initial_coding": InitialCodingAgent(),
            "thematic_grouping": ThematicGroupingAgent(),
            "theme_refinement": ThemeRefinerAgent(),
            "report_generator": ReportGeneratorAgent()
        }
        
        # Agent type mapping (frontend hyphenated -> backend underscore)
        self.agent_type_mapping = {
            "data-extractor": "data_extractor",
            "literature-review": "literature_review",
            "initial-coding": "initial_coding",
            "thematic-grouping": "thematic_grouping",
            "theme-refiner": "theme_refinement",
            "report-generator": "report_generator"
        }
    
    async def retry_agent(
        self, 
        agent_type: str, 
        original_input: Dict[str, Any], 
        enhanced_context: str,
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retry an agent with enhanced context.
        
        Args:
            agent_type: Type of agent to retry
            original_input: Original input sent to the agent
            enhanced_context: Enhanced context from supervisor feedback
            user_context: Additional context from user
            
        Returns:
            Agent output with enhanced context applied
        """
        # Map frontend agent type to backend agent type
        backend_agent_type = self.agent_type_mapping.get(agent_type, agent_type)
        
        if backend_agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type} (mapped to: {backend_agent_type})")
        
        agent = self.agents[backend_agent_type]
        
        # Combine enhanced context and user context
        full_context = enhanced_context
        if user_context:
            full_context += f"\n\nUser Context: {user_context}"
        
        # Extract parameters based on agent type
        retry_params = self._extract_agent_parameters(backend_agent_type, original_input, full_context)
        
        print(f"[RETRY SERVICE] Retrying {agent_type} with enhanced context")
        print(f"[RETRY SERVICE] Context: {full_context[:200]}...")
        print(f"[RETRY SERVICE] Parameters: {list(retry_params.keys())}")
        print(f"[RETRY SERVICE] Original input keys: {list(original_input.keys())}")
        print(f"[RETRY SERVICE] Documents count: {len(original_input.get('documents', []))}")
        
        # Call the agent with enhanced context
        try:
            result = await agent.run(**retry_params)
            
            print(f"[RETRY SERVICE] {agent_type} retry completed successfully")
            print(f"[RETRY SERVICE] Result type: {type(result)}")
            print(f"[RETRY SERVICE] Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check if result contains an error
            if isinstance(result, dict) and "error" in result:
                print(f"[RETRY SERVICE] Agent returned error: {result['error']}")
                return result
            
            # Ensure we always return a dictionary for AgentResponse compatibility
            if isinstance(result, dict):
                # Already a dictionary, return as is
                return result
            elif isinstance(result, list):
                # Handle list results (like retriever agent)
                if agent_type == "retriever":
                    return {
                        "documents": result,
                        "query": original_input.get("query", ""),
                        "research_domain": original_input.get("research_domain", "General"),
                        "total_documents": len(result)
                    }
                else:
                    # Generic list handling for other agents
                    return {
                        "results": result,
                        "total_items": len(result),
                        "agent_type": agent_type
                    }
            elif isinstance(result, str):
                # Handle string results
                return {
                    "content": result,
                    "agent_type": agent_type
                }
            else:
                # Handle any other type by converting to string
                return {
                    "result": str(result),
                    "agent_type": agent_type,
                    "result_type": type(result).__name__
                }
            
        except Exception as e:
            print(f"[RETRY SERVICE] Exception during agent retry: {str(e)}")
            return {"error": f"Agent retry failed: {str(e)}"}
    
    def _extract_agent_parameters(self, agent_type: str, original_input: Dict[str, Any], enhanced_context: str) -> Dict[str, Any]:
        """
        Extract the correct parameters for each agent type.
        
        Args:
            agent_type: Type of agent
            original_input: Original input
            enhanced_context: Enhanced context
            
        Returns:
            Parameters for the agent
        """
        if agent_type == "data_extractor":
            # DataExtractorAgent only accepts basic parameters, no supervisor feedback
            # Only include parameters that are actually provided in original_input
            params = {}
            
            if "query" in original_input:
                params["query"] = original_input["query"]
            if "max_results" in original_input:
                params["max_results"] = original_input["max_results"]
            if "year_from" in original_input:
                params["year_from"] = original_input["year_from"]
            if "year_to" in original_input:
                params["year_to"] = original_input["year_to"]
            if "research_domain" in original_input:
                params["research_domain"] = original_input["research_domain"]
            
            return params
        
        elif agent_type == "retriever":
            # RetrieverAgent only accepts basic parameters, no supervisor feedback
            return {
                "query": original_input.get("query", ""),
                "top_k": original_input.get("top_k", 10)
            }
        
        elif agent_type == "literature_review":
            # LiteratureReviewAgent accepts supervisor feedback
            return {
                "documents": original_input.get("documents", []),
                "research_domain": original_input.get("research_domain", "General"),
                "supervisor_feedback": enhanced_context
            }
        
        elif agent_type == "initial_coding":
            # InitialCodingAgent accepts supervisor feedback
            return {
                "documents": original_input.get("documents", []),
                "research_domain": original_input.get("research_domain", "General"),
                "supervisor_feedback": enhanced_context
            }
        
        elif agent_type == "thematic_grouping":
            # ThematicGroupingAgent accepts supervisor feedback
            return {
                "coded_units": original_input.get("coded_units", []),
                "research_domain": original_input.get("research_domain", "General"),
                "supervisor_feedback": enhanced_context
            }
        
        elif agent_type == "theme_refinement":
            # ThemeRefinerAgent accepts supervisor feedback
            return {
                "themes": original_input.get("themes", []),
                "research_domain": original_input.get("research_domain", "General"),
                "supervisor_feedback": enhanced_context
            }
        
        elif agent_type == "report_generator":
            # ReportGeneratorAgent accepts supervisor feedback
            return {
                "sections": original_input.get("sections", {}),
                "research_domain": original_input.get("research_domain", "General"),
                "supervisor_feedback": enhanced_context
            }
        
        else:
            # Fallback: pass all original input
            return {**original_input} 