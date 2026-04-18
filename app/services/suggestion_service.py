"""
Suggestion engine for generating fix recommendations.
"""

import logging
from typing import List

from app.models.schemas import Suggestion, CodeIssue, HealthCheckResponse, LoadTestResponse

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """Engine for generating actionable suggestions based on analysis results."""
    
    def __init__(self):
        """Initialize suggestion engine."""
        self.suggestions_map = self._build_suggestions_map()
    
    def _build_suggestions_map(self) -> dict:
        """Build mapping of issue keywords to suggestions."""
        return {
            "error_handling": {
                "without error handling": {
                    "priority": "HIGH",
                    "description": "Add try/except blocks to handle network errors and exceptions",
                    "effort": "LOW"
                },
                "exception": {
                    "priority": "HIGH",
                    "description": "Implement comprehensive error handling",
                    "effort": "MEDIUM"
                },
            },
            "timeout": {
                "timeout": {
                    "priority": "HIGH",
                    "description": "Add or increase timeout values for HTTP requests",
                    "effort": "LOW"
                },
                "hanging": {
                    "priority": "CRITICAL",
                    "description": "Implement request timeout to prevent indefinite hanging",
                    "effort": "LOW"
                },
            },
            "performance": {
                "blocking": {
                    "priority": "MEDIUM",
                    "description": "Replace blocking calls with async/await patterns",
                    "effort": "MEDIUM"
                },
                "latency": {
                    "priority": "MEDIUM",
                    "description": "Optimize performance to reduce response latency",
                    "effort": "HIGH"
                },
            },
            "security": {
                "credentials": {
                    "priority": "CRITICAL",
                    "description": "Move hardcoded credentials to environment variables",
                    "effort": "LOW"
                },
                "password": {
                    "priority": "CRITICAL",
                    "description": "Use secure credential management",
                    "effort": "LOW"
                },
            },
            "reliability": {
                "infinite loop": {
                    "priority": "HIGH",
                    "description": "Add proper loop termination conditions",
                    "effort": "LOW"
                },
                "failure": {
                    "priority": "HIGH",
                    "description": "Add retry logic and circuit breaker patterns",
                    "effort": "MEDIUM"
                },
            },
        }
    
    def generate_from_code_issues(self, issues: List[CodeIssue]) -> List[Suggestion]:
        """
        Generate suggestions based on code analysis issues.
        
        Args:
            issues: List of CodeIssue objects
            
        Returns:
            List of Suggestion objects
        """
        suggestions = []
        processed_categories = set()
        
        for issue in issues:
            category = self._categorize_issue(issue.issue)
            
            # Avoid duplicate suggestions for same category
            if category in processed_categories:
                continue
            
            suggestion = self._create_suggestion_from_issue(issue, category)
            if suggestion:
                suggestions.append(suggestion)
                processed_categories.add(category)
        
        return suggestions
    
    def generate_from_health_check(self, health_check: HealthCheckResponse) -> List[Suggestion]:
        """
        Generate suggestions based on health check results.
        
        Args:
            health_check: HealthCheckResponse object
            
        Returns:
            List of Suggestion objects
        """
        suggestions = []
        
        if health_check.status == "DOWN":
            suggestions.append(Suggestion(
                category="availability",
                priority="CRITICAL",
                description="Website is down. Investigate server logs and infrastructure health.",
                estimated_effort="HIGH"
            ))
        elif health_check.latency > 5.0:
            suggestions.append(Suggestion(
                category="performance",
                priority="HIGH",
                description="High latency detected. Consider optimizing backend response time.",
                estimated_effort="HIGH"
            ))
        elif health_check.latency > 2.0:
            suggestions.append(Suggestion(
                category="performance",
                priority="MEDIUM",
                description="Response time is slower than typical. Profile and optimize.",
                estimated_effort="MEDIUM"
            ))
        
        if health_check.status_code and 400 <= health_check.status_code < 500:
            suggestions.append(Suggestion(
                category="error_handling",
                priority="MEDIUM",
                description="Client errors detected. Review request validation and error messages.",
                estimated_effort="LOW"
            ))
        elif health_check.status_code and health_check.status_code >= 500:
            suggestions.append(Suggestion(
                category="error_handling",
                priority="HIGH",
                description="Server error detected. Review application logs and error handling.",
                estimated_effort="MEDIUM"
            ))
        
        return suggestions
    
    def generate_from_load_test(self, load_test: LoadTestResponse) -> List[Suggestion]:
        """
        Generate suggestions based on load test results.
        
        Args:
            load_test: LoadTestResponse object
            
        Returns:
            List of Suggestion objects
        """
        suggestions = []
        
        if load_test.failure_rate > 0.05:
            suggestions.append(Suggestion(
                category="reliability",
                priority="HIGH",
                description="High failure rate under load. Add error handling and retry logic.",
                estimated_effort="MEDIUM"
            ))
        
        if load_test.avg_latency > 5.0:
            suggestions.append(Suggestion(
                category="performance",
                priority="HIGH",
                description="Slow response times under load. Implement caching and optimization.",
                estimated_effort="HIGH"
            ))
        elif load_test.avg_latency > 2.0:
            suggestions.append(Suggestion(
                category="performance",
                priority="MEDIUM",
                description="Average latency increases under load. Optimize database queries and endpoints.",
                estimated_effort="MEDIUM"
            ))
        
        if load_test.max_latency > load_test.avg_latency * 3:
            suggestions.append(Suggestion(
                category="performance",
                priority="MEDIUM",
                description="Inconsistent performance detected. Add monitoring and performance testing.",
                estimated_effort="MEDIUM"
            ))
        
        return suggestions
    
    def _categorize_issue(self, issue_text: str) -> str:
        """
        Categorize issue based on issue text.
        
        Args:
            issue_text: Issue description
            
        Returns:
            Category name
        """
        text_lower = issue_text.lower()
        
        if any(word in text_lower for word in ["error", "exception", "handling"]):
            return "error_handling"
        elif any(word in text_lower for word in ["timeout", "timeout"]):
            return "timeout"
        elif any(word in text_lower for word in ["blocking", "async", "performance", "latency"]):
            return "performance"
        elif any(word in text_lower for word in ["credential", "password", "secret", "api_key", "token"]):
            return "security"
        elif any(word in text_lower for word in ["loop", "failure", "retry"]):
            return "reliability"
        else:
            return "general"
    
    def _create_suggestion_from_issue(self, issue: CodeIssue, category: str) -> Suggestion:
        """
        Create a suggestion from a code issue.
        
        Args:
            issue: CodeIssue object
            category: Category name
            
        Returns:
            Suggestion object
        """
        # Map priority based on issue type
        priority_map = {
            "error_handling": "HIGH",
            "timeout": "HIGH",
            "performance": "MEDIUM",
            "security": "CRITICAL",
            "reliability": "HIGH",
        }
        
        effort_map = {
            "error_handling": "LOW",
            "timeout": "LOW",
            "performance": "MEDIUM",
            "security": "LOW",
            "reliability": "MEDIUM",
        }
        
        return Suggestion(
            category=category,
            priority=priority_map.get(category, "MEDIUM"),
            description=issue.suggestion,
            estimated_effort=effort_map.get(category, "MEDIUM")
        )
    
    def prioritize_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """
        Sort suggestions by priority.
        
        Args:
            suggestions: List of Suggestion objects
            
        Returns:
            Sorted list of Suggestion objects
        """
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        
        return sorted(
            suggestions,
            key=lambda s: priority_order.get(s.priority, 999)
        )
