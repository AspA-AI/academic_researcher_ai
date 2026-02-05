"""
Report route handlers for the Research Pipeline API.
Contains endpoints for report generation and management.
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Optional

# Add the parent directory to the path for imports

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse, FileResponse
from fastapi.responses import StreamingResponse
import io

from api.models.requests import ReportRequest
from api.models.responses import (
    ReportResponse, ReportListResponse, ReportDownloadResponse, ReportStatisticsResponse
)
from api.models.format_models import FormatTransformRequest, FormatTransformResponse
from api.services.report_service import ReportService
from api.agents.format_transformation_agent import FormatTransformationAgent

router = APIRouter()

# Initialize report service
report_service = ReportService()

# Initialize format transformation agent
transformation_agent = FormatTransformationAgent()

@router.post("/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate a new academic report from pipeline sections.
    
    This endpoint creates a comprehensive academic report:
    - Combines all pipeline outputs (literature review, coding, themes, etc.)
    - Generates structured academic paper with proper sections
    - Includes citations and references
    - Saves report to local storage
    """
    try:
        if not request.sections:
            raise HTTPException(
                status_code=400,
                detail="Pipeline sections are required for report generation"
            )
        
        result = await report_service.generate_report(
            sections=request.sections,
            pipeline_id=request.pipeline_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Report generation failed: {result.get('error', 'Unknown error')}"
            )
        
        response = ReportResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

@router.get("/", response_model=ReportListResponse)
async def list_reports(
    limit: int = Query(20, ge=1, le=100, description="Number of reports to return"),
    research_domain: Optional[str] = Query(None, description="Filter by research domain"),
    pipeline_id: Optional[str] = Query(None, description="Filter by pipeline ID")
):
    """
    List all generated reports with optional filtering.
    
    Returns a list of reports with basic information:
    - Report ID and pipeline association
    - Research domain and generation date
    - Word count and reference count
    - Status and metadata
    """
    try:
        result = report_service.list_reports(
            limit=limit,
            research_domain=research_domain,
            pipeline_id=pipeline_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list reports: {result.get('error', 'Unknown error')}"
            )
        
        response = ReportListResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reports: {str(e)}"
        )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_details(
    report_id: str = Path(..., description="Unique report identifier")
):
    """
    Get detailed information about a specific report.
    
    Returns comprehensive report information including:
    - Report metadata and statistics
    - Pipeline association and research domain
    - Section breakdown and content preview
    - File path and storage information
    """
    try:
        result = report_service.get_report_details(report_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {report_id}"
            )
        
        response = ReportResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get report details: {str(e)}"
        )

@router.get("/{report_id}/download", response_model=ReportDownloadResponse)
async def download_report(
    report_id: str = Path(..., description="Unique report identifier"),
    format: str = Query("markdown", description="Download format (markdown, json, text)")
):
    """
    Download a report in the specified format.
    
    Returns the report content in the requested format:
    - **markdown**: Formatted markdown with sections and citations
    - **json**: Structured JSON with all report data
    - **text**: Plain text version of the report
    """
    try:
        result = report_service.download_report(report_id, format)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {report_id}"
            )
        
        response = ReportDownloadResponse(
            success=True,
            data=result["data"],
            format=format,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download report: {str(e)}"
        )

@router.get("/{report_id}/file")
async def download_report_file(
    report_id: str = Path(..., description="Unique report identifier"),
    format: str = Query("markdown", description="File format (markdown, pdf, docx)")
):
    """
    Download report as a file attachment.
    
    Returns the report as a downloadable file:
    - **markdown**: .md file with proper formatting
    - **pdf**: PDF version (if available)
    - **docx**: Word document (if available)
    """
    try:
        result = report_service.get_report_file_path(report_id, format)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Report file not found: {report_id}"
            )
        
        file_path = result["data"]["file_path"]
        filename = result["data"]["filename"]
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Report file not found on disk: {filename}"
            )
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download report file: {str(e)}"
        )

@router.delete("/{report_id}")
async def delete_report(
    report_id: str = Path(..., description="Unique report identifier")
):
    """
    Delete a report and its associated files.
    
    This will permanently remove the report and all associated files.
    Use with caution as this action cannot be undone.
    """
    try:
        result = report_service.delete_report(report_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {report_id}"
            )
        
        return {
            "success": True,
            "message": f"Report {report_id} deleted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete report: {str(e)}"
        )

