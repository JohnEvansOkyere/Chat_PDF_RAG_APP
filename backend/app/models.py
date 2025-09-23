# backend/app/models.py
"""
Essential Pydantic models for the FastAPI application
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

# Base model with common config
class BaseModelWithConfig(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }

# Authentication models - Required by main.py
class UserRegistrationRequest(BaseModel):
    """User registration request"""
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = None

class UserLoginRequest(BaseModel):
    """User login request"""
    email: str
    password: str

# Chat models - Required by main.py
class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=4000)
    document_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    """Chat response model"""
    message_id: str
    content: str
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatSession(BaseModelWithConfig):
    """Chat session model"""
    id: str
    title: str = "New Chat"
    document_id: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

# Document models - Required by main.py
class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    document_id: str
    filename: str
    status: str
    message: str

class DocumentInfo(BaseModelWithConfig):
    """Document information model"""
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str = "application/pdf"
    status: str = "processing"  # processing, completed, failed
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: int = 0
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

# User models - Required by main.py
class UserProfile(BaseModelWithConfig):
    """User profile model"""
    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: str = "free"
    api_usage_count: int = 0
    api_usage_limit: int = 100
    created_at: datetime
    updated_at: datetime

# Error models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Health check model
class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    environment: str