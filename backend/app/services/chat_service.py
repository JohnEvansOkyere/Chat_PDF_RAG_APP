# backend/app/services/chat_service.py
"""
Complete chat service with RAG pipeline implementation.
Handles creation, retrieval, and deletion of chat sessions, 
and manages message processing with context-aware responses.
"""

import logging
import uuid
import re
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

from app.config import settings
from app.database import get_supabase_client
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        """Initialize ChatService with config, database client, vector service, and LLM service"""
        self.config = settings
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        self.logger = logger

    def _serialize_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize session payloads for API responses."""
        return {
            'id': session['id'],
            'title': session.get('title', 'New Chat'),
            'document_id': session.get('document_id'),
            'message_count': session.get('message_count', 0),
            'created_at': session['created_at'],
            'updated_at': session['updated_at'],
            **({'status': session['status']} if 'status' in session else {}),
            **({'user_id': session['user_id']} if 'user_id' in session else {}),
        }
    
    async def create_session(self, user_id: str, title: str = "New Chat", document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new chat session for the user.

        Args:
            user_id (str): ID of the user starting the session.
            title (str): Session title, defaults to "New Chat".
            document_id (Optional[str]): Optional ID of document associated with this chat.

        Returns:
            Dict[str, Any]: Created session record from Supabase.
        """
        try:
            # Prepare session payload
            session_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'title': title,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            if document_id:
                session_data['document_id'] = document_id

            # Insert into Supabase. If the DB schema does not yet include
            # `document_id`, retry without it so chat can still function.
            try:
                response = self.supabase.table('chat_sessions').insert(session_data).execute()
            except Exception as e:
                if document_id and "document_id" in str(e):
                    self.logger.warning("chat_sessions.document_id is missing in Supabase; retrying without it")
                    fallback_data = {k: v for k, v in session_data.items() if k != 'document_id'}
                    response = self.supabase.table('chat_sessions').insert(fallback_data).execute()
                else:
                    raise
            
            if response.data:
                session = self._serialize_session(response.data[0])
                if document_id and 'document_id' not in response.data[0]:
                    session['document_id'] = document_id
                return session
            else:
                raise Exception("Failed to create session")
                
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chat sessions for a specific user.

        Args:
            user_id (str): User identifier.

        Returns:
            List[Dict[str, Any]]: List of sessions sorted by last update.
        """
        try:
            response = self.supabase.table('chat_sessions').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
            return [self._serialize_session(session) for session in (response.data or [])]
        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {e}")
            return []

    async def get_session_with_messages(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get a single session and all messages within it.

        Args:
            session_id (str): Chat session ID.
            user_id (str): User ID (for ownership check).

        Returns:
            Dict[str, Any]: Session data including messages.
        """
        try:
            # Fetch session info
            session_response = self.supabase.table('chat_sessions').select('*').eq('id', session_id).eq('user_id', user_id).single().execute()
            
            if not session_response.data:
                raise Exception("Session not found")
            
            # Fetch all messages in this session
            messages_response = self.supabase.table('chat_messages').select('*').eq('session_id', session_id).order('created_at').execute()
            
            session = self._serialize_session(session_response.data)
            session['messages'] = messages_response.data or []
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to get session with messages: {e}")
            raise

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        Delete a session and its messages.

        Args:
            session_id (str): ID of the chat session.
            user_id (str): ID of the user.

        Returns:
            bool: True if deletion succeeded.
        """
        try:
            # Delete messages first (maintain DB consistency)
            self.supabase.table('chat_messages').delete().eq('session_id', session_id).execute()
            
            # Delete the session record
            self.supabase.table('chat_sessions').delete().eq('id', session_id).eq('user_id', user_id).execute()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            raise

    async def process_message(self, session_id: str, user_id: str, message: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message through the RAG pipeline and return AI response.

        Steps:
            1. Save user message.
            2. Retrieve recent conversation history for context.
            3. Search for relevant document chunks (via vector DB).
            4. Generate AI response using LLM + context.
            5. Save assistant message.
            6. Update session timestamp.

        Args:
            session_id (str): ID of the session.
            user_id (str): ID of the user.
            message (str): User’s input message.
            document_id (Optional[str]): Optional linked document ID.

        Returns:
            Dict[str, Any]: AI response, metadata, and references.
        """
        try:
            # Step 1: Save user message to DB
            user_message_data = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'user_id': user_id,
                'role': 'user',
                'content': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('chat_messages').insert(user_message_data).execute()
            
            # Step 2: Get conversation history for context
            conversation_history = await self._get_conversation_history(session_id, limit=10)
            
            # Step 3: Initialize RAG variables
            relevant_chunks = []
            context = ""
            sources = []
            
            try:
                # Perform vector search for related document snippets
                search_results = await self.vector_service.search_similar_chunks(
                    user_id=user_id,
                    query=message,
                    document_id=document_id,
                    limit=5,
                    similarity_threshold=0.3  # Lower threshold to capture more possible results
                )
                
                if search_results:
                    self.logger.info(f"Found {len(search_results)} relevant chunks")
                    
                    # Build context string by cleaning retrieved chunks
                    context_parts = []
                    for chunk in search_results:
                        content = chunk['content']
                        
                        # Remove extra metadata/formatting
                        content = re.sub(r'Chunk \d+:', '', content)
                        content = re.sub(r'section; consistent in Chunk \d+', '', content)
                        content = re.sub(r'\(Cited from [^)]*\)', '', content)
                        content = content.replace('**', '').replace('#', '').strip()
                        
                        context_parts.append(content)

                    context = "\n\n".join(context_parts)
                else:
                    self.logger.warning("No relevant chunks found for query")
                    context = "No relevant document content found."
                    
            except Exception as e:
                # Vector search error should not block chat response
                self.logger.error(f"Vector search failed: {e}")
                context = "Error retrieving document content."
            
            # Step 4: Generate LLM response
            try:
                llm_response = await self.llm_service.generate_response(
                    user_message=message,
                    context=context,
                    conversation_history=conversation_history
                )
                
                ai_response = llm_response['response']
                metadata = {
                    'tokens_used': llm_response.get('tokens_used', 0),
                    'model': llm_response.get('model', ''),
                    'provider': llm_response.get('provider', ''),
                    'chunks_found': len(relevant_chunks)
                }
                
            except Exception as e:
                # Gracefully handle LLM errors
                self.logger.error(f"LLM generation failed: {e}")
                ai_response = "I apologize, but I encountered an error while processing your question. Please try again."
                metadata = {'error': str(e)}
            
            # Step 5: Save assistant (AI) message
            ai_message_data = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'user_id': user_id,
                'role': 'assistant',
                'content': ai_response,
                'metadata': metadata,
                'created_at': datetime.utcnow().isoformat()
            }
            
            ai_message_response = self.supabase.table('chat_messages').insert(ai_message_data).execute()
            
            # Step 6: Update session last updated timestamp
            self.supabase.table('chat_sessions').update({
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', session_id).execute()
            
            return {
                'message_id': ai_message_response.data[0]['id'],
                'content': ai_response,
                'sources': sources,
                'metadata': metadata,
                'created_at': ai_message_response.data[0]['created_at']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            raise

    async def _get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetch recent conversation history for a session.

        Args:
            session_id (str): ID of the chat session.
            limit (int): Number of past exchanges to return.

        Returns:
            List[Dict[str, str]]: Recent messages in format {role, content}.
        """
        try:
            response = self.supabase.table('chat_messages').select('role, content').eq('session_id', session_id).order('created_at', desc=True).limit(limit * 2).execute()
            
            if not response.data:
                return []
            
            # Reverse to chronological order and keep only the last `limit` messages
            messages = []
            for msg in reversed(response.data):
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            return messages[-limit:]  
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {e}")
            return []