@router.get("/statistics/overview", response_model=ReportStatisticsResponse)
async def get_report_statistics():
    """
    Get comprehensive report statistics.
    
    Returns statistics about all generated reports including:
    - Total reports and word counts
    - Research domain distribution
    - Average report metrics
    - Recent activity trends
    """
    try:
        result = report_service.get_report_statistics()
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get report statistics: {result.get('error', 'Unknown error')}"
            )
        
        response = ReportStatisticsResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get report statistics: {str(e)}"
        )

@router.post("/{report_id}/regenerate", response_model=ReportResponse)
async def regenerate_report(
    report_id: str = Path(..., description="Unique report identifier"),
    sections: Optional[dict] = None
):
    """
    Regenerate a report with updated sections.
    
    This allows you to regenerate a report with new or updated pipeline sections.
    Useful when pipeline outputs have been improved or corrected.
    """
    try:
        result = await report_service.regenerate_report(report_id, sections)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Report regeneration failed: {result.get('error', 'Unknown error')}"
            )
        
        response = ReportResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report regeneration failed: {str(e)}"
        )

@router.get("/{report_id}/preview", response_model=ReportResponse)
async def get_report_preview(
    report_id: str = Path(..., description="Unique report identifier"),
    max_length: int = Query(1000, ge=100, le=5000, description="Maximum preview length")
):
    """
    Get a preview of the report content.
    
    Returns a preview of the report content with specified length limit.
    Useful for displaying report summaries without downloading the full content.
    """
    try:
        result = report_service.get_report_preview(report_id, max_length)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {report_id}"
            )
        
        response = ReportResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get report preview: {str(e)}"
        )

@router.post("/{report_id}/export")
async def export_report(
    report_id: str = Path(..., description="Unique report identifier"),
    format: str = Query("pdf", description="Export format (pdf, docx, html)")
):
    """
    Export a report to a different format.
    
    Converts the report to the specified format:
    - **pdf**: Professional PDF document
    - **docx**: Microsoft Word document
    - **html**: Web-ready HTML format
    """
    try:
        result = await report_service.export_report(report_id, format)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Report export failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "message": f"Report exported successfully to {format}",
            "data": result["data"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report export failed: {str(e)}"
        )

@router.get("/templates/available", response_model=ReportResponse)
async def get_available_templates():
    """
    Get available report templates.
    
    Returns information about available report templates including:
    - Template names and descriptions
    - Format specifications
    - Customization options
    """
    try:
        result = report_service.get_available_templates()
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get templates: {result.get('error', 'Unknown error')}"
            )
        
        response = ReportResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get templates: {str(e)}"
        )

@router.post("/{report_id}/share")
async def share_report(
    report_id: str = Path(..., description="Unique report identifier"),
    share_method: str = Query("link", description="Share method (link, email, api)")
):
    """
    Share a report using the specified method.
    
    Creates shareable links or sends reports via different methods:
    - **link**: Generate a shareable URL
    - **email**: Send report via email
    - **api**: Return report data for API integration
    """
    try:
        result = report_service.share_report(report_id, share_method)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Report sharing failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "message": f"Report shared successfully via {share_method}",
            "data": result["data"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report sharing failed: {str(e)}"
        )

@router.post("/transform", response_model=FormatTransformResponse)
async def transform_report_format(request: FormatTransformRequest):
    """
    Transform a canonical report JSON into format-specific structure.
    
    This endpoint uses LLM to intelligently restructure report content
    for optimal presentation in the target format:
    
    - **pptx**: Converts to slide deck structure with bullet points
    - **html**: Creates HTML-friendly structure with semantic sections
    - **pdf**: Maintains canonical structure (already PDF-optimized)
    - **docx**: Creates Word document structure with proper headings
    
    The transformation preserves all content while optimizing for the target format.
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔄 Transform request received: format={request.targetFormat}")
        
        # Validate format
        valid_formats = ["pptx", "html", "pdf", "docx"]
        if request.targetFormat.lower() not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
        # Transform using LLM agent
        logger.info("🔄 Calling transformation agent...")
        transformed_data = await transformation_agent.transform(
            canonical_report=request.report,
            target_format=request.targetFormat.lower()
        )
        logger.info(f"✅ Transformation complete. Has error: {'error' in transformed_data}")
        
        # Check for errors in transformation
        if "error" in transformed_data:
            logger.warning(f"⚠️ Transformation had error: {transformed_data.get('error')}")
            return FormatTransformResponse(
                success=False,
                format=request.targetFormat.lower(),
                data=transformed_data.get("fallback", request.report),
                error=transformed_data.get("error", "Transformation failed")
            )
        
        logger.info("✅ Returning successful transformation")
        return FormatTransformResponse(
            success=True,
            format=request.targetFormat.lower(),
            data=transformed_data,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Format transformation failed: {str(e)}"
        ) 