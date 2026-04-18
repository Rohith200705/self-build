"""
Pydantic models for request and response schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, HttpUrl, field_validator


# Health Check Models
class HealthCheckRequest(BaseModel):
    """Request model for health check endpoint."""
    url: HttpUrl

    model_config = {
        "json_schema_extra": {
            "example": {"url": "https://example.com"}
        }
    }


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str  # UP or DOWN
    status_code: Optional[int] = None
    latency: float
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "UP",
                "status_code": 200,
                "latency": 0.45,
                "message": "Website is healthy"
            }
        }
    }


# Load Testing Models
class LoadTestRequest(BaseModel):
    """Request model for load testing endpoint."""
    url: HttpUrl
    users: int = 10
    requests_per_user: int = 5

    @field_validator("users", "requests_per_user")
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Must be positive integer")
        if v > 1000:
            raise ValueError("Value too large (max 1000)")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://example.com",
                "users": 10,
                "requests_per_user": 5
            }
        }
    }


class LoadTestResponse(BaseModel):
    """Response model for load testing endpoint."""
    avg_latency: float
    total_requests: int
    failed_requests: int
    failure_rate: float
    min_latency: float
    max_latency: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "avg_latency": 0.45,
                "total_requests": 50,
                "failed_requests": 2,
                "failure_rate": 0.04,
                "min_latency": 0.30,
                "max_latency": 1.20
            }
        }
    }


# Code Analysis Models
class CodeIssue(BaseModel):
    """Model for a single code issue."""
    file: str
    line_number: Optional[int] = None
    issue: str
    suggestion: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "file": "src/main.py",
                "line_number": 42,
                "issue": "Missing try/except block in request call",
                "suggestion": "Wrap httpx request in try/except to handle timeouts and network errors"
            }
        }
    }


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis endpoint."""
    total_issues: int
    issues: List[CodeIssue]
    files_scanned: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_issues": 3,
                "files_scanned": 5,
                "issues": [
                    {
                        "file": "src/main.py",
                        "line_number": 42,
                        "issue": "Missing try/except block",
                        "suggestion": "Wrap in try/except"
                    }
                ]
            }
        }
    }


# GitHub Analysis Models
class GitHubAnalysisRequest(BaseModel):
    """Request model for GitHub repository analysis."""
    repo_url: str

    @field_validator("repo_url")
    @classmethod
    def validate_github_url(cls, v):
        if "github.com" not in v:
            raise ValueError("Invalid GitHub repository URL")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_url": "https://github.com/username/repo"
            }
        }
    }


class GitHubAnalysisResponse(BaseModel):
    """Response model for GitHub analysis endpoint."""
    repo_name: str
    total_issues: int
    issues: List[CodeIssue]
    files_scanned: int
    analysis_timestamp: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_name": "username/repo",
                "total_issues": 5,
                "files_scanned": 12,
                "issues": [],
                "analysis_timestamp": "2024-01-15T10:30:00"
            }
        }
    }


# Suggestion Models
class Suggestion(BaseModel):
    """Model for a suggestion."""
    category: str  # e.g., "error_handling", "performance", "security"
    priority: str  # HIGH, MEDIUM, LOW
    description: str
    estimated_effort: str  # LOW, MEDIUM, HIGH


class SuggestionsResponse(BaseModel):
    """Response model for suggestions endpoint."""
    suggestions: List[Suggestion]

    model_config = {
        "json_schema_extra": {
            "example": {
                "suggestions": [
                    {
                        "category": "error_handling",
                        "priority": "HIGH",
                        "description": "Add timeout handling for external API calls",
                        "estimated_effort": "LOW"
                    }
                ]
            }
        }
    }


# Report Models
class ReportSummary(BaseModel):
    """Summary section of the report."""
    website_url: Optional[str] = None
    overall_health: str
    total_issues_found: int
    critical_issues: int
    recommendations_count: int


class FullReport(BaseModel):
    """Full report combining all analysis results."""
    summary: ReportSummary
    health_check: Optional[HealthCheckResponse] = None
    load_test: Optional[LoadTestResponse] = None
    code_analysis: Optional[CodeAnalysisResponse] = None
    suggestions: Optional[List[Suggestion]] = None
    generated_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "generated_at": "2024-01-15T10:30:00",
                "summary": {
                    "website_url": "https://example.com",
                    "overall_health": "GOOD",
                    "total_issues_found": 3,
                    "critical_issues": 0,
                    "recommendations_count": 5
                },
                "health_check": None,
                "load_test": None,
                "code_analysis": None,
                "suggestions": None
            }
        }
    }


# Error Response Models
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Validation Error",
                "detail": "Invalid URL format",
                "status_code": 400
            }
        }
    }
