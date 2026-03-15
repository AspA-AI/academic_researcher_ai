"""
Pipeline route handlers for the Research Pipeline API.
Contains endpoints for pipeline management and execution.
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Optional

# Add the parent directory to the path for imports

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse, FileResponse

from api.models.requests import PipelineRequest
from api.models.responses import (
    PipelineResponse, PipelineProgressResponse, PipelineResultsResponse,
    PipelineStatisticsResponse, ErrorResponse, SuccessResponse
)
from api.models.responses import PipelineStatus
from api.services.pipeline_service import PipelineService

router = APIRouter()

# Initialize pipeline service
pipeline_service = PipelineService()

@router.post("/")
async def start_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new research pipeline.
    
    This endpoint initiates a complete research pipeline that includes:
    1. Enhanced Document retrieval (with smart fallback to CORE API)
    2. Literature review
    3. Initial coding
    4. Thematic grouping
    5. Theme refinement
    6. Report generation
    
    Each step includes quality control via the supervisor agent.
    """

    
    try:
        # Convert request to service format
        selected_sources = request.sources if request.mode == "manual" and request.sources else [
            "openalex", "europe_pmc", "arxiv", "core"
        ]
        if request.enrich == "none":
            enrich_with = []
        elif request.enrich == "deep":
            enrich_with = ["crossref", "unpaywall", "sem_scholar"]
        else:
            enrich_with = ["crossref", "unpaywall"]
        max_results = request.limit
        per_source_limit = max(2, (max_results + len(selected_sources) - 1) // max(1, len(selected_sources)))

        # Server-side decisions for fallbacks
        auto_fallback = True  # always enable backend auto fallback
        enable_playwright_env = os.getenv("ENABLE_PLAYWRIGHT", "").lower() in ("1", "true", "yes")
        use_playwright_fallback = bool(request.store) and enable_playwright_env

        request_data = {
            "query": request.query,
            "research_domain": request.research_domain,
            "max_results": request.max_results,
            "pipeline_config": request.pipeline_config.model_dump() if request.pipeline_config else None,
            "mode": request.mode,
            "sources": selected_sources,
            "enrich_with": enrich_with,
            "per_source_limit": per_source_limit,
            "year_from": request.year_from,
            "year_to": request.year_to,
            "auto_fallback": auto_fallback,
            "store": request.store,
            "collection_name": "ResearchPaper",
            "use_playwright_fallback": use_playwright_fallback
        }

        result = await pipeline_service.run_full_pipeline(request_data)
        
        if not result["success"]:
            print(f"[ROUTE] ❌ Pipeline failed to start!")
            return result.get('res', {})
        
        # Determine final status from result
        final_status_str = result.get("status") or ("completed" if result.get("success") else "failed")
        try:
            final_status = PipelineStatus(final_status_str)
        except Exception:
            final_status = PipelineStatus.COMPLETED if result.get("success") else PipelineStatus.FAILED

        # Create response reflecting actual completion state
        response = PipelineResponse(
            success=True,
            pipeline_id=str(result["pipeline_id"]),  # Convert UUID to string
            status=final_status,
            result=result['res'],
            data={
                "current_step": result.get("data", {}).get("current_step", 6 if final_status == PipelineStatus.COMPLETED else 0),
                "total_steps": result.get("data", {}).get("total_steps", 6),
                "started_at": result.get("data", {}).get("started_at", datetime.now(timezone.utc).isoformat()),
                "query": request.query,
                "research_domain": request.research_domain,
                "quality_scores": result.get("data", {}).get("quality_scores", {}),
                "supervisor_decisions": result.get("data", {}).get("supervisor_decisions", {})
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        return response
        
    except Exception as e:
        print(f"[ROUTE] ❌ PIPELINE START FAILED! Exception: {str(e)}")
        import traceback
        print(f"[ROUTE]   Traceback: {traceback.format_exc()}")        
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline start failed: {str(e)}"
        )


@router.post("/lite")
async def start_lite_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a lite research pipeline (runs in background to avoid Render 90s timeout).

    Returns immediately with pipeline_id. Poll GET /pipelines/{id}/progress or /results.
    """
    try:
        selected_sources = request.sources if request.mode == "manual" and request.sources else [
            "openalex", "europe_pmc", "arxiv", "core"
        ]
        if request.enrich == "none":
            enrich_with = []
        elif request.enrich == "deep":
            enrich_with = ["crossref", "unpaywall", "sem_scholar"]
        else:
            enrich_with = ["crossref", "unpaywall"]
        max_results = request.limit
        per_source_limit = max(2, (max_results + len(selected_sources) - 1) // max(1, len(selected_sources)))

        auto_fallback = True
        enable_playwright_env = os.getenv("ENABLE_PLAYWRIGHT", "").lower() in ("1", "true", "yes")
        use_playwright_fallback = bool(request.store) and enable_playwright_env

        request_data = {
            "query": request.query,
            "research_domain": request.research_domain,
            "max_results": request.max_results,
            "pipeline_config": request.pipeline_config.model_dump() if request.pipeline_config else None,
            "mode": request.mode,
            "sources": selected_sources,
            "enrich_with": enrich_with,
            "per_source_limit": per_source_limit,
            "year_from": request.year_from,
            "year_to": request.year_to,
            "auto_fallback": auto_fallback,
            "store": request.store,
            "collection_name": "ResearchPaper",
            "use_playwright_fallback": use_playwright_fallback,
        }


        # Create pipeline and return immediately; run steps in background (avoids Render 90s timeout)
        # pipeline_id = pipeline_service.create_lite_pipeline(request_data)
        result = await pipeline_service.run_lite_pipeline(request_data)

        # background_tasks.add_task(
        #     pipeline_service.run_lite_pipeline,
        #     request_data,
        #     existing_pipeline_id=pipeline_id,
        # )
        if not result["success"]:
            print(f"[ROUTE] ❌ Pipeline failed to start!")
            return result.get('res', {})
        
        # Determine final status from result
        final_status_str = result.get("status") or ("completed" if result.get("success") else "failed")
        try:
            final_status = PipelineStatus(final_status_str)
        except Exception:
            final_status = PipelineStatus.COMPLETED if result.get("success") else PipelineStatus.FAILED

        response = PipelineResponse(
            success=True,
            pipeline_id=str(result["pipeline_id"]),  # Convert UUID to string
            status=final_status,
            result=result['res'],
            data={
                "current_step": result.get("data", {}).get("current_step", 6 if final_status == PipelineStatus.COMPLETED else 0),
                "total_steps": result.get("data", {}).get("total_steps", 6),
                "started_at": result.get("data", {}).get("started_at", datetime.now(timezone.utc).isoformat()),
                "query": request.query,
                "research_domain": request.research_domain,
                "quality_scores": result.get("data", {}).get("quality_scores", {}),
                "supervisor_decisions": result.get("data", {}).get("supervisor_decisions", {})
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        return response

    except Exception as e:
        print(f"[ROUTE] ❌ LITE PIPELINE START FAILED! Exception: {str(e)}")
        import traceback
        print(f"[ROUTE]   Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Lite pipeline start failed: {str(e)}"
        )

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of pipelines to return"),
    status: Optional[PipelineStatus] = Query(None, description="Filter by pipeline status"),
    research_domain: Optional[str] = Query(None, description="Filter by research domain")
):
    """
    List all pipelines with optional filtering.
    
    Returns a list of pipelines with basic information:
    - Pipeline ID and status
    - Query and research domain
    - Start and completion times
    - Quality scores
    """
    try:
        result = pipeline_service.list_pipelines(
            limit=limit,
            status=status.value if status else None,
            research_domain=research_domain
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list pipelines: {result.get('error', 'Unknown error')}"
            )
        
        pipelines = []
        for pipeline_data in result["data"]["pipelines"]:
            pipeline_response = PipelineResponse(
                success=True,
                pipeline_id=str(pipeline_data["pipeline_id"]),  # Convert UUID to string
                status=PipelineStatus(pipeline_data["status"]),
                data=pipeline_data,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            pipelines.append(pipeline_response)
        
        return pipelines
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list pipelines: {str(e)}"
        )

@router.get("/{pipeline_id}/progress", response_model=PipelineProgressResponse)
async def get_pipeline_progress(
    pipeline_id: str = Path(..., description="Unique pipeline identifier")
):
    """
    Get the current progress of a running pipeline.
    
    Returns detailed progress information including:
    - Current step and percentage completion
    - Step-by-step status
    - Quality scores and supervisor decisions
    - Estimated completion time
    """
    print(f"\n" + "📊"*60)
    print(f"📊 GET PIPELINE PROGRESS REQUEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊"*60)
    
    try:
        print(f"[PROGRESS] 📥 Incoming request:")
        print(f"[PROGRESS]   Pipeline ID: {pipeline_id}")
        print(f"[PROGRESS]   Full ID length: {len(pipeline_id)}")
        print(f"[PROGRESS]   ID format validation: {'✅ Valid UUID format' if len(pipeline_id) == 36 and pipeline_id.count('-') == 4 else '❌ Invalid UUID format'}")
        
        print(f"[PROGRESS] 🔍 Calling pipeline_service.get_pipeline_progress()...")
        result = pipeline_service.get_pipeline_progress(pipeline_id)
        
        print(f"[PROGRESS] 📊 Pipeline service result:")
        print(f"[PROGRESS]   Success: {result.get('success', False)}")
        print(f"[PROGRESS]   Result keys: {list(result.keys())}")
        
        if result.get("error"):
            print(f"[PROGRESS]   ❌ Error: {result['error']}")
        
        if result.get("data"):
            data = result["data"]
            print(f"[PROGRESS]   📈 Progress data:")
            print(f"[PROGRESS]     Pipeline ID: {data.get('pipeline_id', 'N/A')}")
            print(f"[PROGRESS]     Status: {data.get('status', 'N/A')}")
            if "progress" in data:
                progress = data["progress"]
                print(f"[PROGRESS]     Current Step: {progress.get('current_step', 'N/A')}")
                print(f"[PROGRESS]     Total Steps: {progress.get('total_steps', 'N/A')}")
                print(f"[PROGRESS]     Percentage: {progress.get('percentage_complete', 'N/A')}%")
        
        if not result["success"]:
            print(f"[PROGRESS] ❌ Pipeline not found: {pipeline_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline not found: {pipeline_id}"
            )
        
        progress_data = result["data"]
        
        print(f"[PROGRESS] 📦 Creating response object...")
        response = PipelineProgressResponse(
            success=True,
            pipeline_id=pipeline_id,
            status=PipelineStatus(progress_data["status"]),
            data=progress_data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        print(f"[PROGRESS] ✅ Progress response created successfully!")
        print(f"[PROGRESS]   Response status: {response.status}")
        print(f"[PROGRESS]   Response data keys: {list(response.data.keys()) if response.data else 'None'}")
        print(f"📊"*60 + "\n")
        
        return response
        
    except HTTPException:
        print(f"[PROGRESS] ❌ HTTP Exception - re-raising")
        print(f"📊"*60 + "\n")
        raise
    except Exception as e:
        print(f"[PROGRESS] ❌ UNEXPECTED ERROR!")
        print(f"[PROGRESS]   Exception: {str(e)}")
        print(f"[PROGRESS]   Exception type: {type(e).__name__}")
        import traceback
        print(f"[PROGRESS]   Traceback: {traceback.format_exc()}")
        print(f"📊"*60 + "\n")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline progress: {str(e)}"
        )

@router.get("/{pipeline_id}/results", response_model=PipelineResultsResponse)
async def get_pipeline_results(
    pipeline_id: str = Path(..., description="Unique pipeline identifier")
):
    """
    Get the final results of a completed pipeline.
    
    Returns all pipeline outputs including:
    - Retrieved documents
    - Literature review results
    - Coding results
    - Thematic analysis
    - Final report information
    - Quality scores and supervisor decisions
    """
    try:
        result = pipeline_service.get_pipeline_results(pipeline_id)
        
        if not result["success"]:
            # When pipeline is still running, return 200 with error so client can keep polling
            error_msg = result.get("error", f"Pipeline {pipeline_id} not found")
            if "not finished yet" in error_msg:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": False,
                        "error": error_msg,
                        "pipeline_id": pipeline_id,
                        "timestamp": result.get("timestamp"),
                    },
                )
            raise HTTPException(
                status_code=404,
                detail=error_msg
            )
        
        results_data = result["data"]
        
        response = PipelineResultsResponse(
            success=True,
            pipeline_id=pipeline_id,
            data=results_data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline results: {str(e)}"
        )

@router.get("/{pipeline_id}/download")
async def download_pipeline_report(
    pipeline_id: str = Path(..., description="Unique pipeline identifier"),
    format: str = Query("pdf", description="Download format (pdf, markdown, text)")
):
    """
    Download the generated report from a completed pipeline.
    
    Returns the report as a downloadable file:
    - **pdf**: PDF version of the report (default)
    - **markdown**: .md file with proper formatting
    - **text**: Plain text version of the report
    """
    try:
        result = pipeline_service.download_pipeline_report(pipeline_id, format)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline report not found: {pipeline_id}"
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
            detail=f"Failed to download pipeline report: {str(e)}"
        )

@router.delete("/{pipeline_id}", response_model=SuccessResponse)
async def delete_pipeline(
    pipeline_id: str = Path(..., description="Unique pipeline identifier")
):
    """
    Delete a pipeline and all its associated data.
    
    This will remove:
    - Pipeline state and progress
    - All intermediate results
    - Generated reports
    - Quality assessments
    """
    try:
        result = pipeline_service.delete_pipeline(pipeline_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline not found: {pipeline_id}"
            )
        
        response = SuccessResponse(
            message=f"Pipeline {pipeline_id} deleted successfully",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete pipeline: {str(e)}"
        )

@router.get("/statistics/overview", response_model=PipelineStatisticsResponse)
async def get_pipeline_statistics():
    """
    Get comprehensive pipeline statistics.
    
    Returns statistics including:
    - Total pipelines and success rates
    - Average processing times
    - Quality score trends
    - Research domain distribution
    """
    print(f"\n📊 ===== PIPELINE STATISTICS ENDPOINT =====")
    print(f"📊 GET /statistics/overview request received")
    
    try:
        print(f"📊 Calling pipeline_service.get_pipeline_statistics()...")
        result = pipeline_service.get_pipeline_statistics()
        
        print(f"📊 Pipeline service result:")
        print(f"📊   Success: {result.get('success', False)}")
        print(f"📊   Has data: {bool(result.get('data'))}")
        if result.get('error'):
            print(f"📊   ❌ Error: {result['error']}")
        
        if not result["success"]:
            print(f"📊 ❌ Pipeline statistics retrieval failed!")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get pipeline statistics: {result.get('error', 'Unknown error')}"
            )
        
        print(f"📊 Creating statistics response...")
        response = PipelineStatisticsResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        print(f"📊 ✅ Statistics response created successfully!")
        print(f"📊   Total pipelines: {result['data'].get('total_pipelines', 0)}")
        print(f"📊   Completed: {result['data'].get('completed', 0)}")
        print(f"📊   Success rate: {result['data'].get('success_rate', 0):.1f}%")
        print(f"📊 =======================================\n")
        
        return response
        
    except HTTPException:
        print(f"📊 ❌ HTTP Exception - re-raising")
        print(f"📊 =======================================\n")
        raise
    except Exception as e:
        print(f"📊 ❌ STATISTICS ENDPOINT FAILED!")
        print(f"📊   Exception: {str(e)}")
        print(f"📊   Exception type: {type(e).__name__}")
        import traceback
        print(f"📊   Traceback: {traceback.format_exc()}")
        print(f"📊 =======================================\n")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline statistics: {str(e)}"
        )

@router.post("/{pipeline_id}/retry", response_model=PipelineResponse)
async def retry_pipeline_step(
    pipeline_id: str = Path(..., description="Unique pipeline identifier"),
    step_name: str = Query(..., description="Name of the step to retry")
):
    """
    Retry a specific step in a pipeline.
    
    This is useful when a step has failed and you want to retry it
    without restarting the entire pipeline.
    """
    try:
        result = pipeline_service.retry_pipeline_step(pipeline_id, step_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to retry step: {result.get('error', 'Unknown error')}"
            )
        
        response = PipelineResponse(
            success=True,
            pipeline_id=pipeline_id,
            status=PipelineStatus.RUNNING,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retry pipeline step: {str(e)}"
        )

@router.post("/{pipeline_id}/halt", response_model=SuccessResponse)
async def halt_pipeline(
    pipeline_id: str = Path(..., description="Unique pipeline identifier"),
    reason: str = Query("User requested halt", description="Reason for halting the pipeline")
):
    """
    Halt a running pipeline.
    
    This will stop the pipeline at the current step and mark it as halted.
    The pipeline can be resumed later if needed.
    """
    try:
        result = pipeline_service.halt_pipeline(pipeline_id, reason)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to halt pipeline: {result.get('error', 'Unknown error')}"
            )
        
        response = SuccessResponse(
            message=f"Pipeline {pipeline_id} halted successfully",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to halt pipeline: {str(e)}"
        ) 