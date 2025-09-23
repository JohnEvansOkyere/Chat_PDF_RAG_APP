# backend/app/services/chat_service.py
"""
Complete chat service with RAG pipeline implementation
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

from app.config import settings
from app.database import get_supabase_client
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.config = settings
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
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

    async def process_message(self, session_id: str, user_id: str, message: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Process message and generate response using RAG pipeline"""
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
            
            # Get conversation history for context
            conversation_history = await self._get_conversation_history(session_id, limit=10)
            
            # Search for relevant chunks using RAG
            relevant_chunks = []
            context = ""
            sources = []
            
            try:
                # Use vector search to find relevant document chunks
                search_results = await self.vector_service.search_similar_chunks(
                    user_id=user_id,
                    query=message,
                    document_id=document_id,
                    limit=5,
                    similarity_threshold=0.3  # Lower threshold for more results
                )
                
                if search_results:
                    self.logger.info(f"Found {len(search_results)} relevant chunks")
                    
                    # Build context from retrieved chunks
                    context_parts = []
                    for i, chunk in enumerate(search_results):
                        context_parts.append(f"[Chunk {i+1}]:\n{chunk['content']}")
                        sources.append({
                            'document_id': chunk['document_id'],
                            'chunk_id': chunk.get('id', ''),
                            'similarity': chunk.get('similarity', 0),
                            'page_number': chunk.get('page_number'),
                        })
                    
                    context = "\n\n".join(context_parts)
                else:
                    self.logger.warning("No relevant chunks found for query")
                    context = "No relevant document content found."
                    
            except Exception as e:
                self.logger.error(f"Vector search failed: {e}")
                context = "Error retrieving document content."
            
            # Generate response using LLM
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
                self.logger.error(f"LLM generation failed: {e}")
                ai_response = "I apologize, but I encountered an error while processing your question. Please try again."
                metadata = {'error': str(e)}
            
            # Save AI response
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
            
            # Update session timestamp
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
            
            # For now, return regular response as streaming isn't implemented in LLM service
            # You can implement proper streaming later if needed
            response = await self.process_message(session_id, user_id, message, document_id)
            
            # Simulate streaming by yielding words
            words = response['content'].split()
            for word in words:
                yield f'"{word} "'
                
        except Exception as e:
            self.logger.error(f"Failed to process streaming message: {e}")
            yield f'"Error: {str(e)}"'
    
    async def _get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        try:
            response = self.supabase.table('chat_messages').select('role, content').eq('session_id', session_id).order('created_at', desc=True).limit(limit * 2).execute()
            
            if not response.data:
                return []
            
            # Reverse to get chronological order and format for LLM
            messages = []
            for msg in reversed(response.data):
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            return messages[-limit:]  # Return last 'limit' messages
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {e}")
            return []