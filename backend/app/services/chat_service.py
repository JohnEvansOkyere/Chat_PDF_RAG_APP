# backend/app/services/chat_service.py
"""
Complete chat service with all required methods
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.config = settings
        self.supabase = get_supabase_client()
        self.logger = logger
    
    async def create_session(self, user_id: str, title: str = "New Chat", document_id: Optional[str] = None) -> Dict[str, Any]:
        """Create new chat session"""
        try:
            session_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'title': title,
                'document_id': document_id,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('chat_sessions').insert(session_data).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Failed to create session")
                
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        try:
            response = self.supabase.table('chat_sessions').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
            return response.data or []
        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {e}")
            return []

    async def get_session_with_messages(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get session with messages"""
        try:
            # Get session
            session_response = self.supabase.table('chat_sessions').select('*').eq('id', session_id).eq('user_id', user_id).single().execute()
            
            if not session_response.data:
                raise Exception("Session not found")
            
            # Get messages for this session
            messages_response = self.supabase.table('chat_messages').select('*').eq('session_id', session_id).order('created_at').execute()
            
            session = session_response.data
            session['messages'] = messages_response.data or []
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to get session with messages: {e}")
            raise

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete chat session"""
        try:
            # Delete messages first
            self.supabase.table('chat_messages').delete().eq('session_id', session_id).execute()
            
            # Delete session
            self.supabase.table('chat_sessions').delete().eq('id', session_id).eq('user_id', user_id).execute()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            raise

        # backend/app/services/chat_service.py
    async def process_message(self, session_id: str, user_id: str, message: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Process message and generate response"""
        try:
            # Save user message
            user_message_data = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'user_id': user_id,
                'role': 'user',
                'content': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('chat_messages').insert(user_message_data).execute()
            
            # Generate AI response
            ai_response = f"Thank you for your message: '{message}'. This is a placeholder response from the chat service."
            
            # Save AI response
            ai_message_data = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'user_id': user_id,
                'role': 'assistant',
                'content': ai_response,
                'created_at': datetime.utcnow().isoformat()
            }
            
            ai_message_response = self.supabase.table('chat_messages').insert(ai_message_data).execute()
            
            # Update session - remove the problematic SQL increment
            self.supabase.table('chat_sessions').update({
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', session_id).execute()
            
            return {
                'message_id': ai_message_response.data[0]['id'],
                'content': ai_response,
                'sources': [],
                'metadata': {},
                'created_at': ai_message_response.data[0]['created_at']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            raise

    async def process_message_stream(self, session_id: str, user_id: str, message: str, document_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Process message with streaming response"""
        try:
            # Save user message first
            user_message_data = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'user_id': user_id,
                'role': 'user',
                'content': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('chat_messages').insert(user_message_data).execute()
            
            # Simulate streaming response
            response_text = f"Streaming response to: '{message}'. This is a placeholder streaming implementation."
            
            for word in response_text.split():
                yield f'"{word} "'
                
        except Exception as e:
            self.logger.error(f"Failed to process streaming message: {e}")
            yield f'"Error: {str(e)}"'