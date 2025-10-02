# backend/app/models.py
"""
Pydantic models for the FastAPI application.

These models define the data structures used for:
- Authentication (registration, login)
- Chat (requests, responses, sessions)
- Documents (uploads, metadata, info)
- Users (profiles)
- Errors & health checks

They provide schema validation, OpenAPI docs support, and ensure 
consistent data flow across the API.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

# ---------------------------------------------------------
# Base model with common config
# ---------------------------------------------------------
class BaseModelWithConfig(BaseModel):
    """
    Base Pydantic model with shared configuration:
    - Ensures correct serialization of datetime and UUID fields
    - Useful for models that are returned in API responses
    """
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }

# ---------------------------------------------------------
# Authentication Models
# ---------------------------------------------------------
class UserRegistrationRequest(BaseModel):
    """
    Request model for user registration.
    
    Fields:
        - email: must be valid email format
        - password: minimum 6 characters
        - display_name: optional user-facing name
    """
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = None

class UserLoginRequest(BaseModel):
    """
    Request model for user login.
    
    Fields:
        - email: registered email address
        - password: account password
    """
    email: str
    password: str

# ---------------------------------------------------------
# Chat Models
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    """
    Request model for sending a chat message.
    
    Fields:
        - message: user query text
        - document_id: optional reference to a specific document
        - stream: whether to stream responses (True/False)
    """
    message: str = Field(..., min_length=1, max_length=4000)
    document_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    """
    Response model for chat API.
    
    Fields:
        - message_id: unique identifier for the response
        - content: generated answer
        - sources: list of document chunks used for grounding
        - metadata: any additional context
        - created_at: timestamp of the response
    """
    message_id: str
    content: str
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatSession(BaseModelWithConfig):
    """
    Model representing a chat session.
    
    Fields:
        - id: session ID
        - title: session title (default: "New Chat")
        - document_id: optional linked document
        - message_count: number of messages exchanged
        - created_at: creation timestamp
        - updated_at: last update timestamp
    """
    id: str
    title: str = "New Chat"
    document_id: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------
# Document Models
# ---------------------------------------------------------
class DocumentUploadResponse(BaseModel):
    """
    Response returned after document upload.
    
    Fields:
        - document_id: assigned ID
        - filename: stored filename
        - status: upload status (processing, completed, failed)
        - message: additional info
    """
    document_id: str
    filename: str
    status: str
    message: str

class DocumentInfo(BaseModelWithConfig):
    """
    Model containing full document metadata.
    
    Fields:
        - id: document ID
        - filename: stored filename
        - original_filename: original name uploaded by user
        - file_size: size in bytes
        - mime_type: default "application/pdf"
        - status: processing state
        - error_message: optional error if processing failed
        - page_count: number of pages (if PDF)
        - chunk_count: number of text chunks extracted
        - metadata: additional metadata
        - created_at: upload timestamp
        - updated_at: last update timestamp
    """
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str = "application/pdf"
    status: str = "processing"  # Options: processing, completed, failed
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: int = 0
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------
# User Models
# ---------------------------------------------------------
class UserProfile(BaseModelWithConfig):
    """
    Model representing a user profile.
    
    Fields:
        - id: user ID
        - email: account email
        - display_name: optional display name
        - avatar_url: optional profile picture
        - subscription_tier: free, premium, etc.
        - api_usage_count: number of API calls made
        - api_usage_limit: max allowed API calls
        - created_at: account creation timestamp
        - updated_at: last profile update
    """
    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: str = "free"
    api_usage_count: int = 0
    api_usage_limit: int = 100
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------
# Error & Health Check Models
# ---------------------------------------------------------
class ErrorResponse(BaseModel):
    """
    Standard error response model for API endpoints.
    
    Fields:
        - error: short error code/label
        - message: human-readable error message
        - details: optional debug info
        - timestamp: time of error occurrence
    """
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthCheck(BaseModel):
    """
    Model returned for health check endpoint.
    
    Fields:
        - status: health status (e.g., "ok")
        - timestamp: check execution time
        - version: app version
        - environment: current environment (dev, prod)
    """
    status: str
    timestamp: datetime
    version: str
    environment: str
