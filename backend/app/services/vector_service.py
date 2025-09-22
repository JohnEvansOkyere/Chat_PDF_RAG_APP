# backend/app/services/vector_service.py  
"""
Vector service with embedding support for different providers
"""

import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.config = settings
        self.supabase = get_supabase_client()
        self.logger = logger
        self._initialize_embedding_client()
    
    def _initialize_embedding_client(self):
        """Initialize embedding client"""
        self.client = httpx.AsyncClient(timeout=60.0)
        
        if self.config.embedding_provider == "openai":
            self.embedding_url = "https://api.openai.com/v1/embeddings"
            self.headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json"
            }
            self.embedding_model = self.config.openai_embedding_model
            
        elif self.config.embedding_provider == "cohere":
            self.embedding_url = "https://api.cohere.ai/v1/embed"
            self.headers = {
                "Authorization": f"Bearer {self.config.cohere_api_key}",
                "Content-Type": "application/json"
            }
            self.embedding_model = self.config.cohere_embedding_model
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if self.config.embedding_provider == "openai":
                payload = {
                    "model": self.embedding_model,
                    "input": text
                }
                
                response = await self.client.post(
                    self.embedding_url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['data'][0]['embedding']
                else:
                    raise Exception(f"OpenAI Embedding API error: {response.status_code}")
                    
            elif self.config.embedding_provider == "cohere":
                payload = {
                    "texts": [text],
                    "model": self.embedding_model
                }
                
                response = await self.client.post(
                    self.embedding_url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['embeddings'][0]
                else:
                    raise Exception(f"Cohere Embedding API error: {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise
    
    async def create_document_embeddings(self, document_id: str, chunks: List[Dict[str, Any]]):
        """Create embeddings for document chunks"""
        try:
            chunk_records = []
            
            for i, chunk in enumerate(chunks):
                embedding = await self.generate_embedding(chunk['content'])
                
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
            
            # Batch insert
            response = self.supabase.table('document_chunks').insert(chunk_records).execute()
            
            if not response.data:
                raise Exception("Failed to insert document chunks")
            
            self.logger.info(f"Created {len(chunk_records)} embeddings for document {document_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating document embeddings: {e}")
            raise
    
    async def search_similar_chunks(
        self,
        user_id: str,
        query: str,
        document_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
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
                    return []
            
            # Vector search
            search_response = self.supabase.rpc('search_document_chunks', {
                'query_embedding': query_embedding,
                'document_ids': document_ids,
                'similarity_threshold': similarity_threshold,
                'match_count': limit
            }).execute()
            
            return search_response.data or []
            
        except Exception as e:
            self.logger.error(f"Error searching similar chunks: {e}")
            raise
    
    async def test_embeddings(self) -> bool:
        """Test embedding generation"""
        try:
            test_text = "This is a test document for embedding generation."
            embedding = await self.generate_embedding(test_text)
            
            if embedding and len(embedding) > 0:
                self.logger.info("Embedding test successful")
                return True
            else:
                self.logger.error("Embedding test failed: empty embedding")
                return False
                
        except Exception as e:
            self.logger.error(f"Embedding test failed: {e}")
            return False

