"""
Quality control route handlers for the Research Pipeline API.
Contains endpoints for supervisor agent operations and quality management.
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Optional

# Add the parent directory to the path for imports

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from api.models.requests import QualityRequest, QualityOverrideRequest, QualityThresholdsRequest
from api.models.responses import (
    QualityResponse, QualityHistoryResponse, QualityAnalyticsResponse, ErrorResponse, SuccessResponse
)
from api.models.agents import AgentType
from api.services.quality_service import QualityService

router = APIRouter()

# Initialize quality service
quality_service = QualityService()

@router.post("/assess", response_model=QualityResponse)
async def assess_quality(request: QualityRequest):
    """
    Assess the quality of agent output using the supervisor agent.
    
    This endpoint evaluates the quality of agent outputs and provides:
    - Quality score (0.0-1.0)
    - Supervisor decision (APPROVE, REVISE, HALT)
    - Detailed feedback and issues
    - Recommended actions
    """
    try:
        # Convert request to service format
        request_data = {
            "agent_output": request.agent_output,
            "agent_type": request.agent_type.value,
            "research_domain": request.research_domain
        }
        
        result = await quality_service.assess_quality(request_data)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Quality assessment failed: {result.get('error', 'Unknown error')}"
            )
        
        assessment_data = result["data"]
        
        response = QualityResponse(
            success=True,
            assessment_id=assessment_data["assessment_id"],
            data=assessment_data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quality assessment failed: {str(e)}"
        )

@router.post("/override", response_model=QualityResponse)
async def override_quality_assessment(request: QualityOverrideRequest):
    """
    Override a quality assessment decision.
    
    This allows manual override of supervisor decisions when needed.
    Useful for cases where the supervisor's decision needs to be overridden
    based on human judgment or specific requirements.
    """
    try:
        result = quality_service.override_assessment(
            request.assessment_id,
            request.user_notes
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Assessment not found: {request.assessment_id}"
            )
        
        response = QualityResponse(
            success=True,
            assessment_id=request.assessment_id,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Override failed: {str(e)}"
        )

@router.get("/thresholds", response_model=QualityResponse)
async def get_quality_thresholds():
    """
    Get current quality thresholds for all agent types.
    
    Returns the current threshold configuration including:
    - Minimum quality scores for each agent type
    - Halt thresholds for automatic stopping
    - Custom threshold settings
    """
    try:
        result = quality_service.get_quality_thresholds()
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get thresholds: {result.get('error', 'Unknown error')}"
            )
        
        response = QualityResponse(
            success=True,
            assessment_id="thresholds",
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quality thresholds: {str(e)}"
        )

@router.put("/thresholds", response_model=QualityResponse)
async def update_quality_thresholds(request: QualityThresholdsRequest):
    """
    Update quality thresholds for agent types.
    
    Allows customization of quality thresholds for different agent types.
    This affects how the supervisor agent makes decisions about
    approving, revising, or halting pipeline steps.
    """
    try:
        result = quality_service.update_quality_thresholds(request.thresholds)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update thresholds: {result.get('error', 'Unknown error')}"
            )
        
        response = QualityResponse(
            success=True,
            assessment_id="thresholds_updated",
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update quality thresholds: {str(e)}"
        )

@router.get("/history", response_model=QualityHistoryResponse)
async def get_quality_history(
    limit: int = Query(20, ge=1, le=100, description="Number of assessments to return"),
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by assessment status")
):
    """
    Get quality assessment history.
    
    Returns a history of quality assessments including:
    - Assessment details and decisions
    - Quality scores and feedback
    - Timestamps and agent types
    - Statistics and trends
    """
    try:
        result = quality_service.get_quality_history(
            limit=limit,
            agent_type=agent_type.value if agent_type else None,
            status=status
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get quality history: {result.get('error', 'Unknown error')}"
            )
        
        response = QualityHistoryResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quality history: {str(e)}"
        )

@router.get("/analytics", response_model=QualityAnalyticsResponse)
async def get_quality_analytics(
    time_period: str = Query("7d", description="Time period for analytics (e.g., '7d', '30d', '90d')")
):
    """
    Get quality analytics and trends.
    
    Returns comprehensive analytics including:
    - Quality score trends over time
    - Agent performance comparisons
    - Approval rates and patterns
    - Quality improvement recommendations
    """
    try:
        result = quality_service.get_quality_analytics(time_period)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get quality analytics: {result.get('error', 'Unknown error')}"
            )
        
        response = QualityAnalyticsResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quality analytics: {str(e)}"
        )

@router.get("/{assessment_id}", response_model=QualityResponse)
async def get_assessment_details(
    assessment_id: str = Path(..., description="Unique assessment identifier")
):
    """
    Get detailed information about a specific quality assessment.
    
    Returns complete assessment details including:
    - Original agent output
    - Quality evaluation criteria
    - Supervisor feedback and reasoning
    - Override information if applicable
    """
    try:
        result = quality_service.get_assessment_details(assessment_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Assessment not found: {assessment_id}"
            )
        
        response = QualityResponse(
            success=True,
            assessment_id=assessment_id,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assessment details: {str(e)}"
        )

@router.delete("/{assessment_id}")
async def delete_assessment(
    assessment_id: str = Path(..., description="Unique assessment identifier")
):
    """
    Delete a quality assessment.
    
    Removes the assessment from the quality control history.
    This is useful for cleaning up test assessments or correcting errors.
    """
    try:
        result = quality_service.delete_assessment(assessment_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Assessment not found: {assessment_id}"
            )
        
        return {
            "success": True,
            "message": f"Assessment {assessment_id} deleted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete assessment: {str(e)}"
        )

@router.post("/batch-assess", response_model=List[QualityResponse])
async def batch_assess_quality(
    requests: List[QualityRequest]
):
    """
    Perform batch quality assessment for multiple agent outputs.
    
    This endpoint allows you to assess multiple agent outputs at once,
    which is useful for bulk processing or comparing multiple results.
    """
    try:
        results = []
        
        for request in requests:
            request_data = {
                "agent_output": request.agent_output,
                "agent_type": request.agent_type.value,
                "research_domain": request.research_domain
            }
            
            result = await quality_service.assess_quality(request_data)
            
            if result["success"]:
                response = QualityResponse(
                    success=True,
                    assessment_id=result["data"]["assessment_id"],
                    data=result["data"],
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                results.append(response)
            else:
                # Create error response for failed assessment
                error_response = QualityResponse(
                    success=False,
                    assessment_id="failed",
                    data={"error": result.get("error", "Unknown error")},
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                results.append(error_response)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch assessment failed: {str(e)}"
        )

@router.get("/supervisor/status", response_model=QualityResponse)
async def get_supervisor_status():
    """
    Get the current status of the supervisor agent.
    
    Returns supervisor agent information including:
    - Current status and health
    - Performance metrics
    - Configuration settings
    - Recent activity
    """
    try:
        result = quality_service.get_supervisor_status()
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get supervisor status: {result.get('error', 'Unknown error')}"
            )
        
        response = QualityResponse(
            success=True,
            assessment_id="supervisor_status",
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supervisor status: {str(e)}"
        ) 