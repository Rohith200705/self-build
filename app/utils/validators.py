"""
Utility functions for common operations.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False


def sanitize_path(path: Path) -> bool:
    """
    Check if path is safe (prevent path traversal attacks).
    
    Args:
        path: Path object to check
        
    Returns:
        True if safe, False otherwise
    """
    try:
        path.resolve().relative_to(Path(__file__).parent.parent.parent / "temp_uploads")
        return True
    except ValueError:
        return False


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain name or None
    """
    try:
        parsed = urlparse(str(url))
        return parsed.netloc
    except Exception as e:
        logger.error(f"Error extracting domain: {e}")
        return None


def is_code_file(filename: str) -> bool:
    """
    Check if file is a code file by extension.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if code file, False otherwise
    """
    from app.core.config import ALLOWED_CODE_EXTENSIONS
    
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_CODE_EXTENSIONS


def detect_blocking_patterns(code: str) -> list:
    """
    Detect simple blocking patterns in code.
    
    Args:
        code: Code string to analyze
        
    Returns:
        List of detected blocking patterns
    """
    patterns = [
        (r"requests\.", "Blocking HTTP library (use httpx with async)"),
        (r"\.sleep\(", "Blocking sleep call"),
        (r"urllib\.request", "Blocking HTTP library"),
        (r"time\.sleep\(", "Blocking sleep detected"),
    ]
    
    issues = []
    for pattern, message in patterns:
        if re.search(pattern, code):
            issues.append(message)
    
    return issues


def detect_try_except_blocks(code: str, line_number: int = 0) -> bool:
    """
    Check if code section is wrapped in try/except.
    
    Args:
        code: Code string
        line_number: Line number context
        
    Returns:
        True if try/except found, False otherwise
    """
    return "try:" in code and "except" in code


def detect_request_timeout(code: str) -> bool:
    """
    Check if HTTP requests have timeout specified.
    
    Args:
        code: Code string to analyze
        
    Returns:
        True if timeout found, False otherwise
    """
    return bool(re.search(r"timeout\s*=", code)) or bool(re.search(r"timeout:\s*\d+", code))


class ProgressTracker:
    """Track progress of async operations."""
    
    def __init__(self, total: int):
        """Initialize progress tracker."""
        self.total = total
        self.current = 0
        self.start_time = datetime.utcnow()
    
    def update(self, amount: int = 1):
        """Update progress."""
        self.current += amount
    
    def get_percentage(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()
