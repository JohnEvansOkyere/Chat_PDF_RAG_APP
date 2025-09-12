"""
Configuration settings for VexaAI RAG Chat PDF Application
Developed by: John Evans Okyere
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the RAG application"""
    
    # Application Info
    APP_NAME = "VexaAI RAG Chat PDF"
    DEVELOPER = "John Evans Okyere"
    VERSION = "1.0.0"
    
    # Model Configuration
    MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-r1:14b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "deepseek-r1:14b")
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", None)
    
    # Text Splitting Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
    
    # Retrieval Configuration
    SIMILARITY_SEARCH_K = int(os.getenv("SIMILARITY_SEARCH_K", 5))
    RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.7))
    
    # File Paths
    BASE_DIR = Path(__file__).parent.parent
    PDF_DIRECTORY = BASE_DIR / "data" / "pdfs"
    LOGS_DIRECTORY = BASE_DIR / "logs"
    CACHE_DIRECTORY = BASE_DIR / "cache"
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
    ALLOWED_EXTENSIONS = ['.pdf']
    
    # Chat Configuration
    MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", 500))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))
    
    # UI Configuration
    PRIMARY_COLOR = "#1f77b4"
    SECONDARY_COLOR = "#ff7f0e"
    BACKGROUND_COLOR = "#f8f9fa"
    
    # Prompt Template
    SYSTEM_PROMPT = """
    You are VexaAI, an intelligent assistant specialized in answering questions about PDF documents.
    You have been developed by John Evans Okyere to provide accurate, concise, and helpful responses.
    
    Instructions:
    1. Use ONLY the provided context to answer questions
    2. If the context doesn't contain sufficient information, clearly state "I don't have enough information in the provided document to answer this question."
    3. Keep responses concise and limit to a maximum of three sentences unless more detail is specifically requested
    4. Do not make up information or use external knowledge
    5. Be professional and helpful in your responses
    6. If asked about topics outside the document, politely redirect to document-related questions
    
    Context: {context}
    
    Human: {question}
    
    VexaAI:"""
    
    # Error Messages
    ERROR_MESSAGES = {
        "no_pdf": "❌ Please upload a PDF document first.",
        "processing_failed": "❌ Failed to process the PDF document. Please try again.",
        "empty_question": "❌ Please enter a question to get started.",
        "model_error": "❌ Error connecting to the language model. Please check your configuration.",
        "file_too_large": f"❌ File size exceeds {MAX_FILE_SIZE_MB}MB limit.",
        "invalid_file": "❌ Please upload a valid PDF file.",
    }
    
    # Success Messages
    SUCCESS_MESSAGES = {
        "pdf_processed": "✅ PDF processed successfully! You can now ask questions about the document.",
        "chat_cleared": "✅ Chat history cleared.",
        "session_reset": "✅ Session reset successfully.",
    }
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check required directories exist
        for directory in [cls.PDF_DIRECTORY, cls.LOGS_DIRECTORY, cls.CACHE_DIRECTORY]:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {directory}: {e}")
        
        # Validate numeric parameters
        if cls.CHUNK_SIZE <= 0:
            errors.append("CHUNK_SIZE must be greater than 0")
        
        if cls.CHUNK_OVERLAP < 0:
            errors.append("CHUNK_OVERLAP must be non-negative")
        
        if cls.SIMILARITY_SEARCH_K <= 0:
            errors.append("SIMILARITY_SEARCH_K must be greater than 0")
        
        if not 0 <= cls.TEMPERATURE <= 1:
            errors.append("TEMPERATURE must be between 0 and 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def get_model_config(cls):
        """Get model configuration dictionary"""
        return {
            "model": cls.MODEL_NAME,
            "base_url": cls.OLLAMA_BASE_URL,
            "temperature": cls.TEMPERATURE,
        }
    
    @classmethod
    def get_embedding_config(cls):
        """Get embedding configuration dictionary"""
        return {
            "model": cls.EMBEDDING_MODEL,
            "base_url": cls.OLLAMA_BASE_URL,
        }
    
    @classmethod
    def get_text_splitter_config(cls):
        """Get text splitter configuration dictionary"""
        return {
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "add_start_index": True,
        }