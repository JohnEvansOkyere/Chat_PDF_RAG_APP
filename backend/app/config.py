# backend/app/config.py
"""
Fixed configuration with correct Pydantic imports
"""
import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import validator
import json

class Settings(BaseSettings):
    """Application settings with Grok and Claude support"""
    
    # Application
    app_name: str = "VexaAI RAG Chat PDF API"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str
    supabase_url: str
    supabase_service_role_key: str
    
    # LLM Configuration - Choose provider
    llm_provider: str = "grok"  # grok, claude, openai
    
    # Grok (X.AI) Configuration
    grok_api_key: str = ""
    grok_model: str = "grok-beta"
    
    # Claude (Anthropic) Configuration
    claude_api_key: str = ""
    claude_model: str = "claude-3-sonnet-20240229"
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # Embedding Configuration
    embedding_provider: str = "openai"  # openai, cohere
    openai_embedding_model: str = "text-embedding-3-large"
    
    # Cohere Configuration
    cohere_api_key: str = ""
    cohere_embedding_model: str = "embed-english-v3.0"
    
    # Processing Configuration
    max_file_size_mb: int = 50
    chunk_size: int = 1000
    chunk_overlap: int = 200
    similarity_search_k: int = 5
    relevance_threshold: float = 0.7
    max_context_length: int = 8000
    max_response_length: int = 500
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # CORS - Updated with production URLs
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:3001,https://localhost:3000,https://chat-pdf-rag-app.vercel.app,https://chat-pdf-rag-app.onrender.com"    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from various formats"""
        if isinstance(v, str):
            # Handle JSON-like format from .env
            if v.startswith('[') and v.endswith(']'):
                try:
                    # Try to parse as JSON first
                    return json.loads(v)
                except json.JSONDecodeError:
                    # If JSON parsing fails, manually parse
                    origins_str = v.strip('[]').strip()
                    if not origins_str:
                        return ["http://localhost:3000"]
                    # Split by comma and clean up
                    origins = []
                    for origin in origins_str.split(','):
                        origin = origin.strip().strip('"\'')
                        if origin:
                            origins.append(origin)
                    return origins if origins else ["http://localhost:3000"]
            
            # Handle comma-separated format
            elif ',' in v:
                origins = [origin.strip() for origin in v.split(',') if origin.strip()]
                return origins if origins else ["http://localhost:3000"]
            
            # Handle single URL
            else:
                return [v.strip()] if v.strip() else ["http://localhost:3000"]
        
        # If it's already a list, return as is
        elif isinstance(v, list):
            return v
        
        # Fallback
        return ["http://localhost:3000"]
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def current_llm_config(self) -> dict:
        """Get current LLM configuration based on provider"""
        if self.llm_provider == "grok":
            return {
                "provider": "grok",
                "api_key": self.grok_api_key,
                "model": self.grok_model
            }
        elif self.llm_provider == "claude":
            return {
                "provider": "claude",
                "api_key": self.claude_api_key,
                "model": self.claude_model
            }
        elif self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    @property
    def current_embedding_config(self) -> dict:
        """Get current embedding configuration"""
        if self.embedding_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_embedding_model
            }
        elif self.embedding_provider == "cohere":
            return {
                "provider": "cohere",
                "api_key": self.cohere_api_key,
                "model": self.cohere_embedding_model
            }
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()