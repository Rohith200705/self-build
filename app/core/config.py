"""
Core configuration for the application.
"""

import logging
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMP_UPLOAD_DIR = BASE_DIR / "temp_uploads"
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

# Application settings
APP_NAME = "AI-Powered Website Reliability Analyzer"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "API for analyzing website health, performance, and code quality"

# HTTP Client settings
HTTP_TIMEOUT = 30  # seconds
HTTP_RETRIES = 2
HTTP_MAX_CONNECTIONS = 100

# File Upload settings
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_ARCHIVE_FORMATS = {".zip"}
ALLOWED_CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cs", ".go"}

# Load Testing settings
MAX_CONCURRENT_REQUESTS = 100
LOAD_TEST_TIMEOUT = 120  # seconds
DEFAULT_USERS = 10
DEFAULT_REQUESTS_PER_USER = 5

# GitHub settings
GITHUB_TIMEOUT = 60
GIT_CLONE_TIMEOUT = 120

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# Stream handler
handler = logging.StreamHandler()
handler.setLevel(LOG_LEVEL)
formatter = logging.Formatter(LOG_FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)
