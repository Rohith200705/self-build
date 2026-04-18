"""
Report generation service for combining analysis results.
"""

import logging
from typing import Optional

from app.models.schemas import (
    FullReport,
    ReportSummary,
    HealthCheckResponse,
    LoadTestResponse,
    CodeAnalysisResponse,
    Suggestion,
)
from app.utils.validators import get_timestamp

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """Service for generating comprehensive analysis reports."""
    
    def __init__(self):
        """Initialize report generation service."""
        pass
    
    def generate_report(
        self,
        website_url: Optional[str] = None,
        health_check: Optional[HealthCheckResponse] = None,
        load_test: Optional[LoadTestResponse] = None,
        code_analysis: Optional[CodeAnalysisResponse] = None,
        suggestions: Optional[list] = None,
    ) -> FullReport:
        """
        Generate a comprehensive report combining all analysis results.
        
        Args:
            website_url: Website URL being analyzed
            health_check: Health check results
            load_test: Load test results
            code_analysis: Code analysis results
            suggestions: List of suggestions
            
        Returns:
            FullReport object with all combined results
        """
        # Generate summary
        summary = self._generate_summary(
            website_url,
            health_check,
            load_test,
            code_analysis,
            suggestions
        )
        
        # Create full report
        report = FullReport(
            summary=summary,
            health_check=health_check,
            load_test=load_test,
            code_analysis=code_analysis,
            suggestions=suggestions,
            generated_at=get_timestamp()
        )
        
        logger.info(f"Report generated for {website_url or 'repository'}")
        return report
    
    def _generate_summary(
        self,
        website_url: Optional[str],
        health_check: Optional[HealthCheckResponse],
        load_test: Optional[LoadTestResponse],
        code_analysis: Optional[CodeAnalysisResponse],
        suggestions: Optional[list],
    ) -> ReportSummary:
        """
        Generate report summary based on all analysis results.
        
        Args:
            website_url: Website URL
            health_check: Health check results
            load_test: Load test results
            code_analysis: Code analysis results
            suggestions: List of suggestions
            
        Returns:
            ReportSummary object
        """
        # Calculate total issues
        total_issues = 0
        if code_analysis:
            total_issues += code_analysis.total_issues
        
        # Count critical issues
        critical_issues = 0
        
        # Determine overall health
        overall_health = self._determine_overall_health(
            health_check,
            load_test,
            code_analysis,
            suggestions
        )
        
        # Count critical suggestions
        if suggestions:
            critical_issues = sum(1 for s in suggestions if s.priority == "CRITICAL" or s.priority == "HIGH")
        
        # Add health check issues
        if health_check and health_check.status == "DOWN":
            critical_issues += 1
        elif health_check and health_check.latency > 5.0:
            critical_issues += 1
        
        # Add load test issues
        if load_test and load_test.failure_rate > 0.1:
            critical_issues += 1
        elif load_test and load_test.avg_latency > 5.0:
            critical_issues += 1
        
        recommendations_count = len(suggestions) if suggestions else 0
        
        return ReportSummary(
            website_url=website_url,
            overall_health=overall_health,
            total_issues_found=total_issues,
            critical_issues=critical_issues,
            recommendations_count=recommendations_count
        )
    
    def _determine_overall_health(
        self,
        health_check: Optional[HealthCheckResponse],
        load_test: Optional[LoadTestResponse],
        code_analysis: Optional[CodeAnalysisResponse],
        suggestions: Optional[list],
    ) -> str:
        """
        Determine overall health status based on all metrics.
        
        Args:
            health_check: Health check results
            load_test: Load test results
            code_analysis: Code analysis results
            suggestions: List of suggestions
            
        Returns:
            Health status string (CRITICAL, POOR, FAIR, GOOD, EXCELLENT)
        """
        score = 100  # Start with perfect score
        
        # Health check impact
        if health_check:
            if health_check.status == "DOWN":
                return "CRITICAL"
            elif health_check.latency > 5.0:
                score -= 30
            elif health_check.latency > 2.0:
                score -= 15
            elif health_check.latency > 1.0:
                score -= 5
        
        # Load test impact
        if load_test:
            if load_test.failure_rate > 0.1:
                score -= 25
            elif load_test.failure_rate > 0.05:
                score -= 15
            
            if load_test.avg_latency > 5.0:
                score -= 20
            elif load_test.avg_latency > 2.0:
                score -= 10
        
        # Code analysis impact
        if code_analysis:
            if code_analysis.total_issues > 10:
                score -= 20
            elif code_analysis.total_issues > 5:
                score -= 10
            elif code_analysis.total_issues > 0:
                score -= 5
        
        # Suggestions impact
        if suggestions:
            critical_count = sum(1 for s in suggestions if s.priority == "CRITICAL")
            high_count = sum(1 for s in suggestions if s.priority == "HIGH")
            
            if critical_count > 0:
                score -= (critical_count * 20)
            if high_count > 0:
                score -= (high_count * 10)
        
        # Map score to health status
        if score >= 85:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "FAIR"
        elif score >= 30:
            return "POOR"
        else:
            return "CRITICAL"
    
    def format_report_as_text(self, report: FullReport) -> str:
        """
        Format report as human-readable text.
        
        Args:
            report: FullReport object
            
        Returns:
            Formatted text report
        """
        lines = []
        
        lines.append("=" * 80)
        lines.append("WEBSITE RELIABILITY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 40)
        if report.summary.website_url:
            lines.append(f"Website: {report.summary.website_url}")
        lines.append(f"Overall Health: {report.summary.overall_health}")
        lines.append(f"Total Issues Found: {report.summary.total_issues_found}")
        lines.append(f"Critical Issues: {report.summary.critical_issues}")
        lines.append(f"Recommendations: {report.summary.recommendations_count}")
        lines.append(f"Generated: {report.generated_at}")
        lines.append("")
        
        # Health check section
        if report.health_check:
            lines.append("HEALTH CHECK RESULTS")
            lines.append("-" * 40)
            lines.append(f"Status: {report.health_check.status}")
            if report.health_check.status_code:
                lines.append(f"Status Code: {report.health_check.status_code}")
            lines.append(f"Latency: {report.health_check.latency:.3f}s")
            lines.append(f"Message: {report.health_check.message}")
            lines.append("")
        
        # Load test section
        if report.load_test:
            lines.append("LOAD TEST RESULTS")
            lines.append("-" * 40)
            lines.append(f"Total Requests: {report.load_test.total_requests}")
            lines.append(f"Failed Requests: {report.load_test.failed_requests}")
            lines.append(f"Average Latency: {report.load_test.avg_latency:.3f}s")
            lines.append(f"Min Latency: {report.load_test.min_latency:.3f}s")
            lines.append(f"Max Latency: {report.load_test.max_latency:.3f}s")
            lines.append(f"Failure Rate: {report.load_test.failure_rate:.2%}")
            lines.append("")
        
        # Code analysis section
        if report.code_analysis:
            lines.append("CODE ANALYSIS RESULTS")
            lines.append("-" * 40)
            lines.append(f"Files Scanned: {report.code_analysis.files_scanned}")
            lines.append(f"Issues Found: {report.code_analysis.total_issues}")
            
            if report.code_analysis.issues:
                lines.append("\nDetailed Issues:")
                for i, issue in enumerate(report.code_analysis.issues[:10], 1):  # Limit to first 10
                    lines.append(f"  {i}. {issue.file}")
                    if issue.line_number:
                        lines.append(f"     Line {issue.line_number}: {issue.issue}")
                    else:
                        lines.append(f"     {issue.issue}")
                    lines.append(f"     Suggestion: {issue.suggestion}")
            lines.append("")
        
        # Suggestions section
        if report.suggestions:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 40)
            for i, suggestion in enumerate(report.suggestions, 1):
                lines.append(f"{i}. [{suggestion.priority}] {suggestion.category.upper()}")
                lines.append(f"   {suggestion.description}")
                lines.append(f"   Effort: {suggestion.estimated_effort}")
                lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
