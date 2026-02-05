"""
Quality Service - Manages supervisor operations and quality control workflows.
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the path to import agents

from api.agents.supervisor_agent import SupervisorAgent, QualityAssessment

class QualityService:
    """
    Service layer for managing quality control operations and supervisor workflows.
    """
    
    def __init__(self):
        """Initialize quality service."""
        self.supervisor_agent = SupervisorAgent()
        
        # Track quality assessments
        self.quality_history = []
        
        # Quality thresholds (configurable)
        self.quality_thresholds = {
            "literature_review": {"min_score": 0.6, "halt_threshold": 0.3},
            "initial_coding": {"min_score": 0.6, "halt_threshold": 0.3},
            "thematic_grouping": {"min_score": 0.6, "halt_threshold": 0.3},
            "theme_refinement": {"min_score": 0.6, "halt_threshold": 0.3},
            "report_generation": {"min_score": 0.7, "halt_threshold": 0.4}
        }
    
    async def check_quality(self, agent_output: Dict[str, Any], agent_type: str, research_domain: str = "General") -> Dict[str, Any]:
        """
        Check quality of agent output using supervisor.
        
        Args:
            agent_output: Output from an agent to check
            agent_type: Type of agent that produced the output
            research_domain: Research domain/topic
            
        Returns:
            Dict containing quality assessment results
        """
        try:
            # Generate assessment ID
            assessment_id = str(uuid.uuid4())
            
            # Log assessment start
            self.quality_history.append({
                "assessment_id": assessment_id,
                "agent_type": agent_type,
                "research_domain": research_domain,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running"
            })
            
            # Perform quality assessment
            assessment = await self.supervisor_agent.check_quality(agent_output, agent_type, research_domain)

            # Normalize quality_score to a consistent 0.0-1.0 scale.
            # The SupervisorAgent historically returns a 0-10 score in some prompts, while our thresholds are 0-1.
            raw_quality_score = float(getattr(assessment, "quality_score", 0.0) or 0.0)
            normalized_quality_score = raw_quality_score
            if normalized_quality_score > 1.0:
                normalized_quality_score = normalized_quality_score / 10.0
            # Clamp to [0,1] to keep downstream logic stable
            normalized_quality_score = max(0.0, min(1.0, normalized_quality_score))
            assessment.quality_score = normalized_quality_score
            
            # Get thresholds for this agent type
            thresholds = self.quality_thresholds.get(agent_type, {"min_score": 0.6, "halt_threshold": 0.3})
            
            # Determine action based on quality score and thresholds (fallback only)
            threshold_action = self._determine_action(assessment.quality_score, thresholds)

            # Prefer the supervisor's explicit decision when available (keeps status/action consistent)
            recommended_action = assessment.status if assessment.status in ("APPROVE", "REVISE", "HALT") else threshold_action
            
            # Update assessment history
            for hist in self.quality_history:
                if hist["assessment_id"] == assessment_id:
                    hist["status"] = "completed"
                    hist["quality_score"] = assessment.quality_score
                    hist["supervisor_status"] = assessment.status
                    hist["recommended_action"] = recommended_action
                    hist["confidence"] = assessment.confidence
                    break
            
            return {
                "success": True,
                "data": {
                    "assessment_id": assessment_id,
                    "agent_type": agent_type,
                    "research_domain": research_domain,
                    "quality_score": assessment.quality_score,
                    "raw_quality_score": raw_quality_score,
                    "supervisor_status": assessment.status,
                    "recommended_action": recommended_action,
                    "confidence": assessment.confidence,
                    "feedback": assessment.feedback,
                    "action": assessment.action,
                    "issues_found": assessment.issues_found,
                    "thresholds": thresholds
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            # Update assessment history
            for hist in self.quality_history:
                if hist.get("assessment_id") == assessment_id:
                    hist["status"] = "failed"
                    hist["error"] = str(e)
                    break
            
            return {
                "success": False,
                "error": str(e),
                "assessment_id": assessment_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def assess_quality(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess quality of agent output (alias for check_quality for route compatibility).
        
        Args:
            request_data: Dictionary containing agent_output, agent_type, and research_domain
            
        Returns:
            Dict containing quality assessment results
        """
        agent_output = request_data.get("agent_output", {})
        agent_type = request_data.get("agent_type", "general")
        research_domain = request_data.get("research_domain", "General")
        
        return await self.check_quality(agent_output, agent_type, research_domain)
    
    def _determine_action(self, quality_score: float, thresholds: Dict[str, float]) -> str:
        """
        Determine recommended action based on quality score and thresholds.
        
        Args:
            quality_score: Quality score from supervisor
            thresholds: Quality thresholds for the agent type
            
        Returns:
            Recommended action: "APPROVE", "REVISE", or "HALT"
        """
        min_score = thresholds.get("min_score", 0.6)
        halt_threshold = thresholds.get("halt_threshold", 0.3)
        
        if quality_score >= min_score:
            return "APPROVE"
        elif quality_score >= halt_threshold:
            return "REVISE"
        else:
            return "HALT"
    
    async def approve_output(self, assessment_id: str, user_notes: str = "") -> Dict[str, Any]:
        """
        Manually approve an output (override supervisor decision).
        
        Args:
            assessment_id: ID of the assessment to approve
            user_notes: Optional notes from user
            
        Returns:
            Dict containing approval results
        """
        try:
            # Find the assessment in history
            assessment = None
            for hist in self.quality_history:
                if hist.get("assessment_id") == assessment_id:
                    assessment = hist
                    break
            
            if not assessment:
                return {
                    "success": False,
                    "error": f"Assessment {assessment_id} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Update assessment with manual approval
            assessment["manual_override"] = True
            assessment["manual_action"] = "APPROVE"
            assessment["user_notes"] = user_notes
            assessment["override_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            return {
                "success": True,
                "data": {
                    "assessment_id": assessment_id,
                    "action": "APPROVE",
                    "user_notes": user_notes,
                    "original_quality_score": assessment.get("quality_score"),
                    "original_supervisor_status": assessment.get("supervisor_status")
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def reject_output(self, assessment_id: str, user_notes: str = "") -> Dict[str, Any]:
        """
        Manually reject an output (override supervisor decision).
        
        Args:
            assessment_id: ID of the assessment to reject
            user_notes: Optional notes from user
            
        Returns:
            Dict containing rejection results
        """
        try:
            # Find the assessment in history
            assessment = None
            for hist in self.quality_history:
                if hist.get("assessment_id") == assessment_id:
                    assessment = hist
                    break
            
            if not assessment:
                return {
                    "success": False,
                    "error": f"Assessment {assessment_id} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Update assessment with manual rejection
            assessment["manual_override"] = True
            assessment["manual_action"] = "REJECT"
            assessment["user_notes"] = user_notes
            assessment["override_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            return {
                "success": True,
                "data": {
                    "assessment_id": assessment_id,
                    "action": "REJECT",
                    "user_notes": user_notes,
                    "original_quality_score": assessment.get("quality_score"),
                    "original_supervisor_status": assessment.get("supervisor_status")
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_quality_history(self, limit: int = 20, agent_type: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """
        Get quality assessment history.
        
        Args:
            limit: Maximum number of assessments to return
            agent_type: Filter by agent type (optional)
            status: Filter by assessment status (optional)
            
        Returns:
            Dict containing quality history
        """
        try:
            # Filter by agent type if specified
            filtered_history = self.quality_history
            if agent_type:
                filtered_history = [h for h in self.quality_history if h.get("agent_type") == agent_type]
            
            # Filter by status if specified
            if status:
                filtered_history = [h for h in filtered_history if h.get("supervisor_status") == status]
            
            # Get recent assessments
            recent_assessments = filtered_history[-limit:] if filtered_history else []
            
            # Calculate statistics
            total_assessments = len(filtered_history)
            approved_count = len([h for h in filtered_history if h.get("supervisor_status") == "APPROVE"])
            revised_count = len([h for h in filtered_history if h.get("supervisor_status") == "REVISE"])
            halted_count = len([h for h in filtered_history if h.get("supervisor_status") == "HALT"])
            manual_overrides = len([h for h in filtered_history if h.get("manual_override")])
            
            return {
                "success": True,
                "data": {
                    "assessments": recent_assessments,
                    "statistics": {
                        "total_assessments": total_assessments,
                        "approved": approved_count,
                        "revised": revised_count,
                        "halted": halted_count,
                        "manual_overrides": manual_overrides,
                        "approval_rate": (approved_count / total_assessments * 100) if total_assessments > 0 else 0
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_quality_thresholds(self) -> Dict[str, Any]:
        """
        Get current quality thresholds.
        
        Returns:
            Dict containing quality thresholds
        """
        return {
            "success": True,
            "data": {
                "thresholds": self.quality_thresholds
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def update_quality_thresholds(self, new_thresholds: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Update quality thresholds.
        
        Args:
            new_thresholds: New threshold values
            
        Returns:
            Dict containing update results
        """
        try:
            # Validate thresholds
            for agent_type, thresholds in new_thresholds.items():
                if "min_score" not in thresholds or "halt_threshold" not in thresholds:
                    return {
                        "success": False,
                        "error": f"Invalid thresholds for {agent_type}: missing required fields",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                
                if thresholds["min_score"] <= thresholds["halt_threshold"]:
                    return {
                        "success": False,
                        "error": f"Invalid thresholds for {agent_type}: min_score must be greater than halt_threshold",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
            
            # Update thresholds
            self.quality_thresholds.update(new_thresholds)
            
            return {
                "success": True,
                "data": {
                    "updated_thresholds": new_thresholds,
                    "all_thresholds": self.quality_thresholds
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_quality_analytics(self) -> Dict[str, Any]:
        """
        Get quality analytics and trends.
        
        Returns:
            Dict containing quality analytics
        """
        try:
            # Calculate analytics
            total_assessments = len(self.quality_history)
            if total_assessments == 0:
                return {
                    "success": True,
                    "data": {
                        "message": "No quality assessments available for analytics",
                        "total_assessments": 0
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Quality score trends
            quality_scores = [h.get("quality_score", 0) for h in self.quality_history if h.get("quality_score") is not None]
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Agent type performance
            agent_performance = {}
            for agent_type in self.quality_thresholds.keys():
                agent_assessments = [h for h in self.quality_history if h.get("agent_type") == agent_type]
                if agent_assessments:
                    agent_scores = [h.get("quality_score", 0) for h in agent_assessments if h.get("quality_score") is not None]
                    agent_performance[agent_type] = {
                        "total_assessments": len(agent_assessments),
                        "average_score": sum(agent_scores) / len(agent_scores) if agent_scores else 0,
                        "approval_rate": len([h for h in agent_assessments if h.get("supervisor_status") == "APPROVE"]) / len(agent_assessments) * 100
                    }
            
            return {
                "success": True,
                "data": {
                    "total_assessments": total_assessments,
                    "average_quality_score": avg_quality_score,
                    "agent_performance": agent_performance,
                    "recent_trend": "improving" if len(quality_scores) >= 2 and quality_scores[-1] > quality_scores[-2] else "stable"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            } 