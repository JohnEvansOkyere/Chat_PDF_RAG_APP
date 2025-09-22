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

# backend/app/middleware/logging_middleware.py
"""
Request logging middleware
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"{request.method} {request.url.path} - "
            f"{process_time:.3f}s"
        )
        
        # Add processing time to headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

# backend/app/utils/exceptions.py
"""
Exception handlers
"""

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url.path}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()} - {request.method} {request.url.path}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "errors": exc.errors(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)} - {request.method} {request.url.path}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# backend/app/database.py
"""
Database connection utilities
"""

from supabase import create_client, Client
from app.config import settings

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    return _supabase_client

# backend/app/__init__.py
"""
VexaAI RAG Chat PDF Backend Application
"""

__version__ = "1.0.0"
__author__ = "John Evans Okyere"