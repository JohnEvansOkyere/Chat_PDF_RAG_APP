# backend/app/services/auth_service.py
"""
Authentication service
"""

import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def register_user(self, email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Register new user"""
        try:
            # Use Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "display_name": display_name or email.split("@")[0]
                    }
                }
            })
            
            if auth_response.user:
                return {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "display_name": display_name
                }
            else:
                raise Exception("User registration failed")
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                return {
                    "access_token": auth_response.session.access_token,
                    "token_type": "bearer",
                    "expires_in": auth_response.session.expires_in,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "display_name": auth_response.user.user_metadata.get("display_name")
                    }
                }
            else:
                raise Exception("Login failed")
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            # Use Supabase to verify token
            auth_response = self.supabase.auth.get_user(token)
            
            if auth_response.user:
                return {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "display_name": auth_response.user.user_metadata.get("display_name")
                }
            else:
                raise Exception("Invalid token")
                
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise
    
    async def logout_user(self, user_id: str):
        """Logout user"""
        try:
            self.supabase.auth.sign_out()
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            raise
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        response = self.supabase.table('user_profiles').select('*').eq('id', user_id).single().execute()
        
        if response.data:
            return response.data
        else:
            raise Exception("Profile not found")
    
    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user usage statistics"""
        try:
            # Get usage from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            usage_response = self.supabase.table('api_usage').select('*').eq('user_id', user_id).gte('created_at', thirty_days_ago.isoformat()).execute()
            
            usage_data = usage_response.data or []
            
            total_requests = len(usage_data)
            total_tokens = sum(record.get('tokens_used', 0) for record in usage_data)
            
            # Get today's usage
            today = datetime.utcnow().date()
            today_usage = [record for record in usage_data if record['created_at'].startswith(str(today))]
            
            return {
                "total_requests": total_requests,
                "requests_today": len(today_usage),
                "total_tokens_used": total_tokens,
                "tokens_today": sum(record.get('tokens_used', 0) for record in today_usage),
                "average_response_time": sum(record.get('response_time', 0) for record in usage_data) / max(len(usage_data), 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise

# backend/app/utils/pdf_processor.py
"""
PDF processing utility adapted from original code
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """Validate PDF file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            if not file_path.lower().endswith('.pdf'):
                logger.error(f"Invalid file extension: {file_path}")
                return False
            
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                logger.error(f"File too large: {file_size_mb:.2f}MB > {settings.max_file_size_mb}MB")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating PDF file: {str(e)}")
            return False
    
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF file and return chunks with metadata"""
        try:
            if not self.validate_pdf_file(file_path):
                raise ValueError(f"Invalid PDF file: {file_path}")
            
            logger.info(f"Processing PDF: {file_path}")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(file_path)
            
            pages_text = []
            total_text = ""
            
            # Extract text from each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                
                pages_text.append({
                    'page_number': page_num + 1,
                    'content': page_text,
                    'metadata': {
                        'source_file': os.path.basename(file_path),
                        'page_number': page_num + 1,
                        'total_pages': doc.page_count
                    }
                })
                
                total_text += page_text + "\n\n"
            
            doc.close()
            
            if not total_text.strip():
                raise ValueError("No content found in PDF")
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(total_text)
            
            # Create chunk objects with metadata
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Find which page this chunk belongs to
                page_number = self._find_page_for_chunk(chunk, pages_text)
                
                chunk_obj = {
                    'content': chunk,
                    'chunk_index': i,
                    'metadata': {
                        'source_file': os.path.basename(file_path),
                        'chunk_id': i,
                        'page_number': page_number,
                        'total_chunks': len(chunks)
                    },
                    'page_number': page_number,
                    'start_index': total_text.find(chunk)
                }
                
                processed_chunks.append(chunk_obj)
            
            # Generate statistics
            stats = {
                'total_pages': doc.page_count if 'doc' in locals() else len(pages_text),
                'total_chunks': len(processed_chunks),
                'total_characters': len(total_text),
                'total_words': len(total_text.split()),
                'average_chunk_size': len(total_text) // len(processed_chunks) if processed_chunks else 0
            }
            
            # Generate preview
            preview = total_text[:500] + "..." if len(total_text) > 500 else total_text
            
            logger.info(f"Successfully processed PDF: {stats['total_chunks']} chunks from {stats['total_pages']} pages")
            
            return {
                'chunks': processed_chunks,
                'stats': stats,
                'preview': preview
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    def _find_page_for_chunk(self, chunk: str, pages_text: List[Dict]) -> int:
        """Find which page a chunk belongs to"""
        for page_data in pages_text:
            if chunk[:100] in page_data['content']:
                return page_data['page_number']
        return 1  # Default to page 1 if not found

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

# backend/requirements.txt
"""
Backend requirements for VexaAI RAG Chat PDF API
"""

# FastAPI and server
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
supabase==2.0.2
psycopg2-binary==2.9.7
asyncpg==0.28.0

# LLM integrations
openai==1.3.5
anthropic==0.7.7
cohere==4.37

# PDF processing
PyMuPDF==1.23.8
pdfplumber==0.10.3

# Text processing
langchain==0.0.340
langchain-text-splitters==0.0.1
tiktoken==0.5.1

# Authentication and security
PyJWT==2.8.0
bcrypt==4.0.1
cryptography==41.0.7
python-jose[cryptography]==3.3.0

# HTTP and async
httpx==0.25.2
aiofiles==23.2.1

# Configuration and environment
pydantic[email]==2.5.0
python-dotenv==1.0.0
pydantic-settings==2.0.3

# Utilities
python-json-logger==2.0.7
structlog==23.2.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2  # for testing

# Development
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1