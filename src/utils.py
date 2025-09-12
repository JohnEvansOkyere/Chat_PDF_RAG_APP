"""
Utility Functions for VexaAI RAG Chat PDF Application
Common helper functions and utilities
Developed by: John Evans Okyere
"""
import os
import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import streamlit as st

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        "data/pdfs",
        "logs", 
        "cache",
        "exports",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup application logging
    
    Args:
        log_level: Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/vexaai_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("VexaAI")
    logger.info("Logging initialized")
    return logger

def log_interaction(session_id: str, pdf_name: str, question: str, 
                   response: str, processing_time: float = 0):
    """
    Log user interaction for analytics
    
    Args:
        session_id: Session identifier
        pdf_name: Name of the PDF
        question: User question
        response: Assistant response
        processing_time: Time taken to process
    """
    try:
        interaction_log = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "pdf_name": pdf_name,
            "question": question[:200],  # Truncate for privacy
            "response": response[:200],  # Truncate for privacy
            "processing_time": processing_time,
            "question_length": len(question),
            "response_length": len(response)
        }
        
        # Log to file
        log_file = Path("logs") / f"interactions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(interaction_log) + "\n")
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Error logging interaction: {str(e)}")

def calculate_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MD5 hash of the file
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.getLogger(__name__).error(f"Error calculating file hash: {str(e)}")
        return ""

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove special characters that might cause issues
    text = text.replace("\x00", "")  # Remove null characters
    
    return text.strip()

def validate_pdf_content(content: str) -> bool:
    """
    Validate PDF content for processing
    
    Args:
        content: PDF content to validate
        
    Returns:
        bool: True if content is valid
    """
    if not content or not content.strip():
        return False
    
    # Check minimum content length
    if len(content.strip()) < 10:
        return False
    
    # Check for common extraction issues
    if content.count("�") > len(content) * 0.1:  # Too many replacement characters
        return False
    
    return True

def get_system_info() -> Dict[str, Any]:
    """
    Get system information for diagnostics
    
    Returns:
        Dict: System information
    """
    import platform
    import sys
    
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "architecture": platform.architecture(),
        "timestamp": datetime.now().isoformat()
    }

def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        str: Safe filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    
    # Remove multiple underscores
    while "__" in filename:
        filename = filename.replace("__", "_")
    
    return filename.strip("_")

def create_backup(data: Dict, backup_name: str = None) -> str:
    """
    Create a backup of data
    
    Args:
        data: Data to backup
        backup_name: Name for the backup
        
    Returns:
        str: Path to backup file
    """
    if backup_name is None:
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    backup_path = backup_dir / f"{backup_name}.json"
    
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logging.getLogger(__name__).info(f"Backup created: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating backup: {str(e)}")
        return ""

def load_backup(backup_path: str) -> Optional[Dict]:
    """
    Load data from backup
    
    Args:
        backup_path: Path to backup file
        
    Returns:
        Dict: Loaded data or None if error
    """
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        logging.getLogger(__name__).info(f"Backup loaded: {backup_path}")
        return data
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading backup: {str(e)}")
        return None

def measure_performance(func):
    """
    Decorator to measure function performance
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger = logging.getLogger(__name__)
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        
        return result
    
    return wrapper

def get_available_models() -> List[str]:
    """
    Get list of available Ollama models
    
    Returns:
        List[str]: List of available models
    """
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = [line.split()[0] for line in lines if line.strip()]
            return models
        else:
            return ['deepseek-r1:14b']  # Default fallback
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting available models: {str(e)}")
        return ['deepseek-r1:14b']  # Default fallback

def check_ollama_status() -> bool:
    """
    Check if Ollama service is running
    
    Returns:
        bool: True if Ollama is running
    """
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def export_chat_history(messages: List[Dict], filename: str = None) -> str:
    """
    Export chat history to file
    
    Args:
        messages: List of chat messages
        filename: Output filename
        
    Returns:
        str: Path to exported file
    """
    if filename is None:
        filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    export_path = export_dir / filename
    
    try:
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_messages": len(messages),
            "messages": messages
        }
        
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(export_path)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error exporting chat history: {str(e)}")
        return ""

def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics
    
    Returns:
        Dict: Memory usage statistics
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent()
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}