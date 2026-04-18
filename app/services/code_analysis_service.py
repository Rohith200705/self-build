"""
Code analysis service for detecting issues in source code.
Supports multiple languages: Python, JavaScript/TypeScript, Java, C#, Go, and more.
"""

import logging
import re
import zipfile
from pathlib import Path
from typing import List

from app.models.schemas import CodeIssue, CodeAnalysisResponse
from app.core.config import TEMP_UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_CODE_EXTENSIONS
from app.utils.validators import is_code_file
from app.services.multi_language_analyzer import MultiLanguageCodeAnalyzer

logger = logging.getLogger(__name__)


class CodeAnalysisService:
    """Service for analyzing source code for issues across multiple languages."""
    
    def __init__(self):
        """Initialize code analysis service."""
        self.temp_dir = TEMP_UPLOAD_DIR
        self.max_size = MAX_UPLOAD_SIZE
        self.allowed_extensions = ALLOWED_CODE_EXTENSIONS
        self.multi_analyzer = MultiLanguageCodeAnalyzer()
    
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
        Analyze a single file for issues using language-specific analyzers.
        
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
        rel_path = str(file_path.name)
        
        # Use multi-language analyzer
        try:
            analysis_issues = self.multi_analyzer.analyze(content, str(file_path))
            
            # Convert to CodeIssue objects
            for issue in analysis_issues:
                issues.append(CodeIssue(
                    file=rel_path,
                    line_number=issue.get("line"),
                    issue=issue.get("issue", "Unknown issue"),
                    suggestion=issue.get("suggestion", "Review the code")
                ))
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
        
        return issues
