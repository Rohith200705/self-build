"""
GitHub repository analysis service.
"""

import logging
import shutil
import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from git import Repo
from git.exc import GitCommandError

from app.models.schemas import GitHubAnalysisResponse
from app.core.config import TEMP_UPLOAD_DIR, GIT_CLONE_TIMEOUT
from app.utils.validators import get_timestamp
from app.services.code_analysis_service import CodeAnalysisService

logger = logging.getLogger(__name__)


class GitHubAnalysisService:
    """Service for analyzing GitHub repositories."""
    
    def __init__(self):
        """Initialize GitHub analysis service."""
        self.temp_dir = TEMP_UPLOAD_DIR
        self.clone_timeout = GIT_CLONE_TIMEOUT
        self.code_service = CodeAnalysisService()
    
    async def analyze_repository(self, repo_url: str) -> GitHubAnalysisResponse:
        """
        Clone and analyze a GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            GitHubAnalysisResponse with analyzed code issues
        """
        clone_path = None
        
        try:
            # Validate and parse URL
            repo_name = self._extract_repo_name(repo_url)
            if not repo_name:
                logger.error(f"Invalid GitHub URL: {repo_url}")
                return GitHubAnalysisResponse(
                    repo_name="Unknown",
                    total_issues=0,
                    issues=[],
                    files_scanned=0,
                    analysis_timestamp=get_timestamp()
                )
            
            # Clone repository
            clone_path = self.temp_dir / repo_name
            logger.info(f"Cloning repository: {repo_url}")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: Repo.clone_from(repo_url, clone_path)
                ),
                timeout=self.clone_timeout
            )
            
            logger.info(f"Repository cloned successfully to {clone_path}")
            
            # Analyze the repository
            analysis = await self.code_service.analyze_repository(str(clone_path))
            
            return GitHubAnalysisResponse(
                repo_name=repo_name,
                total_issues=analysis.total_issues,
                issues=analysis.issues,
                files_scanned=analysis.files_scanned,
                analysis_timestamp=get_timestamp()
            )
        
        except asyncio.TimeoutError:
            logger.error(f"Repository clone timeout: {repo_url}")
            return GitHubAnalysisResponse(
                repo_name=self._extract_repo_name(repo_url) or "Unknown",
                total_issues=0,
                issues=[],
                files_scanned=0,
                analysis_timestamp=get_timestamp()
            )
        except GitCommandError as e:
            logger.error(f"Git command error: {e}")
            return GitHubAnalysisResponse(
                repo_name=self._extract_repo_name(repo_url) or "Unknown",
                total_issues=0,
                issues=[],
                files_scanned=0,
                analysis_timestamp=get_timestamp()
            )
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            return GitHubAnalysisResponse(
                repo_name=self._extract_repo_name(repo_url) or "Unknown",
                total_issues=0,
                issues=[],
                files_scanned=0,
                analysis_timestamp=get_timestamp()
            )
        finally:
            # Clean up cloned repository
            if clone_path and clone_path.exists():
                try:
                    shutil.rmtree(clone_path)
                    logger.info(f"Cleaned up repository clone: {clone_path}")
                except Exception as e:
                    logger.warning(f"Error cleaning up repository: {e}")
    
    def _extract_repo_name(self, repo_url: str) -> Optional[str]:
        """
        Extract repository name from GitHub URL.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Repository name in format owner/repo
        """
        try:
            # Handle various GitHub URL formats
            if "github.com" not in repo_url:
                return None
            
            # Parse the URL
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip("/").split("/")
            
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].rstrip(".git")
                return f"{owner}/{repo}"
            
            return None
        except Exception as e:
            logger.error(f"Error parsing GitHub URL: {e}")
            return None
