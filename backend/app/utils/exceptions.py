
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