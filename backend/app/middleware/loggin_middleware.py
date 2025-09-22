# backend/app/middleware/logging_middleware.py
"""
Request logging middleware
"""

import time
import logging
import json
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
