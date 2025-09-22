# backend/app/services/document_service.py
"""
Document processing service
"""

import os
import uuid
import tempfile
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import UploadFile, HTTPException
from supabase import create_client

from app.config import settings
from app.database import get_supabase_client
from app.services.vector_service import VectorService
from app.utils.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
        self.pdf_processor = PDFProcessor()
    
    async def create_document(self, user_id: str, file: UploadFile) -> Dict[str, Any]:
        """Create document record and upload to storage"""
        try:
            # Generate unique filename
            document_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            storage_filename = f"{document_id}{file_extension}"
            storage_path = f"{user_id}/{storage_filename}"
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Upload to Supabase storage
            storage_response = self.supabase.storage.from_('documents').upload(
                storage_path,
                file_content,
                file_options={
                    'content-type': file.content_type or 'application/pdf'
                }
            )
            
            if storage_response.get('error'):
                raise Exception(f"Storage upload failed: {storage_response['error']}")
            
            # Create document record
            document_data = {
                'id': document_id,
                'user_id': user_id,
                'filename': storage_filename,
                'original_filename': file.filename,
                'file_path': storage_path,
                'file_size': file_size,
                'mime_type': file.content_type or 'application/pdf',
                'status': 'processing'
            }
            
            response = self.supabase.table('documents').insert(document_data).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Failed to create document record")
                
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    async def process_document(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Process uploaded document: extract text, chunk, and create embeddings"""
        start_time = datetime.utcnow()
        
        try:
            # Get document record
            doc_response = self.supabase.table('documents').select('*').eq('id', document_id).single().execute()
            
            if not doc_response.data:
                raise Exception("Document not found")
            
            document = doc_response.data
            
            # Download file from storage
            file_response = self.supabase.storage.from_('documents').download(document['file_path'])
            
            if not file_response:
                raise Exception("Failed to download file from storage")
            
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(file_response)
                tmp_file_path = tmp_file.name
            
            try:
                # Process PDF
                processing_result = await self.pdf_processor.process_pdf(tmp_file_path)
                
                # Create embeddings and store chunks
                await self.vector_service.create_document_embeddings(
                    document_id=document_id,
                    chunks=processing_result['chunks']
                )
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update document with processing results
                update_data = {
                    'status': 'completed',
                    'processing_time': processing_time,
                    'page_count': processing_result['stats']['total_pages'],
                    'total_chunks': processing_result['stats']['total_chunks'],
                    'total_characters': processing_result['stats']['total_characters'],
                    'total_words': processing_result['stats']['total_words'],
                    'preview_text': processing_result['preview'],
                    'processed_at': datetime.utcnow().isoformat()
                }
                
                update_response = self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
                
                if update_response.data:
                    return update_response.data[0]
                else:
                    raise Exception("Failed to update document status")
                    
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            
            # Update document status to failed
            error_update = {
                'status': 'failed',
                'error_message': str(e),
                'processing_time': (datetime.utcnow() - start_time).total_seconds()
            }
            
            self.supabase.table('documents').update(error_update).eq('id', document_id).execute()
            raise
    
    async def get_document(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Get document by ID"""
        response = self.supabase.table('documents').select('*').eq('id', document_id).eq('user_id', user_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return response.data
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        response = self.supabase.table('documents').select('*').eq('user_id', user_id).neq('status', 'deleted').order('created_at', desc=True).execute()
        
        return response.data or []
    
    async def delete_document(self, document_id: str, user_id: str):
        """Delete document and associated data"""
        # Verify ownership
        document = await self.get_document(document_id, user_id)
        
        # Delete from storage
        storage_response = self.supabase.storage.from_('documents').remove([document['file_path']])
        
        # Delete chunks
        self.supabase.table('document_chunks').delete().eq('document_id', document_id).execute()
        
        # Mark document as deleted
        self.supabase.table('documents').update({'status': 'deleted'}).eq('id', document_id).execute()

# backend/app/services/vector_service.py
"""
Vector embedding and similarity search service
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import openai
import cohere
from anthropic import Anthropic

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.llm_config = settings.current_llm_config
        
        # Initialize embedding client based on provider
        if self.llm_config['provider'] == 'openai':
            self.openai_client = openai.AsyncOpenAI(api_key=self.llm_config['api_key'])
        elif self.llm_config['provider'] == 'cohere':
            self.cohere_client = cohere.AsyncClient(api_key=self.llm_config['api_key'])
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if self.llm_config['provider'] == 'openai':
                response = await self.openai_client.embeddings.create(
                    model=self.llm_config['embedding_model'],
                    input=text
                )
                return response.data[0].embedding
            
            elif self.llm_config['provider'] == 'cohere':
                response = await self.cohere_client.embed(
                    texts=[text],
                    model=self.llm_config['embedding_model']
                )
                return response.embeddings[0]
            
            else:
                raise Exception(f"Embedding not supported for provider: {self.llm_config['provider']}")
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def create_document_embeddings(self, document_id: str, chunks: List[Dict[str, Any]]):
        """Create embeddings for document chunks and store in database"""
        try:
            chunk_records = []
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.generate_embedding(chunk['content'])
                
                # Prepare chunk record
                chunk_record = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'content': chunk['content'],
                    'embedding': embedding,
                    'metadata': chunk.get('metadata', {}),
                    'page_number': chunk.get('page_number'),
                    'chunk_size': len(chunk['content']),
                    'start_index': chunk.get('start_index')
                }
                
                chunk_records.append(chunk_record)
            
            # Batch insert chunks
            response = self.supabase.table('document_chunks').insert(chunk_records).execute()
            
            if not response.data:
                raise Exception("Failed to insert document chunks")
            
            logger.info(f"Created {len(chunk_records)} embeddings for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error creating document embeddings: {e}")
            raise
    
    async def search_similar_chunks(
        self,
        user_id: str,
        query: str,
        document_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Get user's document IDs if not specified
            document_ids = None
            if document_id:
                document_ids = [document_id]
            else:
                docs_response = self.supabase.table('documents').select('id').eq('user_id', user_id).eq('status', 'completed').execute()
                if docs_response.data:
                    document_ids = [doc['id'] for doc in docs_response.data]
                else:
                    return []  # No documents found
            
            # Perform vector search
            search_response = self.supabase.rpc('search_document_chunks', {
                'query_embedding': query_embedding,
                'document_ids': document_ids,
                'similarity_threshold': similarity_threshold,
                'match_count': limit
            }).execute()
            
            return search_response.data or []
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            raise
    
    async def test_embeddings(self) -> bool:
        """Test embedding generation"""
        try:
            test_text = "This is a test document for embedding generation."
            embedding = await self.generate_embedding(test_text)
            
            if embedding and len(embedding) > 0:
                logger.info("Embedding test successful")
                return True
            else:
                logger.error("Embedding test failed: empty embedding")
                return False
                
        except Exception as e:
            logger.error(f"Embedding test failed: {e}")
            return False

# backend/app/services/llm_service.py
"""
Language model service for chat responses
"""

import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, Optional
import openai
import cohere
from anthropic import Anthropic

from app.config import settings
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm_config = settings.current_llm_config
        self.vector_service = VectorService()
        
        # Initialize LLM client based on provider
        if self.llm_config['provider'] == 'openai':
            self.openai_client = openai.AsyncOpenAI(api_key=self.llm_config['api_key'])
        elif self.llm_config['provider'] == 'anthropic':
            self.anthropic_client = Anthropic(api_key=self.llm_config['api_key'])
        elif self.llm_config['provider'] == 'cohere':
            self.cohere_client = cohere.AsyncClient(api_key=self.llm_config['api_key'])
    
    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate response to user message"""
        try:
            # Prepare system prompt
            system_prompt = f"""
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
"""
            
            if self.llm_config['provider'] == 'openai':
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add conversation history
                if conversation_history:
                    messages.extend(conversation_history[-10:])  # Last 10 messages
                
                messages.append({"role": "user", "content": user_message})
                
                response = await self.openai_client.chat.completions.create(
                    model=self.llm_config['model'],
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500
                )
                
                return {
                    'response': response.choices[0].message.content,
                    'tokens_used': response.usage.total_tokens,
                    'model': self.llm_config['model']
                }
            
            elif self.llm_config['provider'] == 'anthropic':
                # Anthropic doesn't use system messages in the same way
                full_prompt = f"{system_prompt}\n\nHuman: {user_message}\n\nAssistant:"
                
                response = await self.anthropic_client.messages.create(
                    model=self.llm_config['model'],
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                
                return {
                    'response': response.content[0].text,
                    'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                    'model': self.llm_config['model']
                }
            
            elif self.llm_config['provider'] == 'cohere':
                full_prompt = f"{system_prompt}\n\nUser: {user_message}\nAssistant:"
                
                response = await self.cohere_client.generate(
                    model=self.llm_config['model'],
                    prompt=full_prompt,
                    temperature=0.1,
                    max_tokens=500
                )
                
                return {
                    'response': response.generations[0].text.strip(),
                    'tokens_used': response.meta.billed_units.output_tokens if response.meta else 0,
                    'model': self.llm_config['model']
                }
            
            else:
                raise Exception(f"Unsupported LLM provider: {self.llm_config['provider']}")
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_response_stream(
        self,
        user_message: str,
        context: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response to user message"""
        try:
            system_prompt = f"""
You are VexaAI, an intelligent assistant specialized in answering questions about PDF documents.
You have been developed by John Evans Okyere to provide accurate, concise, and helpful responses.

Instructions:
1. Use ONLY the provided context to answer questions
2. If the context doesn't contain sufficient information, clearly state "I don't have enough information in the provided document to answer this question."
3. Keep responses concise and limit to a maximum of three sentences unless more detail is specifically requested
4. Do not make up information or use external knowledge
5. Be professional and helpful in your responses

Context: {context}
"""
            
            if self.llm_config['provider'] == 'openai':
                messages = [{"role": "system", "content": system_prompt}]
                
                if conversation_history:
                    messages.extend(conversation_history[-10:])
                
                messages.append({"role": "user", "content": user_message})
                
                stream = await self.openai_client.chat.completions.create(
                    model=self.llm_config['model'],
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            else:
                # Fallback to non-streaming for other providers
                response = await self.generate_response(user_message, context, conversation_history)
                yield response['response']
                
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Error: {str(e)}"
    
    async def test_connection(self) -> str:
        """Test LLM connection"""
        try:
            response = await self.generate_response("Hello, please respond with 'Connection successful'")
            return response['response']
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            raise

# backend/app/services/chat_service.py
"""
Chat session management service
"""

import uuid
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import json

from app.database import get_supabase_client
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
    
    async def create_session(
        self,
        user_id: str,
        title: str = "New Chat",
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new chat session"""
        try:
            session_data = {
                'user_id': user_id,
                'title': title,
                'status': 'active'
            }
            
            response = self.supabase.table('chat_sessions').insert(session_data).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Failed to create chat session")
                
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        response = self.supabase.table('chat_sessions').select('*').eq('user_id', user_id).eq('status', 'active').order('updated_at', desc=True).execute()
        
        return response.data or []
    
    async def get_session_with_messages(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get session with messages"""
        # Verify session ownership
        session_response = self.supabase.table('chat_sessions').select('*').eq('id', session_id).eq('user_id', user_id).single().execute()
        
        if not session_response.data:
            raise Exception("Session not found")
        
        # Get session with messages using database function
        messages_response = self.supabase.rpc('get_chat_session_with_messages', {
            'session_id': session_id,
            'message_limit': 50
        }).execute()
        
        if messages_response.data:
            return messages_response.data[0]
        else:
            return {
                'session': session_response.data,
                'messages': []
            }
    
    async def process_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user message and generate response"""
        start_time = datetime.utcnow()
        
        try:
            # Add user message
            user_message_data = {
                'session_id': session_id,
                'user_id': user_id,
                'role': 'user',
                'content': message
            }
            
            self.supabase.table('chat_messages').insert(user_message_data).execute()
            
            # Get relevant context
            context_chunks = []
            if document_id:
                similar_chunks = await self.vector_service.search_similar_chunks(
                    user_id=user_id,
                    query=message,
                    document_id=document_id,
                    limit=5
                )
                context_chunks = [chunk['id'] for chunk in similar_chunks]
                context = '\n\n'.join([chunk['content'] for chunk in similar_chunks])
            else:
                context = ""
            
            # Get conversation history
            history_response = self.supabase.table('chat_messages').select('role,content').eq('session_id', session_id).order('created_at', desc=True).limit(10).execute()
            
            conversation_history = []
            if history_response.data:
                for msg in reversed(history_response.data[:-1]):  # Exclude the just-added user message
                    conversation_history.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Generate response
            llm_response = await self.llm_service.generate_response(
                user_message=message,
                context=context,
                conversation_history=conversation_history
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Add assistant response
            assistant_message_data = {
                'session_id': session_id,
                'user_id': user_id,
                'role': 'assistant',
                'content': llm_response['response'],
                'metadata': {
                    'model': llm_response['model'],
                    'context_length': len(context)
                },
                'tokens_used': llm_response.get('tokens_used'),
                'processing_time': processing_time,
                'context_chunks': context_chunks
            }
            
            assistant_response = self.supabase.table('chat_messages').insert(assistant_message_data).execute()
            
            if assistant_response.data:
                return {
                    'id': assistant_response.data[0]['id'],
                    'message': llm_response['response'],
                    'context_chunks': context_chunks,
                    'tokens_used': llm_response.get('tokens_used'),
                    'processing_time': processing_time,
                    'timestamp': assistant_response.data[0]['created_at']
                }
            else:
                raise Exception("Failed to save assistant response")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def process_message_stream(
        self,
        session_id: str,
        user_id: str,
        message: str,
        document_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Process message with streaming response"""
        try:
            # Add user message (same as non-streaming)
            user_message_data = {
                'session_id': session_id,
                'user_id': user_id,
                'role': 'user',
                'content': message
            }
            
            self.supabase.table('chat_messages').insert(user_message_data).execute()
            
            # Get context and history (same as non-streaming)
            context_chunks = []
            if document_id:
                similar_chunks = await self.vector_service.search_similar_chunks(
                    user_id=user_id,
                    query=message,
                    document_id=document_id,
                    limit=5
                )
                context_chunks = [chunk['id'] for chunk in similar_chunks]
                context = '\n\n'.join([chunk['content'] for chunk in similar_chunks])
            else:
                context = ""
            
            # Get conversation history
            history_response = self.supabase.table('chat_messages').select('role,content').eq('session_id', session_id).order('created_at', desc=True).limit(10).execute()
            
            conversation_history = []
            if history_response.data:
                for msg in reversed(history_response.data[:-1]):
                    conversation_history.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Stream response
            full_response = ""
            async for chunk in self.llm_service.generate_response_stream(
                user_message=message,
                context=context,
                conversation_history=conversation_history
            ):
                full_response += chunk
                yield json.dumps({'chunk': chunk, 'done': False})
            
            # Save complete response
            assistant_message_data = {
                'session_id': session_id,
                'user_id': user_id,
                'role': 'assistant',
                'content': full_response,
                'context_chunks': context_chunks
            }
            
            self.supabase.table('chat_messages').insert(assistant_message_data).execute()
            
            yield json.dumps({'chunk': '', 'done': True, 'context_chunks': context_chunks})
            
        except Exception as e:
            logger.error(f"Error in streaming message: {e}")
            yield json.dumps({'chunk': f'Error: {str(e)}', 'done': True, 'error': True})
    
    async def delete_session(self, session_id: str, user_id: str):
        """Delete chat session"""
        # Verify ownership
        session_response = self.supabase.table('chat_sessions').select('*').eq('id', session_id).eq('user_id', user_id).single().execute()
        
        if not session_response.data:
            raise Exception("Session not found")
        
        # Soft delete
        self.supabase.table('chat_sessions').update({'status': 'deleted'}).eq('id', session_id).execute()