"""
VexaAI RAG Chat PDF - FastAPI Backend
Developed by: John Evans Okyere
Optimized for Render deployment
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
import uvicorn
from typing import List, Optional
from datetime import datetime, timedelta

try:
    from app.config import settings
    from app.database import get_supabase_client
    from app.models import (
        ChatRequest, ChatResponse, DocumentUploadResponse, 
        ChatSession, UserProfile, DocumentInfo,
        UserRegistrationRequest, UserLoginRequest
    )
    from app.services.auth_service import AuthService
    from app.services.document_service import DocumentService
    from app.services.chat_service import ChatService
    from app.services.vector_service import VectorService
    from app.services.llm_service import LLMService
    from app.middleware.rate_limiter import RateLimitMiddleware
    from app.middleware.logging_middleware import LoggingMiddleware
    from app.utils.exceptions import setup_exception_handlers
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure all required modules are created in the app/ directory")
    print("Check your project structure and .env file configuration")
    exit(1)

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
    """Optimized application lifespan management for production deployment"""
    # Startup
    logger.info("Starting VexaAI RAG Chat PDF API")
    
    # Skip heavy startup checks in production to avoid timeout
    if settings.environment == "production":
        logger.info("Production mode: Starting with minimal checks")
        try:
            # Quick database ping only
            supabase = get_supabase_client()
            supabase.table('user_profiles').select('id').limit(1).execute()
            logger.info("Database connection verified")
        except Exception as e:
            logger.warning(f"Database check failed: {e}")
        
        logger.info("Production startup completed")
    else:
        # Development mode - run full checks with timeouts
        logger.info("Development mode: Running full startup checks")
        
        startup_tasks = []
        
        async def test_database():
            try:
                supabase = get_supabase_client()
                response = supabase.table('user_profiles').select('id').limit(1).execute()
                logger.info("Database connection successful")
                return True
            except Exception as e:
                logger.warning(f"Database connection failed: {e}")
                return False
        
        async def test_llm():
            try:
                test_response = await llm_service.test_connection()
                logger.info("LLM connection successful")
                return True
            except Exception as e:
                logger.warning(f"LLM connection failed: {e}")
                return False
        
        async def test_vector():
            try:
                await vector_service.test_embeddings()
                logger.info("Vector service initialized successfully")
                return True
            except Exception as e:
                logger.warning(f"Vector service failed: {e}")
                return False
        
        try:
            # Run all checks concurrently with timeout
            startup_tasks = [test_database(), test_llm(), test_vector()]
            results = await asyncio.wait_for(
                asyncio.gather(*startup_tasks, return_exceptions=True),
                timeout=10.0
            )
            logger.info("Development startup completed")
        except asyncio.TimeoutError:
            logger.warning("Startup checks timed out, continuing anyway")
        except Exception as e:
            logger.warning(f"Startup checks failed: {e}, continuing anyway")
    
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

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint for basic health check"""
    return {
        "message": "VexaAI RAG Chat PDF API is running",
        "status": "active",
        "version": "1.0.0",
        "docs": "/api/docs",
        "environment": settings.environment
    }

@app.get("/health")
async def simple_health_check():
    """Simple health check without dependencies"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VexaAI RAG Chat PDF API",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Primary health check endpoint for Render"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.environment,
            "service": "VexaAI RAG Chat PDF API"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register")
async def register(request: UserRegistrationRequest):
    """Register a new user"""
    try:
        user = await auth_service.register_user(request.email, request.password, request.display_name)
        return {"user": user, "message": "Registration successful"}
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(request: UserLoginRequest):
    """Login user"""
    try:
        result = await auth_service.login_user(request.email, request.password)
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

# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

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
        try:
            supabase = get_supabase_client()
            supabase.table('documents').update({
                'status': 'failed',
                'error_message': str(e),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', document_id).execute()
        except Exception as update_error:
            logger.error(f"Failed to update document status: {update_error}")

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
        
        if hasattr(file, 'size') and file.size and file.size > settings.max_file_size_bytes:
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# ============================================================================
# CHAT MANAGEMENT ENDPOINTS
# ============================================================================

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
            try:
                async for chunk in chat_service.process_message_stream(
                    session_id=session_id,
                    user_id=current_user["id"],
                    message=request.message,
                    document_id=request.document_id
                ):
                    yield f"data: {chunk}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
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

# ============================================================================
# SEARCH & ANALYTICS ENDPOINTS
# ============================================================================

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

@app.get("/api/usage/stats")
async def get_usage_stats(current_user: dict = Depends(get_current_user)):
    """Get user's API usage statistics"""
    try:
        stats = await auth_service.get_usage_stats(current_user["id"])
        return stats
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug if hasattr(settings, 'debug') else False,
        log_level=settings.log_level.lower() if hasattr(settings, 'log_level') else "info",
        workers=1,  # Single worker for free tier
        timeout_keep_alive=65
    )