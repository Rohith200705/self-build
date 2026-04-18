"""
Code analysis service for detecting issues in source code.
"""

import logging
import re
import zipfile
from pathlib import Path
from typing import List

from app.models.schemas import CodeIssue, CodeAnalysisResponse
from app.core.config import TEMP_UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_CODE_EXTENSIONS
from app.utils.validators import is_code_file, detect_blocking_patterns, detect_request_timeout

logger = logging.getLogger(__name__)


class CodeAnalysisService:
    """Service for analyzing source code for issues."""
    
    def __init__(self):
        """Initialize code analysis service."""
        self.temp_dir = TEMP_UPLOAD_DIR
        self.max_size = MAX_UPLOAD_SIZE
        self.allowed_extensions = ALLOWED_CODE_EXTENSIONS
    
    async def analyze_zip_file(self, file_path: str) -> CodeAnalysisResponse:
        """
        Extract and analyze ZIP file containing source code.
        
        Args:
            file_path: Path to ZIP file
            
        Returns:
            CodeAnalysisResponse with detected issues
        """
        issues = []
        
        try:
            # Check file exists and size
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return CodeAnalysisResponse(
                    total_issues=0,
                    issues=[],
                    files_scanned=0
                )
            
            if path.stat().st_size > self.max_size:
                logger.error(f"File too large: {file_path}")
                return CodeAnalysisResponse(
                    total_issues=0,
                    issues=[],
                    files_scanned=0
                )
            
            # Extract and analyze
            extract_path = self.temp_dir / path.stem
            extract_path.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Scan extracted files
            files_scanned = 0
            for code_file in extract_path.rglob("*"):
                if code_file.is_file() and is_code_file(code_file.name):
                    files_scanned += 1
                    file_issues = await self._analyze_file(code_file)
                    issues.extend(file_issues)
            
            return CodeAnalysisResponse(
                total_issues=len(issues),
                issues=issues,
                files_scanned=files_scanned
            )
        
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {file_path}")
            return CodeAnalysisResponse(
                total_issues=0,
                issues=[],
                files_scanned=0
            )
        except Exception as e:
            logger.error(f"Error analyzing ZIP file: {e}")
            return CodeAnalysisResponse(
                total_issues=0,
                issues=[],
                files_scanned=0
            )
    
    async def analyze_repository(self, repo_path: str) -> CodeAnalysisResponse:
        """
        Analyze source code in a repository directory.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            CodeAnalysisResponse with detected issues
        """
        issues = []
        
        try:
            repo_dir = Path(repo_path)
            if not repo_dir.exists():
                logger.error(f"Repository not found: {repo_path}")
                return CodeAnalysisResponse(
                    total_issues=0,
                    issues=[],
                    files_scanned=0
                )
            
            # Scan code files
            files_scanned = 0
            for code_file in repo_dir.rglob("*"):
                if code_file.is_file() and is_code_file(code_file.name):
                    files_scanned += 1
                    file_issues = await self._analyze_file(code_file)
                    issues.extend(file_issues)
            
            logger.info(f"Repository analysis complete: {files_scanned} files, {len(issues)} issues")
            
            return CodeAnalysisResponse(
                total_issues=len(issues),
                issues=issues,
                files_scanned=files_scanned
            )
        
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            return CodeAnalysisResponse(
                total_issues=0,
                issues=[],
                files_scanned=0
            )
    
    async def _analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """
        Analyze a single file for issues.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of CodeIssue objects
        """
        issues = []
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return issues
        
        # Relative path for display
        rel_path = str(file_path.relative_to(self.temp_dir))
        
        # Check for blocking patterns
        blocking = detect_blocking_patterns(content)
        for issue_msg in blocking:
            issues.append(CodeIssue(
                file=rel_path,
                issue=issue_msg,
                suggestion="Use httpx with async/await for non-blocking HTTP calls"
            ))
        
        # Check for missing try/except in critical sections
        issues.extend(self._check_error_handling(content, rel_path))
        
        # Check for timeout in requests
        issues.extend(self._check_timeouts(content, rel_path))
        
        # Check for other common issues
        issues.extend(self._check_other_issues(content, rel_path))
        
        return issues
    
    def _check_error_handling(self, content: str, file_path: str) -> List[CodeIssue]:
        """Check for missing error handling."""
        issues = []
        
        # Check for requests/httpx calls without try/except (simplified heuristic)
        if re.search(r"(requests\.|httpx\.|aiohttp\.)" , content):
            # Find lines with requests
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if re.search(r"(requests\.|httpx\.|aiohttp\.)", line):
                    # Check if it's in a try block (simple check)
                    context = "\n".join(lines[max(0, i-5):i])
                    if "try:" not in context:
                        issues.append(CodeIssue(
                            file=file_path,
                            line_number=i,
                            issue="HTTP request without error handling",
                            suggestion="Wrap HTTP calls in try/except block to handle network errors and timeouts"
                        ))
        
        return issues
    
    def _check_timeouts(self, content: str, file_path: str) -> List[CodeIssue]:
        """Check for missing timeout specifications."""
        issues = []
        
        if "httpx" in content and not detect_request_timeout(content):
            # Find httpx calls without timeout
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "httpx." in line and "timeout" not in line:
                    issues.append(CodeIssue(
                        file=file_path,
                        line_number=i,
                        issue="httpx call without explicit timeout",
                        suggestion="Add timeout parameter to prevent hanging requests (e.g., timeout=30)"
                    ))
        
        return issues
    
    def _check_other_issues(self, content: str, file_path: str) -> List[CodeIssue]:
        """Check for other common issues."""
        issues = []
        
        # Check for infinite loops (simplified check)
        if re.search(r"while\s+True\s*:", content):
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if re.search(r"while\s+True\s*:", line):
                    issues.append(CodeIssue(
                        file=file_path,
                        line_number=i,
                        issue="Infinite loop detected",
                        suggestion="Add proper loop termination condition or break statement"
                    ))
        
        # Check for hardcoded credentials
        if re.search(r"(password|api_key|secret|token)\s*=\s*['\"]([^'\"]+)['\"]", content):
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if re.search(r"(password|api_key|secret|token)\s*=\s*['\"]([^'\"]+)['\"]", line):
                    issues.append(CodeIssue(
                        file=file_path,
                        line_number=i,
                        issue="Potential hardcoded credentials detected",
                        suggestion="Use environment variables or configuration management for sensitive data"
                    ))
        
        return issues
