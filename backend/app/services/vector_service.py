# backend/app/services/vector_service.py  
"""
Vector Service
--------------

Handles everything related to vector embeddings and similarity search:
    - Generate embeddings (OpenAI / Cohere)
    - Store embeddings into Supabase
    - Perform similarity search over document chunks
    - Test embedding functionality

This service connects the PDF processing pipeline with vector databases
to enable RAG-style question answering.
"""

import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class VectorService:
    """Service class for embeddings + vector operations"""
    
    def __init__(self):
        self.config = settings
        self.supabase = get_supabase_client()
        self.logger = logger
        self._initialize_embedding_client()
    
    # ---------------------------------------------------------
    # STEP 1: Initialize Embedding Client
    # ---------------------------------------------------------
    def _initialize_embedding_client(self):
        """Setup HTTP client and config for selected embedding provider"""
        self.client = httpx.AsyncClient(timeout=60.0)
        
        if self.config.embedding_provider == "openai":
            # OpenAI embeddings
            self.embedding_url = "https://api.openai.com/v1/embeddings"
            self.headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json"
            }
            self.embedding_model = self.config.openai_embedding_model
            
        elif self.config.embedding_provider == "cohere":
            # Cohere embeddings
            self.embedding_url = "https://api.cohere.ai/v1/embed"
            self.headers = {
                "Authorization": f"Bearer {self.config.cohere_api_key}",
                "Content-Type": "application/json"
            }
            self.embedding_model = self.config.cohere_embedding_model
    
    # ---------------------------------------------------------
    # STEP 2: Embedding Generation
    # ---------------------------------------------------------
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for given text.
        Works with both OpenAI and Cohere providers.
        """
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
    
    # ---------------------------------------------------------
    # STEP 3: Document Embeddings Creation
    # ---------------------------------------------------------
    async def create_document_embeddings(self, document_id: str, chunks: List[Dict[str, Any]]):
        """
        Create embeddings for all chunks in a document.
        Stores the embeddings + metadata into Supabase.
        """
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
            
            # Batch insert embeddings into Supabase
            response = self.supabase.table('document_chunks').insert(chunk_records).execute()
            
            if not response.data:
                raise Exception("Failed to insert document chunks")
            
            self.logger.info(f"Created {len(chunk_records)} embeddings for document {document_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating document embeddings: {e}")
            raise
    
    # ---------------------------------------------------------
    # STEP 4: Vector Search
    # ---------------------------------------------------------
    async def search_similar_chunks(
        self,
        user_id: str,
        query: str,
        document_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks based on query text.
        
        Steps:
            1. Generate query embedding
            2. Select relevant document IDs (all or specific)
            3. Call Supabase RPC for similarity search
        """
        try:
            query_embedding = await self.generate_embedding(query)
            
            # If no specific document → get all user's completed documents
            document_ids = None
            if document_id:
                document_ids = [document_id]
            else:
                docs_response = self.supabase.table('documents') \
                    .select('id') \
                    .eq('user_id', user_id) \
                    .eq('status', 'completed') \
                    .execute()
                
                if docs_response.data:
                    document_ids = [doc['id'] for doc in docs_response.data]
                else:
                    return []
            
            # Perform vector similarity search via Supabase function
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
    
    # ---------------------------------------------------------
    # STEP 5: Health Check
    # ---------------------------------------------------------
    async def test_embeddings(self) -> bool:
        """Quick test to validate that embedding generation works"""
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
