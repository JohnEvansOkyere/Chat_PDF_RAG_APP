# backend/main.py
"""
VexaAI RAG Chat PDF - FastAPI Backend
Developed by: John Evans Okyere
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse

import uvicorn
from typing import List, Optional
import asyncio
from datetime import datetime, timedelta

from app.config import settings
from app.database import get_supabase_client
from app.models import (
    ChatRequest, ChatResponse, DocumentUploadResponse, 
    ChatSession, UserProfile, DocumentInfo
)
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.chat_service import ChatService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.utils.exceptions import setup_exception_handlers
from app.api import auth


app = FastAPI(title="VexaAI RAG Chat PDF API")
app.include_router(auth.router, prefix="/api/auth")



# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
auth_service = AuthService()
document_service = DocumentService()
chat_service = ChatService()
vector_service = VectorService()
llm_service = LLMService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting VexaAI RAG Chat PDF API")
    
    # Test database connection
    try:
        supabase = get_supabase_client()
        response = supabase.table('user_profiles').select('count').limit(1).execute()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    # Test LLM connection
    try:
        test_response = await llm_service.test_connection()
        logger.info(f"LLM connection successful: {test_response}")
    except Exception as e:
        logger.error(f"LLM connection failed: {e}")
        raise
    
    # Test vector service
    try:
        await vector_service.test_embeddings()
        logger.info("Vector service initialized successfully")
    except Exception as e:
        logger.error(f"Vector service initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down VexaAI RAG Chat PDF API")

# Create FastAPI app
app = FastAPI(
    title="VexaAI RAG Chat PDF API",
    description="Backend API for VexaAI RAG Chat PDF Application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Setup middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Setup exception handlers
setup_exception_handlers(app)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "environment": settings.environment
    }

# Authentication endpoints
@app.post("/api/auth/register")
async def register(email: str, password: str, display_name: Optional[str] = None):
    """Register a new user"""
    try:
        user = await auth_service.register_user(email, password, display_name)
        return {"user": user, "message": "Registration successful"}
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(email: str, password: str):
    """Login user"""
    try:
        result = await auth_service.login_user(email, password)
        return result
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user"""
    try:
        await auth_service.logout_user(current_user["id"])
        return {"message": "Logout successful"}
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    try:
        profile = await auth_service.get_user_profile(current_user["id"])
        return profile
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=404, detail="Profile not found")

# Document management endpoints
@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and process PDF document"""
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        if file.size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )
        
        # Create document record
        document = await document_service.create_document(
            user_id=current_user["id"],
            file=file
        )
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            document["id"],
            current_user["id"]
        )
        
        return DocumentUploadResponse(
            document_id=document["id"],
            filename=document["filename"],
            status="processing",
            message="Document uploaded successfully. Processing in background."
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_background(document_id: str, user_id: str):
    """Background task to process uploaded document"""
    try:
        logger.info(f"Starting background processing for document {document_id}")
        
        # Process the document
        await document_service.process_document(document_id, user_id)
        
        logger.info(f"Document {document_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")
        
        # Update document status to failed
        supabase = get_supabase_client()
        supabase.table('documents').update({
            'status': 'failed',
            'error_message': str(e)
        }).eq('id', document_id).execute()

@app.get("/api/documents", response_model=List[DocumentInfo])
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List user's documents"""
    try:
        documents = await document_service.get_user_documents(current_user["id"])
        return documents
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document details"""
    try:
        document = await document_service.get_document(document_id, current_user["id"])
        return document
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=404, detail="Document not found")

@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete document"""
    try:
        await document_service.delete_document(document_id, current_user["id"])
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat management endpoints
@app.post("/api/chat/sessions", response_model=ChatSession)
async def create_chat_session(
    title: str = "New Chat",
    document_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create new chat session"""
    try:
        session = await chat_service.create_session(
            user_id=current_user["id"],
            title=title,
            document_id=document_id
        )
        return session
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/sessions", response_model=List[ChatSession])
async def list_chat_sessions(current_user: dict = Depends(get_current_user)):
    """List user's chat sessions"""
    try:
        sessions = await chat_service.get_user_sessions(current_user["id"])
        return sessions
    except Exception as e:
        logger.error(f"Failed to list chat sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get chat session with messages"""
    try:
        session = await chat_service.get_session_with_messages(
            session_id, 
            current_user["id"]
        )
        return session
    except Exception as e:
        logger.error(f"Failed to get chat session: {e}")
        raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/chat/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send message in chat session"""
    try:
        response = await chat_service.process_message(
            session_id=session_id,
            user_id=current_user["id"],
            message=request.message,
            document_id=request.document_id
        )
        return response
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/sessions/{session_id}/messages/stream")
async def send_message_stream(
    session_id: str,
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send message with streaming response"""
    try:
        async def generate_stream():
            async for chunk in chat_service.process_message_stream(
                session_id=session_id,
                user_id=current_user["id"],
                message=request.message,
                document_id=request.document_id
            ):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        logger.error(f"Failed to process streaming message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete chat session"""
    try:
        await chat_service.delete_session(session_id, current_user["id"])
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Vector search endpoint
@app.post("/api/search")
async def search_documents(
    query: str,
    document_id: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Search documents using vector similarity"""
    try:
        results = await vector_service.search_similar_chunks(
            user_id=current_user["id"],
            query=query,
            document_id=document_id,
            limit=limit
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Usage statistics
@app.get("/api/usage/stats")
async def get_usage_stats(current_user: dict = Depends(get_current_user)):
    """Get user's API usage statistics"""
    try:
        stats = await auth_service.get_usage_stats(current_user["id"])
        return stats
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )