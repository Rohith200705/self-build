"""
Health check service for website monitoring.
"""

import logging
import time
from typing import Optional
import httpx

from app.models.schemas import HealthCheckResponse
from app.core.config import HTTP_TIMEOUT, HTTP_RETRIES
from app.utils.validators import validate_url

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for performing website health checks."""
    
    def __init__(self):
        """Initialize health check service."""
        self.timeout = HTTP_TIMEOUT
        self.retries = HTTP_RETRIES
    
    async def check_health(self, url: str) -> HealthCheckResponse:
        """
        Check health of a website by sending a HEAD or GET request.
        
        Args:
            url: Website URL to check
            
        Returns:
            HealthCheckResponse with status and latency information
        """
        # Validate URL
        if not validate_url(url):
            logger.error(f"Invalid URL: {url}")
            return HealthCheckResponse(
                status="DOWN",
                status_code=None,
                latency=0.0,
                message="Invalid URL format"
            )
        
        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = time.time()
                
                try:
                    # Try HEAD request first (faster)
                    response = await client.head(url, follow_redirects=True)
                except Exception:
                    # Fall back to GET request
                    try:
                        response = await client.get(url, follow_redirects=True)
                    except Exception as e:
                        logger.error(f"Health check failed for {url}: {e}")
                        return HealthCheckResponse(
                            status="DOWN",
                            status_code=None,
                            latency=0.0,
                            message=f"Connection failed: {str(e)}"
                        )
                
                latency = time.time() - start_time
                
                # Determine status based on status code
                if 200 <= response.status_code < 400:
                    status = "UP"
                    message = f"Website is healthy (HTTP {response.status_code})"
                elif 400 <= response.status_code < 500:
                    status = "UP"  # Server is responding but with client error
                    message = f"Website is up but returns client error (HTTP {response.status_code})"
                else:
                    status = "UP"  # Server is responding but with server error
                    message = f"Website is up but returns server error (HTTP {response.status_code})"
                
                return HealthCheckResponse(
                    status=status,
                    status_code=response.status_code,
                    latency=round(latency, 3),
                    message=message
                )
        
        except httpx.TimeoutException:
            logger.warning(f"Health check timeout for {url}")
            return HealthCheckResponse(
                status="DOWN",
                status_code=None,
                latency=self.timeout,
                message="Request timeout"
            )
        except Exception as e:
            logger.error(f"Unexpected error in health check for {url}: {e}")
            return HealthCheckResponse(
                status="DOWN",
                status_code=None,
                latency=0.0,
                message=f"Error: {str(e)}"
            )
    
    async def check_multiple(self, urls: list) -> list:
        """
        Check health of multiple websites concurrently.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            List of HealthCheckResponse objects
        """
        import asyncio
        
        tasks = [self.check_health(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
