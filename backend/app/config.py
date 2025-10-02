# backend/app/config.py
"""
Application configuration module.

This file defines and manages all environment-based configuration 
for the RAG application, including:
- Server details
- Security (JWT tokens)
- Database (Supabase)
- LLM providers (Grok, Claude, OpenAI)
- Embeddings (OpenAI, Cohere)
- Processing limits (chunking, context, file size)
- Rate limiting

Configuration values are primarily loaded from environment variables 
and can be customized via `.env` file.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings class.
    
    Uses Pydantic's BaseSettings to automatically read values 
    from environment variables. Default values are provided 
    where applicable.
    """
    
    # -------------------------------
    # Application Metadata
    # -------------------------------
    app_name: str = "VexaAI RAG Chat PDF API"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # -------------------------------
    # Server Configuration
    # -------------------------------
    host: str = "0.0.0.0"  # Bind to all network interfaces
    port: int = 8000       # Default API port
    
    # -------------------------------
    # Security (JWT Authentication)
    # -------------------------------
    jwt_secret: str                      # Secret key for signing tokens
    jwt_algorithm: str = "HS256"         # Default signing algorithm
    access_token_expire_minutes: int = 30  # Expiry duration for tokens
    
    # -------------------------------
    # Database (Supabase)
    # -------------------------------
    database_url: str
    supabase_url: str
    supabase_service_role_key: str
    
    # -------------------------------
    # LLM Configuration
    # -------------------------------
    llm_provider: str = "grok"  # Options: grok, claude, openai
    
    # Grok (X.AI)
    grok_api_key: str = ""
    grok_model: str = "grok-beta"
    
    # Claude (Anthropic)
    claude_api_key: str = ""
    claude_model: str = "claude-3-sonnet-20240229"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # -------------------------------
    # Embeddings
    # -------------------------------
    embedding_provider: str = "openai"  # Options: openai, cohere
    openai_embedding_model: str = "text-embedding-3-large"
    
    # Cohere
    cohere_api_key: str = ""
    cohere_embedding_model: str = "embed-english-v3.0"
    
    # -------------------------------
    # Document Processing
    # -------------------------------
    max_file_size_mb: int = 50       # Max upload size (MB)
    chunk_size: int = 1000           # Characters per chunk
    chunk_overlap: int = 200         # Overlap between chunks
    similarity_search_k: int = 5     # Top-k results for similarity search
    relevance_threshold: float = 0.7 # Threshold for filtering irrelevant docs
    max_context_length: int = 8000   # Max tokens in context
    max_response_length: int = 500   # Max tokens in response
    
    # -------------------------------
    # Rate Limiting
    # -------------------------------
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # -------------------------------
    # Helper Properties
    # -------------------------------
    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB → bytes for validation purposes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS origins - currently wildcard to allow all origins (not restrictive)."""
        return ["*"]
    
    @property
    def current_llm_config(self) -> dict:
        """
        Get the active LLM configuration depending on the provider.
        
        Returns:
            dict: Provider name, API key, and model to be used.
        """
        if self.llm_provider == "grok":
            return {"provider": "grok", "api_key": self.grok_api_key, "model": self.grok_model}
        elif self.llm_provider == "claude":
            return {"provider": "claude", "api_key": self.claude_api_key, "model": self.claude_model}
        elif self.llm_provider == "openai":
            return {"provider": "openai", "api_key": self.openai_api_key, "model": self.openai_model}
        raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    @property
    def current_embedding_config(self) -> dict:
        """
        Get the active embedding configuration depending on the provider.
        
        Returns:
            dict: Provider name, API key, and embedding model.
        """
        if self.embedding_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_embedding_model,
            }
        elif self.embedding_provider == "cohere":
            return {
                "provider": "cohere",
                "api_key": self.cohere_api_key,
                "model": self.cohere_embedding_model,
            }
        raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
    
    # -------------------------------
    # Pydantic Config
    # -------------------------------
    class Config:
        # Load variables from .env file
        env_file = ".env"
        # Environment variables are case-insensitive
        case_sensitive = False


# Global settings instance (used across the app)
settings = Settings()
