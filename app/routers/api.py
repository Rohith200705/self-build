"""
Main API router for all endpoints.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Optional

from app.models.schemas import (
    HealthCheckRequest,
    HealthCheckResponse,
    LoadTestRequest,
    LoadTestResponse,
    CodeAnalysisResponse,
    GitHubAnalysisRequest,
    GitHubAnalysisResponse,
    SuggestionsResponse,
    FullReport,
    ErrorResponse,
)
from app.services.health_check_service import HealthCheckService
from app.services.load_test_service import LoadTestService
from app.services.code_analysis_service import CodeAnalysisService
from app.services.github_service import GitHubAnalysisService
from app.services.suggestion_service import SuggestionEngine
from app.services.report_service import ReportGenerationService
from app.utils.validators import validate_url, get_timestamp
from app.core.config import TEMP_UPLOAD_DIR
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize services
health_service = HealthCheckService()
load_test_service = LoadTestService()
code_analysis_service = CodeAnalysisService()
github_service = GitHubAnalysisService()
suggestion_engine = SuggestionEngine()
report_service = ReportGenerationService()

# Store recent analysis results (in-memory, for production use database)
analysis_cache = {}


@router.post(
    "/health-check",
    response_model=HealthCheckResponse,
    summary="Check Website Health",
    description="Perform a health check on a website URL"
)
async def health_check(request: HealthCheckRequest) -> HealthCheckResponse:
    """
    Check the health status of a website.
    
    Args:
        request: HealthCheckRequest with URL
        
    Returns:
        HealthCheckResponse with status and latency
    """
    try:
        url = str(request.url)
        logger.info(f"Health check requested for: {url}")
        
        result = await health_service.check_health(url)
        
        # Cache result
        cache_key = f"health_{url}"
        analysis_cache[cache_key] = result
        
        return result
    except Exception as e:
        logger.error(f"Error in health check endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/load-test",
    response_model=LoadTestResponse,
    summary="Run Load Test",
    description="Simulate concurrent users making requests to a website"
)
async def load_test(request: LoadTestRequest) -> LoadTestResponse:
    """
    Run load testing on a website.
    
    Args:
        request: LoadTestRequest with URL and load parameters
        
    Returns:
        LoadTestResponse with performance metrics
    """
    try:
        url = str(request.url)
        logger.info(f"Load test requested for: {url} with {request.users} users")
        
        result = await load_test_service.run_load_test(
            url=url,
            users=request.users,
            requests_per_user=request.requests_per_user
        )
        
        # Cache result
        cache_key = f"load_test_{url}"
        analysis_cache[cache_key] = result
        
        return result
    except Exception as e:
        logger.error(f"Error in load test endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/upload-code",
    response_model=CodeAnalysisResponse,
    summary="Upload and Analyze Code",
    description="Upload a ZIP file containing source code for analysis"
)
async def upload_code(file: UploadFile = File(...)) -> CodeAnalysisResponse:
    """
    Upload and analyze source code from ZIP file.
    
    Args:
        file: ZIP file containing source code
        
    Returns:
        CodeAnalysisResponse with detected issues
    """
    try:
        if not file.filename.endswith(".zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only ZIP files are supported"
            )
        
        logger.info(f"Code upload requested: {file.filename}")
        
        # Save uploaded file
        file_path = TEMP_UPLOAD_DIR / file.filename
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Analyze
        result = await code_analysis_service.analyze_zip_file(str(file_path))
        
        # Cache result
        cache_key = f"code_analysis_{file.filename}"
        analysis_cache[cache_key] = result
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload code endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/analyze-github",
    response_model=GitHubAnalysisResponse,
    summary="Analyze GitHub Repository",
    description="Analyze source code from a GitHub repository"
)
async def analyze_github(request: GitHubAnalysisRequest) -> GitHubAnalysisResponse:
    """
    Analyze source code from GitHub repository.
    
    Args:
        request: GitHubAnalysisRequest with repository URL
        
    Returns:
        GitHubAnalysisResponse with detected issues
    """
    try:
        logger.info(f"GitHub analysis requested: {request.repo_url}")
        
        result = await github_service.analyze_repository(request.repo_url)
        
        # Cache result
        cache_key = f"github_{result.repo_name}"
        analysis_cache[cache_key] = result
        
        return result
    except Exception as e:
        logger.error(f"Error in GitHub analysis endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/suggestions",
    response_model=SuggestionsResponse,
    summary="Generate Suggestions",
    description="Generate recommendations based on detected issues"
)
async def get_suggestions() -> SuggestionsResponse:
    """
    Generate suggestions based on cached analysis results.
    
    Returns:
        SuggestionsResponse with list of suggestions
    """
    try:
        logger.info("Suggestions requested")
        
        # Collect all cached results
        all_suggestions = []
        
        for cache_key, result in analysis_cache.items():
            if "code_analysis" in cache_key or "github" in cache_key:
                if hasattr(result, "issues"):
                    suggestions = suggestion_engine.generate_from_code_issues(result.issues)
                    all_suggestions.extend(suggestions)
            elif "health" in cache_key:
                suggestions = suggestion_engine.generate_from_health_check(result)
                all_suggestions.extend(suggestions)
            elif "load_test" in cache_key:
                suggestions = suggestion_engine.generate_from_load_test(result)
                all_suggestions.extend(suggestions)
        
        # Prioritize suggestions
        prioritized = suggestion_engine.prioritize_suggestions(all_suggestions)
        
        return SuggestionsResponse(suggestions=prioritized)
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/report",
    response_model=FullReport,
    summary="Generate Full Report",
    description="Generate comprehensive report combining all analysis results"
)
async def generate_report() -> FullReport:
    """
    Generate comprehensive report combining all analysis results.
    
    Returns:
        FullReport with all analysis data
    """
    try:
        logger.info("Report generation requested")
        
        # Extract results from cache
        health_check = None
        load_test = None
        code_analysis = None
        website_url = None
        
        for cache_key, result in analysis_cache.items():
            if "health" in cache_key:
                health_check = result
                # Extract URL from cache key
                website_url = cache_key.replace("health_", "")
            elif "load_test" in cache_key:
                load_test = result
            elif "code_analysis" in cache_key or "github" in cache_key:
                code_analysis = result
        
        # Generate suggestions
        all_suggestions = []
        
        if code_analysis and hasattr(code_analysis, "issues"):
            suggestions = suggestion_engine.generate_from_code_issues(code_analysis.issues)
            all_suggestions.extend(suggestions)
        
        if health_check:
            suggestions = suggestion_engine.generate_from_health_check(health_check)
            all_suggestions.extend(suggestions)
        
        if load_test:
            suggestions = suggestion_engine.generate_from_load_test(load_test)
            all_suggestions.extend(suggestions)
        
        # Prioritize
        all_suggestions = suggestion_engine.prioritize_suggestions(all_suggestions)
        
        # Generate report
        report = report_service.generate_report(
            website_url=website_url,
            health_check=health_check,
            load_test=load_test,
            code_analysis=code_analysis,
            suggestions=all_suggestions
        )
        
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/report/text",
    response_model=dict,
    summary="Get Text Report",
    description="Get report formatted as human-readable text"
)
async def get_text_report() -> dict:
    """
    Get report formatted as human-readable text.
    
    Returns:
        Dictionary with formatted text report
    """
    try:
        logger.info("Text report requested")
        
        # Get full report first
        health_check = None
        load_test = None
        code_analysis = None
        website_url = None
        
        for cache_key, result in analysis_cache.items():
            if "health" in cache_key:
                health_check = result
                website_url = cache_key.replace("health_", "")
            elif "load_test" in cache_key:
                load_test = result
            elif "code_analysis" in cache_key or "github" in cache_key:
                code_analysis = result
        
        # Generate suggestions
        all_suggestions = []
        
        if code_analysis and hasattr(code_analysis, "issues"):
            suggestions = suggestion_engine.generate_from_code_issues(code_analysis.issues)
            all_suggestions.extend(suggestions)
        
        if health_check:
            suggestions = suggestion_engine.generate_from_health_check(health_check)
            all_suggestions.extend(suggestions)
        
        if load_test:
            suggestions = suggestion_engine.generate_from_load_test(load_test)
            all_suggestions.extend(suggestions)
        
        all_suggestions = suggestion_engine.prioritize_suggestions(all_suggestions)
        
        # Generate report
        report = report_service.generate_report(
            website_url=website_url,
            health_check=health_check,
            load_test=load_test,
            code_analysis=code_analysis,
            suggestions=all_suggestions
        )
        
        # Format as text
        text_report = report_service.format_report_as_text(report)
        
        return {"report": text_report}
    except Exception as e:
        logger.error(f"Error generating text report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/cache/clear",
    summary="Clear Cache",
    description="Clear all cached analysis results"
)
async def clear_cache() -> dict:
    """Clear all cached analysis results."""
    global analysis_cache
    analysis_cache.clear()
    logger.info("Cache cleared")
    return {"message": "Cache cleared successfully"}
