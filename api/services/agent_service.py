"""
Agent Service - Manages individual agent operations and provides clean interfaces for API.
"""

import asyncio
from ipaddress import collapse_addresses
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the path to import agents

from api.agents.literature_review_agent import LiteratureReviewAgent
from api.agents.initial_coding_agent import InitialCodingAgent
from api.agents.thematic_grouping_agent import ThematicGroupingAgent
from api.agents.theme_refiner_agent import ThemeRefinerAgent
from api.agents.report_generator_agent import ReportGeneratorAgent
from api.agents.supervisor_agent import SupervisorAgent
from api.agents.retriever_validation_agent import RetrieverValidatorAgent
from api.agents.multi_source_data_extractor_agent import MultiSourceDataExtractorAgent

class AgentService:
    """
    Service layer for managing individual agent operations.
    Provides clean interfaces for API operations while wrapping existing agent implementations.
    """
    
    def __init__(self):
        """Initialize all agent instances."""
        self.multi_source_data_extractor_agent = MultiSourceDataExtractorAgent()
        self.retriver_validation_agent = RetrieverValidatorAgent()
        self.literature_agent = LiteratureReviewAgent()
        self.coding_agent = InitialCodingAgent()
        self.thematic_agent = ThematicGroupingAgent()
        self.refiner_agent = ThemeRefinerAgent()
        self.report_agent = ReportGeneratorAgent()
        self.supervisor_agent = SupervisorAgent()
        
        # Track agent health status
        self.agent_status = {
            "multi_source_data_extractor_agent": {"status": "ready", "last_used": None},
            "retriver_validation_agent": {"status": "ready", "last_used": None},
            "literature_review": {"status": "ready", "last_used": None},
            "initial_coding": {"status": "ready", "last_used": None},
            "thematic_grouping": {"status": "ready", "last_used": None},
            "theme_refinement": {"status": "ready", "last_used": None},
            "report_generation": {"status": "ready", "last_used": None},
            "supervisor": {"status": "ready", "last_used": None}
        }

    async def run_multi_agent_extractor(self, 
        query,
        research_domain,
        max_results,
        year_from,
        year_to,
        language,
        sources,
        enrich_with,
        per_source_limit,
        oa_only,
        auto_fallback,
        store,
        full_text,
        use_playwright_fallback
    ) -> Dict[str, Any]:
        """
        Run retriver validation agent.
        
        Args:
            documents: List of documents to analyze
            research_domain: Research domain/topic
            query: user query
            
        Returns:
            Dict containing retriver validation agent results
        """
        try:
            self.agent_status["multi_source_data_extractor_agent"]["status"] = "running"
            self.agent_status["multi_source_data_extractor_agent"]["last_used"] = datetime.now(timezone.utc)

            print("[AGENT_SERVICE][EXTRACTOR] ▶️ Starting MultiSourceDataExtractorAgent.run(...)")
            print(f"[AGENT_SERVICE][EXTRACTOR]    query='{query}' domain='{research_domain}' max_results={max_results} store={store}")

            result = await self.multi_source_data_extractor_agent.run(
                query=query,
                research_domain=research_domain,
                max_results=max_results,
                year_from=year_from,
                year_to=year_to,
                language=None,
                sources=sources,
                enrich_with=enrich_with,
                per_source_limit=per_source_limit,
                oa_only=True,
                auto_fallback=auto_fallback,
                store=store,
                full_text=full_text,
                use_playwright_fallback=use_playwright_fallback
            )

            self.agent_status["multi_source_data_extractor_agent"]["status"] = "ready"

            # Debug shape of extractor result so pipeline telemetry can be trusted
            if isinstance(result, dict):
                inner = result.get("data") if isinstance(result.get("data"), dict) else result
                print(
                    "[AGENT_SERVICE][EXTRACTOR] ✅ Extractor completed. "
                    f"top_keys={list(result.keys())} "
                    f"inner_keys={list(inner.keys()) if isinstance(inner, dict) else 'N/A'}"
                )
            else:
                print(f"[AGENT_SERVICE][EXTRACTOR] ✅ Extractor completed with non-dict result type={type(result)}")

            return {
                "success": True,
                "data": result,
                "agent_type": "multi_source_data_extractor_agent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            import traceback
            self.agent_status["multi_source_data_extractor_agent"]["status"] = "error"
            print(f"[AGENT_SERVICE][EXTRACTOR] ❌ Extractor raised exception: {e}")
            print(f"[AGENT_SERVICE][EXTRACTOR] Traceback:\n{traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": "multi_source_data_extractor_agent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def run_retriver_validation(self, query, documents: List[Dict[str, Any]], research_domain: str = "General") -> Dict[str, Any]:
        """
        Run retriver validation agent.
        
        Args:
            documents: List of documents to analyze
            research_domain: Research domain/topic
            query: user query
            
        Returns:
            Dict containing retriver validation agent results
        """
        try:
            self.agent_status["retriver_validation_agent"]["status"] = "running"
            self.agent_status["retriver_validation_agent"]["last_used"] = datetime.now(timezone.utc)
            
            result = await self.retriver_validation_agent.run(query, documents, research_domain)
            
            self.agent_status["retriver_validation_agent"]["status"] = "ready"
            return {
                "success": True,
                "data": result,
                "agent_type": "retriver_validation_agent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.agent_status["literature_review"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "retriver_validation_agent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def run_academic_feasibility(self, query: str, research_domain: str = "General") -> Dict[str, Any]:
        """
        Lightweight academic-topic check using the Retriever Validation Agent in query-only mode.
        This is used before any heavy retrieval/extraction work to decide if the query is academic.
        """
        try:
            self.agent_status["retriver_validation_agent"]["status"] = "running"
            self.agent_status["retriver_validation_agent"]["last_used"] = datetime.now(timezone.utc)

            # Call validation agent with an empty documents list; prompt will focus on academic_feasibility
            result = await self.retriver_validation_agent.run(query, [], research_domain)

            self.agent_status["retriver_validation_agent"]["status"] = "ready"
            return {
                "success": True,
                "data": result,
                "agent_type": "retriver_validation_agent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.agent_status["retriver_validation_agent"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "retriver_validation_agent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def run_literature_review(self, documents: List[Dict[str, Any]], research_domain: str = "General") -> Dict[str, Any]:
        """
        Run literature review agent.
        
        Args:
            documents: List of documents to analyze
            research_domain: Research domain/topic
            
        Returns:
            Dict containing literature review results
        """
        try:
            self.agent_status["literature_review"]["status"] = "running"
            self.agent_status["literature_review"]["last_used"] = datetime.now(timezone.utc)
            
            result = await self.literature_agent.run(documents, research_domain)
            
            self.agent_status["literature_review"]["status"] = "ready"
            return {
                "success": True,
                "data": result,
                "agent_type": "literature_review",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.agent_status["literature_review"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "literature_review",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def run_initial_coding(self, documents: List[Dict[str, Any]], research_domain: str = "General") -> Dict[str, Any]:
        """
        Run initial coding agent.
        
        Args:
            documents: List of documents to code
            research_domain: Research domain/topic
            
        Returns:
            Dict containing coding results
        """
        try:
            self.agent_status["initial_coding"]["status"] = "running"
            self.agent_status["initial_coding"]["last_used"] = datetime.now(timezone.utc)
            
            result = await self.coding_agent.run(documents, research_domain)
            
            self.agent_status["initial_coding"]["status"] = "ready"
            return {
                "success": True,
                "data": result,
                "agent_type": "initial_coding",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.agent_status["initial_coding"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "initial_coding",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def run_thematic_grouping(self, coded_units: List[Dict[str, Any]], research_domain: str = "General") -> Dict[str, Any]:
        """
        Run thematic grouping agent.
        
        Args:
            coded_units: List of coded units from initial coding
            research_domain: Research domain/topic
            
        Returns:
            Dict containing thematic grouping results
        """
        try:
            self.agent_status["thematic_grouping"]["status"] = "running"
            self.agent_status["thematic_grouping"]["last_used"] = datetime.now(timezone.utc)
            
            result = await self.thematic_agent.run(coded_units, research_domain)
            
            self.agent_status["thematic_grouping"]["status"] = "ready"
            return {
                "success": True,
                "data": result,
                "agent_type": "thematic_grouping",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.agent_status["thematic_grouping"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "thematic_grouping",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def run_theme_refinement(self, themes: List[Dict[str, Any]], research_domain: str = "General") -> Dict[str, Any]:
        """
        Run theme refinement agent.
        
        Args:
            themes: List of themes from thematic grouping
            research_domain: Research domain/topic
            
        Returns:
            Dict containing theme refinement results
        """
        try:
            self.agent_status["theme_refinement"]["status"] = "running"
            self.agent_status["theme_refinement"]["last_used"] = datetime.now(timezone.utc)
            
            result = await self.refiner_agent.run(themes, research_domain)
            
            self.agent_status["theme_refinement"]["status"] = "ready"
            return {
                "success": True,
                "data": result,
                "agent_type": "theme_refinement",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.agent_status["theme_refinement"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "theme_refinement",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def run_report_generation(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run report generation agent.
        
        Args:
            sections: Dictionary containing all pipeline sections
            
        Returns:
            Dict containing report generation results
        """
        try:
            self.agent_status["report_generation"]["status"] = "running"
            self.agent_status["report_generation"]["last_used"] = datetime.now(timezone.utc)
            
            result = await self.report_agent.run(sections)
            
            self.agent_status["report_generation"]["status"] = "ready"
            return {
                "success": True,
                "data": result,
                "agent_type": "report_generation",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.agent_status["report_generation"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "report_generation",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_quality(self, agent_output: Dict[str, Any], agent_type: str, research_domain: str = "General") -> Dict[str, Any]:
        """
        Run supervisor quality check.
        
        Args:
            agent_output: Output from an agent to check
            agent_type: Type of agent that produced the output
            research_domain: Research domain/topic
            
        Returns:
            Dict containing quality assessment results
        """
        try:
            self.agent_status["supervisor"]["status"] = "running"
            self.agent_status["supervisor"]["last_used"] = datetime.now(timezone.utc)
            
            assessment = await self.supervisor_agent.check_quality(agent_output, agent_type, research_domain)
            
            self.agent_status["supervisor"]["status"] = "ready"
            return {
                "success": True,
                "data": {
                    "status": assessment.status,
                    "quality_score": assessment.quality_score,
                    "confidence": assessment.confidence,
                    "feedback": assessment.feedback,
                    "action": assessment.action,
                    "issues_found": assessment.issues_found
                },
                "agent_type": "supervisor",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.agent_status["supervisor"]["status"] = "error"
            return {
                "success": False,
                "error": str(e),
                "agent_type": "supervisor",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents.
        
        Returns:
            Dict containing status of all agents
        """
        return {
            "success": True,
            "agents": self.agent_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_agent_health(self, agent_type: str) -> Dict[str, Any]:
        """
        Get health status of a specific agent.
        
        Args:
            agent_type: Type of agent to check
            
        Returns:
            Dict containing agent health information
        """
        if agent_type not in self.agent_status:
            return {
                "success": False,
                "error": f"Unknown agent type: {agent_type}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        agent_info = self.agent_status[agent_type]
        return {
            "success": True,
            "data": {
                "agent_type": agent_type,
                "status": agent_info["status"],
                "last_used": agent_info["last_used"].isoformat() if agent_info["last_used"] else None,
                "healthy": agent_info["status"] in ["ready", "running"]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        } 