"""
HTTP Client Utilities
Centralized HTTP operations with retry logic, rate limiting, and error handling
"""

import asyncio
import time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class HTTPResponse:
    """Standardized HTTP response wrapper"""
    status_code: int
    content: str
    headers: Dict[str, str]
    success: bool
    error: Optional[str] = None
    
    @property
    def json(self) -> Optional[Dict]:
        """Parse response as JSON"""
        try:
            return json.loads(self.content)
        except (json.JSONDecodeError, TypeError):
            return None


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_second: float = 1.0
    burst_size: int = 5
    
    
class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: List[float] = []
        
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = time.time()
        
        # Remove old requests outside the window
        cutoff = now - 1.0  # 1 second window
        self.requests = [req_time for req_time in self.requests if req_time > cutoff]
        
        # Check if we need to wait
        if len(self.requests) >= self.config.requests_per_second:
            sleep_time = 1.0 / self.config.requests_per_second
            await asyncio.sleep(sleep_time)
            
        self.requests.append(now)


class HTTPClient:
    """
    Centralized HTTP client with retry logic, rate limiting, and error handling
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit: Optional[RateLimitConfig] = None,
        user_agent: str = "Wikipedia-Podcast-Pipeline/1.0"
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.rate_limiter = RateLimiter(rate_limit) if rate_limit else None
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Default headers
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/html, */*',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    async def get(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> HTTPResponse:
        """Make GET request with rate limiting and error handling"""
        return await self._request(HTTPMethod.GET, url, params=params, headers=headers)
    
    async def post(self, url: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, 
                   headers: Optional[Dict] = None) -> HTTPResponse:
        """Make POST request with rate limiting and error handling"""
        return await self._request(HTTPMethod.POST, url, data=data, json_data=json_data, headers=headers)
    
    def get_sync(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> HTTPResponse:
        """Synchronous GET request (for compatibility with existing code)"""
        return asyncio.run(self.get(url, params, headers))
    
    def post_sync(self, url: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None,
                  headers: Optional[Dict] = None) -> HTTPResponse:
        """Synchronous POST request (for compatibility with existing code)"""
        return asyncio.run(self.post(url, data, json_data, headers))
    
    async def _request(
        self,
        method: HTTPMethod,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> HTTPResponse:
        """Internal request method with rate limiting and error handling"""
        
        # Apply rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        # Merge headers
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)
        
        try:
            # Make the request
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.request(
                    method.value,
                    url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=req_headers,
                    timeout=self.timeout
                )
            )
            
            return HTTPResponse(
                status_code=response.status_code,
                content=response.text,
                headers=dict(response.headers),
                success=response.status_code < 400
            )
            
        except requests.exceptions.RequestException as e:
            return HTTPResponse(
                status_code=0,
                content="",
                headers={},
                success=False,
                error=str(e)
            )
    
    def close(self):
        """Close the session"""
        self.session.close()


# Convenience factory functions
def create_wikipedia_client() -> HTTPClient:
    """Create HTTP client optimized for Wikipedia API"""
    return HTTPClient(
        timeout=30,
        max_retries=3,
        rate_limit=RateLimitConfig(requests_per_second=2.0),  # Be respectful to Wikipedia
        user_agent="Wikipedia-Podcast-Pipeline/1.0 (Educational Use)"
    )


def create_openai_client() -> HTTPClient:
    """Create HTTP client optimized for OpenAI API"""
    return HTTPClient(
        timeout=60,  # Longer timeout for AI generation
        max_retries=2,
        rate_limit=RateLimitConfig(requests_per_second=0.5),  # More conservative for paid API
        user_agent="Wikipedia-Podcast-Pipeline/1.0"
    )


def create_generic_client() -> HTTPClient:
    """Create general-purpose HTTP client"""
    return HTTPClient(
        timeout=30,
        max_retries=3,
        user_agent="Wikipedia-Podcast-Pipeline/1.0"
    )