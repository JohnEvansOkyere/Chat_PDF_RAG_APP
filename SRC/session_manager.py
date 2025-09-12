"""
Session Management Module for VexaAI RAG Chat PDF Application
Handles session state and user data management
Developed by: John Evans Okyere
"""
import streamlit as st
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

class SessionManager:
    """Manages user session state and data"""
    
    def __init__(self):
        """Initialize session manager"""
        self.logger = self._setup_logger()
        self.session_timeout = timedelta(hours=2)  # Session timeout
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for session management"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def initialize_session(self):
        """Initialize session state variables"""
        # Core session variables
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            self.logger.info(f"New session created: {st.session_state.session_id}")
        
        if "session_start_time" not in st.session_state:
            st.session_state.session_start_time = datetime.now()
        
        # Chat-related variables
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "conversation_count" not in st.session_state:
            st.session_state.conversation_count = 0
        
        # PDF processing variables
        if "current_pdf" not in st.session_state:
            st.session_state.current_pdf = None
        
        if "pdf_processed" not in st.session_state:
            st.session_state.pdf_processed = False
        
        if "vector_store_ready" not in st.session_state:
            st.session_state.vector_store_ready = False
        
        if "processing_time" not in st.session_state:
            st.session_state.processing_time = 0
        
        if "pdf_stats" not in st.session_state:
            st.session_state.pdf_stats = {}
        
        # UI state variables
        if "show_suggestions" not in st.session_state:
            st.session_state.show_suggestions = True
        
        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = False
        
        # Performance tracking
        if "response_times" not in st.session_state:
            st.session_state.response_times = []
        
        if "error_count" not in st.session_state:
            st.session_state.error_count = 0
        
        # User preferences
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default user preferences"""
        return {
            "max_response_length": 500,
            "show_processing_time": True,
            "auto_clear_old_chats": False,
            "preferred_chunk_size": 1000,
            "similarity_threshold": 0.7
        }
    
    def is_session_valid(self) -> bool:
        """
        Check if current session is still valid
        
        Returns:
            bool: True if session is valid, False otherwise
        """
        if "session_start_time" not in st.session_state:
            return False
        
        session_age = datetime.now() - st.session_state.session_start_time
        return session_age < self.session_timeout
    
    def refresh_session(self):
        """Refresh session timestamp"""
        st.session_state.session_start_time = datetime.now()
        self.logger.debug("Session refreshed")
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to the conversation history
        
        Args:
            role: Message role (user/assistant)
            content: Message content
            metadata: Additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        if metadata:
            message["metadata"] = metadata
        
        st.session_state.messages.append(message)
        
        if role == "user":
            st.session_state.conversation_count += 1
        
        self.logger.debug(f"Added {role} message to conversation")
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get conversation messages
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List[Dict]: List of messages
        """
        messages = st.session_state.messages
        if limit:
            return messages[-limit:]
        return messages
    
    def clear_messages(self):
        """Clear all conversation messages"""
        st.session_state.messages = []
        st.session_state.conversation_count = 0
        self.logger.info("Cleared conversation messages")
    
    def get_last_user_message(self) -> Optional[Dict]:
        """
        Get the last user message
        
        Returns:
            Dict: Last user message or None
        """
        for message in reversed(st.session_state.messages):
            if message["role"] == "user":
                return message
        return None
    
    def set_pdf_processing_state(self, pdf_name: str, processed: bool, 
                                processing_time: float = 0, stats: Optional[Dict] = None):
        """
        Set PDF processing state
        
        Args:
            pdf_name: Name of the PDF file
            processed: Whether PDF is processed
            processing_time: Time taken to process
            stats: Processing statistics
        """
        st.session_state.current_pdf = pdf_name
        st.session_state.pdf_processed = processed
        st.session_state.processing_time = processing_time
        st.session_state.vector_store_ready = processed
        
        if stats:
            st.session_state.pdf_stats = stats
        
        self.logger.info(f"Updated PDF processing state: {pdf_name} - {processed}")
    
    def reset_pdf_state(self):
        """Reset PDF processing state"""
        st.session_state.current_pdf = None
        st.session_state.pdf_processed = False
        st.session_state.vector_store_ready = False
        st.session_state.processing_time = 0
        st.session_state.pdf_stats = {}
        self.clear_messages()
        
        self.logger.info("Reset PDF processing state")
    
    def update_user_preference(self, key: str, value: Any):
        """
        Update user preference
        
        Args:
            key: Preference key
            value: Preference value
        """
        st.session_state.user_preferences[key] = value
        self.logger.debug(f"Updated user preference: {key} = {value}")
    
    def get_user_preference(self, key: str, default: Any = None):
        """
        Get user preference
        
        Args:
            key: Preference key
            default: Default value if key not found
            
        Returns:
            User preference value
        """
        return st.session_state.user_preferences.get(key, default)
    
    def record_response_time(self, response_time: float):
        """
        Record response time for performance tracking
        
        Args:
            response_time: Time taken for response
        """
        st.session_state.response_times.append({
            "time": response_time,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 response times
        if len(st.session_state.response_times) > 100:
            st.session_state.response_times = st.session_state.response_times[-100:]
    
    def record_error(self, error_type: str, error_message: str):
        """
        Record error for tracking
        
        Args:
            error_type: Type of error
            error_message: Error message
        """
        st.session_state.error_count += 1
        
        if "errors" not in st.session_state:
            st.session_state.errors = []
        
        st.session_state.errors.append({
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 50 errors
        if len(st.session_state.errors) > 50:
            st.session_state.errors = st.session_state.errors[-50:]
        
        self.logger.error(f"Recorded error: {error_type} - {error_message}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics
        
        Returns:
            Dict: Session statistics
        """
        session_duration = datetime.now() - st.session_state.session_start_time
        
        stats = {
            "session_id": st.session_state.session_id,
            "session_duration_minutes": session_duration.total_seconds() / 60,
            "total_messages": len(st.session_state.messages),
            "user_messages": len([m for m in st.session_state.messages if m["role"] == "user"]),
            "assistant_messages": len([m for m in st.session_state.messages if m["role"] == "assistant"]),
            "conversation_count": st.session_state.conversation_count,
            "current_pdf": st.session_state.current_pdf,
            "pdf_processed": st.session_state.pdf_processed,
            "processing_time": st.session_state.processing_time,
            "error_count": st.session_state.error_count
        }
        
        # Add performance statistics
        if st.session_state.response_times:
            response_times = [rt["time"] for rt in st.session_state.response_times]
            stats.update({
                "average_response_time": sum(response_times) / len(response_times),
                "fastest_response": min(response_times),
                "slowest_response": max(response_times),
                "total_responses": len(response_times)
            })
        
        return stats
    
    def export_session_data(self) -> str:
        """
        Export session data as JSON string
        
        Returns:
            str: JSON string of session data
        """
        session_data = {
            "session_info": self.get_session_stats(),
            "messages": st.session_state.messages,
            "user_preferences": st.session_state.user_preferences,
            "pdf_stats": st.session_state.pdf_stats,
            "export_timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(session_data, indent=2)
    
    def reset_session(self):
        """Reset entire session"""
        # Store session ID for logging
        old_session_id = st.session_state.get("session_id", "unknown")
        
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Re-initialize session
        self.initialize_session()
        
        self.logger.info(f"Reset session: {old_session_id} -> {st.session_state.session_id}")
    
    def cleanup_old_data(self):
        """Clean up old session data to prevent memory issues"""
        # Limit message history
        max_messages = 200
        if len(st.session_state.messages) > max_messages:
            st.session_state.messages = st.session_state.messages[-max_messages:]
            self.logger.info(f"Cleaned up old messages, kept last {max_messages}")
        
        # Limit response times
        max_response_times = 100
        if len(st.session_state.response_times) > max_response_times:
            st.session_state.response_times = st.session_state.response_times[-max_response_times:]
        
        # Limit errors
        if "errors" in st.session_state and len(st.session_state.errors) > 50:
            st.session_state.errors = st.session_state.errors[-50:]