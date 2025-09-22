# backend/app/middleware/rate_limiter.py
"""
Rate limiting middleware
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Deque
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        # Remove requests older than an hour
        while self.requests[client_ip] and self.requests[client_ip][0] < hour_ago:
            self.requests[client_ip].popleft()
        
        # Check rate limits
        requests_last_minute = sum(1 for req_time in self.requests[client_ip] if req_time > minute_ago)
        requests_last_hour = len(self.requests[client_ip])
        
        if requests_last_minute >= settings.rate_limit_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}: {requests_last_minute} requests/minute")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {settings.rate_limit_per_minute} per minute",
                    "retry_after": 60
                }
            )
        
        if requests_last_hour >= settings.rate_limit_per_hour:
            logger.warning(f"Rate limit exceeded for {client_ip}: {requests_last_hour} requests/hour")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {settings.rate_limit_per_hour} per hour",
                    "retry_after": 3600
                }
            )
        
        # Record this request
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        return response

