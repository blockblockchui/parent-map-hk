"""
HTTP client with rate limiting, retry, and concurrency control
"""

import asyncio
import random
import time
from typing import Optional, Dict, Any, Callable
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)

from .config import config
from .cache import cache, compute_content_hash


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            
            # Add tokens based on time passed
            self.tokens = min(
                self.requests_per_minute,
                self.tokens + time_passed * (self.requests_per_minute / 60)
            )
            self.last_update = now
            
            if self.tokens < 1:
                # Wait for a token to be available
                wait_time = (1 - self.tokens) * (60 / self.requests_per_minute)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class HttpClient:
    """
    HTTP client with:
    - Rate limiting
    - Exponential backoff + jitter retry
    - Caching
    - Concurrency control
    - Timeout handling
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self.semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
        # HTTP client with timeout
        timeout = httpx.Timeout(
            connect=5.0,
            read=config.request_timeout,
            write=5.0,
            pool=5.0,
        )
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "ParentMap-HK-Bot/1.0 (Data Pipeline)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
            },
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get(
        self,
        url: str,
        use_cache: bool = True,
        cache_ttl_hours: Optional[int] = None,
        force_refresh: bool = False,
    ) -> httpx.Response:
        """
        Make a GET request with all safeguards
        
        Args:
            url: Target URL
            use_cache: Whether to use cache
            cache_ttl_hours: Cache TTL (default from config)
            force_refresh: Ignore cache and fetch fresh
        """
        cache_key = f"http:get:{url}"
        
        # Check cache first
        if use_cache and not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                # Reconstruct response from cache
                return self._response_from_cache(url, cached)
        
        # Acquire rate limit token
        await self.rate_limiter.acquire()
        
        # Make request with concurrency control
        async with self.semaphore:
            try:
                response = await self._fetch_with_retry(url)
                
                # Cache successful response
                if use_cache and response.status_code == 200:
                    content_hash = compute_content_hash(response.text)
                    cache.set(
                        cache_key,
                        {
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "text": response.text,
                            "url": str(response.url),
                        },
                        content_hash=content_hash,
                        ttl_hours=cache_ttl_hours,
                    )
                
                return response
                
            except Exception as e:
                # Log and re-raise
                raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=60, jitter=2),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.NetworkError,
        )),
        reraise=True,
    )
    async def _fetch_with_retry(self, url: str) -> httpx.Response:
        """Fetch URL with retry logic"""
        response = await self.client.get(url)
        
        # Raise for 4xx/5xx status codes (but not for 404 - that's expected for closed places)
        if response.status_code >= 500:
            response.raise_for_status()
        
        return response
    
    def _response_from_cache(self, url: str, cached: Dict) -> httpx.Response:
        """Reconstruct httpx.Response from cache"""
        return httpx.Response(
            status_code=cached["value"]["status_code"],
            headers=cached["value"]["headers"],
            text=cached["value"]["text"],
            request=httpx.Request("GET", url),
        )
    
    async def check_url(self, url: str) -> Dict[str, Any]:
        """
        Quick URL check for validation
        Returns status info without full content fetch
        """
        cache_key = f"http:check:{url}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached["value"]
        
        await self.rate_limiter.acquire()
        
        async with self.semaphore:
            try:
                # Use HEAD request first (lighter)
                response = await self.client.head(url, follow_redirects=True)
                
                result = {
                    "url": str(response.url),
                    "status_code": response.status_code,
                    "is_redirect": len(response.history) > 0,
                    "redirect_url": str(response.url) if response.history else None,
                    "headers": dict(response.headers),
                    "checked_at": time.time(),
                }
                
                # Cache check result (shorter TTL for status checks)
                cache.set(cache_key, result, ttl_hours=1)
                
                return result
                
            except httpx.HTTPStatusError as e:
                result = {
                    "url": url,
                    "status_code": e.response.status_code,
                    "error": str(e),
                    "checked_at": time.time(),
                }
                cache.set(cache_key, result, ttl_hours=1)
                return result
                
            except Exception as e:
                result = {
                    "url": url,
                    "status_code": None,
                    "error": str(e),
                    "checked_at": time.time(),
                }
                cache.set(cache_key, result, ttl_hours=1)
                return result
    
    async def batch_check_urls(
        self,
        urls: list,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Check multiple URLs concurrently"""
        results = {}
        
        async def check_one(url: str):
            result = await self.check_url(url)
            results[url] = result
            if progress_callback:
                progress_callback(url, result)
            return result
        
        # Process in batches to avoid overwhelming
        batch_size = config.max_concurrent_requests
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            await asyncio.gather(*[check_one(url) for url in batch])
        
        return results


# Sync wrapper for convenience
def check_url_sync(url: str) -> Dict[str, Any]:
    """Synchronous URL check"""
    return asyncio.run(HttpClient().check_url(url))
