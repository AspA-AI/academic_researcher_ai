"""
Test script for the API models.
Tests that all Pydantic models can be imported and used correctly.
"""

import sys
import os
from datetime import datetime, timezone

# Add the parent directory to the path

def test_model_imports():
    """Test that all models can be imported successfully."""
    print("🧪 Testing Model Imports...")
    
    try:
        # Test request models
        from models.requests import (
            PipelineRequest, AgentRequest, QualityRequest, DataRequest, ReportRequest,
            PipelineConfig, QualityOverrideRequest, QualityThresholdsRequest
        )
        print("✅ Request models imported successfully")
        
        # Test response models
        from models.responses import (
            PipelineResponse, AgentResponse, QualityResponse, DataResponse, ReportResponse,
            ErrorResponse, SuccessResponse, PipelineProgressResponse, PipelineResultsResponse,
            AgentStatusResponse, AgentHealthResponse, QualityHistoryResponse, QualityAnalyticsResponse,
            DataStatisticsResponse, ReportListResponse, ReportDownloadResponse, ReportStatisticsResponse,
            PipelineStatisticsResponse
        )
        print("✅ Response models imported successfully")
        
        # Test pipeline models
        from models.pipeline import (
            PipelineState, PipelineStep, PipelineProgress, PipelineResults,
            PipelineSummary, PipelineStatistics, PipelineConfigModel, QualityMetrics
        )
        print("✅ Pipeline models imported successfully")
        
        # Test agent models
        from models.agents import (
            AgentHealth, AgentStatusInfo, AgentOutput, LiteratureReviewOutput,
            Code, CodedUnit, InitialCodingOutput, Theme, ThematicGroupingOutput,
            RefinedTheme, ThemeRefinementOutput, ReportGenerationOutput, AgentPerformanceMetrics
        )
        print("✅ Agent models imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_request_models():
    """Test request model creation and validation."""
    print("\n🧪 Testing Request Models...")
    
    try:
        from models.requests import PipelineRequest, AgentRequest, QualityRequest
        
        # Test PipelineRequest
        pipeline_request = PipelineRequest(
            query="transparency in blockchain",
            research_domain="Blockchain",
            max_results=15,
            quality_threshold=0.7
        )
        print("✅ PipelineRequest created successfully")
        
        # Test AgentRequest
        agent_request = AgentRequest(
            agent_type="literature_review",
            documents=[{"title": "Test", "content": "Test content"}],
            research_domain="Blockchain"
        )
        print("✅ AgentRequest created successfully")
        
        # Test QualityRequest
        quality_request = QualityRequest(
            agent_output={"summary": "Test summary"},
            agent_type="literature_review",
            research_domain="Blockchain"
        )
        print("✅ QualityRequest created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Request model test failed: {e}")
        return False

def test_response_models():
    """Test response model creation and validation."""
    print("\n🧪 Testing Response Models...")
    
    try:
        from models.responses import (
            PipelineResponse, AgentResponse, QualityResponse, ErrorResponse, SuccessResponse
        )
        from models.requests import AgentType
        from models.responses import PipelineStatus, AgentStatus, QualityStatus
        
        # Test PipelineResponse
        pipeline_response = PipelineResponse(
            success=True,
            pipeline_id="pipeline-123",
            status=PipelineStatus.RUNNING,
            data={"current_step": 2, "total_steps": 6},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        print("✅ PipelineResponse created successfully")
        
        # Test AgentResponse
        agent_response = AgentResponse(
            success=True,
            agent_type="literature_review",
            data={"summary": "Test summary"},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        print("✅ AgentResponse created successfully")
        
        # Test QualityResponse
        quality_response = QualityResponse(
            success=True,
            assessment_id="assessment-123",
            data={"quality_score": 0.8, "supervisor_status": "APPROVE"},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        print("✅ QualityResponse created successfully")
        
        # Test ErrorResponse
        error_response = ErrorResponse(
            error="Test error message",
            error_code="TEST_ERROR",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        print("✅ ErrorResponse created successfully")
        
        # Test SuccessResponse
        success_response = SuccessResponse(
            message="Test success message",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        print("✅ SuccessResponse created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Response model test failed: {e}")
        return False

def test_pipeline_models():
    """Test pipeline model creation and validation."""
    print("\n🧪 Testing Pipeline Models...")
    
    try:
        from models.pipeline import (
            PipelineState, PipelineStep, PipelineProgress, PipelineResults,
            StepStatus, QualityMetrics
        )
        
        # Test PipelineStep
        pipeline_step = PipelineStep(
            step_number=1,
            step_name="Document Retrieval",
            status=StepStatus.COMPLETED,
            message="Retrieved 15 documents",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=45.2
        )
        print("✅ PipelineStep created successfully")
        
        # Test PipelineProgress
        pipeline_progress = PipelineProgress(
            current_step=3,
            total_steps=6,
            percentage=50.0,
            estimated_completion=datetime.now(timezone.utc).isoformat(),
            time_elapsed=180.5,
            time_remaining=180.0
        )
        print("✅ PipelineProgress created successfully")
        
        # Test QualityMetrics
        quality_metrics = QualityMetrics(
            quality_score=0.8,
            supervisor_status="APPROVE",
            confidence=0.9,
            feedback=["Good summary", "Clear findings"],
            issues_found=[]
        )
        print("✅ QualityMetrics created successfully")
        
        # Test PipelineState
        pipeline_state = PipelineState(
            pipeline_id="pipeline-123",
            status="running",
            current_step=2,
            total_steps=6,
            started_at=datetime.now(timezone.utc).isoformat(),
            query="transparency in blockchain",
            research_domain="Blockchain",
            max_results=15,
            quality_threshold=0.7,
            config={"enable_supervisor": True},
            steps=[pipeline_step],
            results={},
            quality_scores={"literature_review": 0.8},
            supervisor_decisions={"literature_review": "APPROVE"},
            errors=[],
            completion_message=None
        )
        print("✅ PipelineState created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline model test failed: {e}")
        return False

def test_agent_models():
    """Test agent model creation and validation."""
    print("\n🧪 Testing Agent Models...")
    
    try:
        from models.agents import (
            AgentHealth, AgentStatusInfo, AgentOutput, LiteratureReviewOutput,
            Code, CodedUnit, InitialCodingOutput, AgentType, AgentStatus
        )
        
        # Test AgentHealth
        agent_health = AgentHealth(
            agent_type=AgentType.LITERATURE_REVIEW,
            status=AgentStatus.READY,
            last_used=datetime.now(timezone.utc).isoformat(),
            healthy=True,
            uptime_seconds=3600.0,
            memory_usage_mb=128.5,
            cpu_usage_percent=5.2,
            error_count=0,
            success_rate=95.5
        )
        print("✅ AgentHealth created successfully")
        
        # Test AgentStatusInfo
        agent_status_info = AgentStatusInfo(
            status=AgentStatus.READY,
            last_used=datetime.now(timezone.utc).isoformat(),
            error_message=None,
            performance_metrics={
                "average_response_time": 2.5,
                "total_operations": 150,
                "successful_operations": 145
            }
        )
        print("✅ AgentStatusInfo created successfully")
        
        # Test Code
        code = Code(
            name="Transparency Mechanisms",
            definition="Various mechanisms for ensuring transparency in blockchain systems",
            confidence=0.85,
            category="primary"
        )
        print("✅ Code created successfully")
        
        # Test CodedUnit
        coded_unit = CodedUnit(
            unit_id="unit_0001",
            content="This paper discusses transparency mechanisms in blockchain...",
            source="Sample Paper Title",
            authors=["Author 1", "Author 2"],
            year=2023,
            codes=[code],
            harvard_citation="(Author 1, 2023)",
            insights=["Insight 1", "Insight 2"]
        )
        print("✅ CodedUnit created successfully")
        
        # Test LiteratureReviewOutput
        lit_review_output = LiteratureReviewOutput(
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_seconds=45.2,
            input_size=15,
            output_size=2500,
            summary="Comprehensive review of transparency in blockchain technology",
            key_findings=["Finding 1", "Finding 2", "Finding 3"],
            research_gaps=["Gap 1", "Gap 2"],
            methodologies=["Qualitative analysis", "Systematic review"],
            future_directions=["Direction 1", "Direction 2"],
            full_literature_review="Complete literature review text...",
            documents_analyzed=15,
            research_domain="Blockchain"
        )
        print("✅ LiteratureReviewOutput created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent model test failed: {e}")
        return False

def test_model_serialization():
    """Test model serialization to JSON."""
    print("\n🧪 Testing Model Serialization...")
    
    try:
        from models.requests import PipelineRequest
        from models.responses import PipelineResponse
        from models.pipeline import PipelineStep
        from models.agents import AgentHealth
        from models.requests import AgentType
        from models.responses import PipelineStatus
        from models.agents import AgentType, AgentStatus
        
        # Test request model serialization
        pipeline_request = PipelineRequest(
            query="transparency in blockchain",
            research_domain="Blockchain",
            max_results=15,
            quality_threshold=0.7
        )
        request_json = pipeline_request.model_dump_json()
        print("✅ PipelineRequest serialized to JSON")
        
        # Test response model serialization
        pipeline_response = PipelineResponse(
            success=True,
            pipeline_id="pipeline-123",
            status=PipelineStatus.RUNNING,
            data={"current_step": 2, "total_steps": 6},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        response_json = pipeline_response.model_dump_json()
        print("✅ PipelineResponse serialized to JSON")
        
        # Test pipeline model serialization
        pipeline_step = PipelineStep(
            step_number=1,
            step_name="Document Retrieval",
            status="completed",
            message="Retrieved 15 documents",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=45.2
        )
        step_json = pipeline_step.model_dump_json()
        print("✅ PipelineStep serialized to JSON")
        
        # Test agent model serialization
        agent_health = AgentHealth(
            agent_type=AgentType.LITERATURE_REVIEW,
            status=AgentStatus.READY,
            last_used=datetime.now(timezone.utc).isoformat(),
            healthy=True,
            uptime_seconds=3600.0,
            memory_usage_mb=128.5,
            cpu_usage_percent=5.2,
            error_count=0,
            success_rate=95.5
        )
        health_json = agent_health.model_dump_json()
        print("✅ AgentHealth serialized to JSON")
        
        return True
        
    except Exception as e:
        print(f"❌ Model serialization test failed: {e}")
        return False

def test_model_validation():
    """Test model validation and error handling."""
    print("\n🧪 Testing Model Validation...")
    
    try:
        from models.requests import PipelineRequest, AgentRequest
        from pydantic import ValidationError
        
        # Test valid pipeline request
        try:
            valid_request = PipelineRequest(
                query="test query",
                research_domain="Test",
                max_results=10,
                quality_threshold=0.5
            )
            print("✅ Valid PipelineRequest validation passed")
        except ValidationError as e:
            print(f"❌ Valid PipelineRequest validation failed: {e}")
            return False
        
        # Test invalid pipeline request (should fail)
        try:
            invalid_request = PipelineRequest(
                query="",  # Empty query should fail
                research_domain="Test",
                max_results=10,
                quality_threshold=0.5
            )
            print("❌ Invalid PipelineRequest validation should have failed")
            return False
        except ValidationError:
            print("✅ Invalid PipelineRequest validation correctly failed")
        
        # Test valid agent request
        try:
            valid_agent_request = AgentRequest(
                agent_type="literature_review",
                documents=[{"title": "Test", "content": "Test content"}],
                research_domain="Test"
            )
            print("✅ Valid AgentRequest validation passed")
        except ValidationError as e:
            print(f"❌ Valid AgentRequest validation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation test failed: {e}")
        return False

def main():
    """Run all model tests."""
    print("🚀 Starting API Models Tests...")
    print("=" * 50)
    
    tests = [
        ("Model Imports", test_model_imports),
        ("Request Models", test_request_models),
        ("Response Models", test_response_models),
        ("Pipeline Models", test_pipeline_models),
        ("Agent Models", test_agent_models),
        ("Model Serialization", test_model_serialization),
        ("Model Validation", test_model_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Model Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All model tests passed! API models are ready for FastAPI integration.")
    else:
        print("⚠️  Some model tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main() 