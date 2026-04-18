"""
Load testing service for performance simulation.
"""

import logging
import time
import asyncio
from typing import List, Dict
import httpx

from app.models.schemas import LoadTestResponse
from app.core.config import HTTP_TIMEOUT, MAX_CONCURRENT_REQUESTS, LOAD_TEST_TIMEOUT
from app.utils.validators import validate_url

logger = logging.getLogger(__name__)


class LoadTestService:
    """Service for performing load testing on websites."""
    
    def __init__(self):
        """Initialize load test service."""
        self.timeout = HTTP_TIMEOUT
        self.load_test_timeout = LOAD_TEST_TIMEOUT
        self.max_concurrent = MAX_CONCURRENT_REQUESTS
    
    async def run_load_test(
        self,
        url: str,
        users: int = 10,
        requests_per_user: int = 5
    ) -> LoadTestResponse:
        """
        Run a load test on the specified URL.
        
        Args:
            url: Website URL to test
            users: Number of concurrent users
            requests_per_user: Requests per user
            
        Returns:
            LoadTestResponse with performance metrics
        """
        # Validate URL
        if not validate_url(url):
            logger.error(f"Invalid URL for load test: {url}")
            return LoadTestResponse(
                avg_latency=0.0,
                total_requests=0,
                failed_requests=0,
                failure_rate=0.0,
                min_latency=0.0,
                max_latency=0.0
            )
        
        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        # Limit concurrent requests
        users = min(users, self.max_concurrent)
        total_requests = users * requests_per_user
        
        try:
            latencies = []
            failed_count = 0
            
            # Create semaphore to limit concurrency
            semaphore = asyncio.Semaphore(users)
            
            async def single_request() -> float:
                """Make a single request and return latency."""
                nonlocal failed_count
                
                async with semaphore:
                    try:
                        async with httpx.AsyncClient(timeout=self.timeout) as client:
                            start = time.time()
                            response = await client.get(url, follow_redirects=True)
                            latency = time.time() - start
                            
                            # Consider 5xx errors as failures
                            if response.status_code >= 500:
                                failed_count += 1
                            
                            return latency
                    except asyncio.TimeoutError:
                        failed_count += 1
                        logger.warning(f"Load test request timeout for {url}")
                        return self.timeout
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Load test request failed for {url}: {e}")
                        return 0.0
            
            # Create all request tasks
            tasks = [single_request() for _ in range(total_requests)]
            
            # Run with timeout
            start_test = time.time()
            latencies = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False),
                timeout=self.load_test_timeout
            )
            test_duration = time.time() - start_test
            
            # Filter out zero latencies (failed requests)
            valid_latencies = [l for l in latencies if l > 0]
            
            if not valid_latencies:
                # All requests failed
                return LoadTestResponse(
                    avg_latency=0.0,
                    total_requests=total_requests,
                    failed_requests=failed_count,
                    failure_rate=1.0,
                    min_latency=0.0,
                    max_latency=0.0
                )
            
            avg_latency = sum(valid_latencies) / len(valid_latencies)
            min_latency = min(valid_latencies)
            max_latency = max(valid_latencies)
            failure_rate = failed_count / total_requests if total_requests > 0 else 0.0
            
            logger.info(
                f"Load test completed for {url}: "
                f"{total_requests} requests, "
                f"avg latency: {avg_latency:.3f}s, "
                f"failure rate: {failure_rate:.2%}"
            )
            
            return LoadTestResponse(
                avg_latency=round(avg_latency, 3),
                total_requests=total_requests,
                failed_requests=failed_count,
                failure_rate=round(failure_rate, 3),
                min_latency=round(min_latency, 3),
                max_latency=round(max_latency, 3)
            )
        
        except asyncio.TimeoutError:
            logger.error(f"Load test timeout for {url}")
            return LoadTestResponse(
                avg_latency=0.0,
                total_requests=total_requests,
                failed_requests=total_requests,
                failure_rate=1.0,
                min_latency=0.0,
                max_latency=0.0
            )
        except Exception as e:
            logger.error(f"Unexpected error in load test for {url}: {e}")
            return LoadTestResponse(
                avg_latency=0.0,
                total_requests=0,
                failed_requests=0,
                failure_rate=0.0,
                min_latency=0.0,
                max_latency=0.0
            )
