"""
Vector Store Management Module for VexaAI RAG Chat PDF Application
Handles document indexing and similarity search
Developed by: John Evans Okyere
"""
import logging
from typing import List, Optional, Tuple
import numpy as np

from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document

class VectorStoreManager:
    """Manages document indexing and retrieval using vector stores"""
    
    def __init__(self, config):
        """
        Initialize vector store manager with configuration
        
        Args:
            config: Configuration object containing embedding parameters
        """
        self.config = config
        self.embeddings = self._create_embeddings()
        self.vector_store = self._create_vector_store()
        self.logger = self._setup_logger()
        self._indexed_documents = []
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for vector store operations"""
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
    
    def _create_embeddings(self) -> OllamaEmbeddings:
        """Create and configure Ollama embeddings"""
        try:
            embeddings = OllamaEmbeddings(
                model=self.config.EMBEDDING_MODEL,
                base_url=self.config.OLLAMA_BASE_URL
            )
            self.logger.info(f"Initialized embeddings with model: {self.config.EMBEDDING_MODEL}")
            return embeddings
        except Exception as e:
            self.logger.error(f"Error creating embeddings: {str(e)}")
            raise
    
    def _create_vector_store(self) -> InMemoryVectorStore:
        """Create and configure in-memory vector store"""
        try:
            vector_store = InMemoryVectorStore(self.embeddings)
            self.logger.info("Initialized in-memory vector store")
            return vector_store
        except Exception as e:
            self.logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def index_documents(self, documents: List[Document]) -> bool:
        """
        Index documents in the vector store
        
        Args:
            documents: List of documents to index
            
        Returns:
            bool: True if indexing successful, False otherwise
        """
        try:
            if not documents:
                self.logger.warning("No documents provided for indexing")
                return False
            
            self.logger.info(f"Indexing {len(documents)} documents...")
            
            # Clear existing documents
            self.clear_index()
            
            # Add documents to vector store
            self.vector_store.add_documents(documents)
            
            # Store reference to indexed documents
            self._indexed_documents = documents.copy()
            
            self.logger.info(f"Successfully indexed {len(documents)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error indexing documents: {str(e)}")
            return False
    
    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """
        Perform similarity search for relevant documents
        
        Args:
            query: Search query
            k: Number of documents to return
            
        Returns:
            List[Document]: List of relevant documents
        """
        try:
            if k is None:
                k = self.config.SIMILARITY_SEARCH_K
            
            self.logger.debug(f"Performing similarity search for: '{query[:50]}...'")
            
            # Perform similarity search
            results = self.vector_store.similarity_search(query, k=k)
            
            self.logger.debug(f"Found {len(results)} relevant documents")
            return results
            
        except Exception as e:
            self.logger.error(f"Error performing similarity search: {str(e)}")
            return []
    
    def similarity_search_with_scores(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        """
        Perform similarity search with relevance scores
        
        Args:
            query: Search query
            k: Number of documents to return
            
        Returns:
            List[Tuple[Document, float]]: List of (document, score) tuples
        """
        try:
            if k is None:
                k = self.config.SIMILARITY_SEARCH_K
            
            self.logger.debug(f"Performing similarity search with scores for: '{query[:50]}...'")
            
            # Perform similarity search with scores
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Filter by relevance threshold if configured
            if hasattr(self.config, 'RELEVANCE_THRESHOLD'):
                filtered_results = [
                    (doc, score) for doc, score in results 
                    if score >= self.config.RELEVANCE_THRESHOLD
                ]
                self.logger.debug(f"Filtered to {len(filtered_results)} documents above threshold")
                return filtered_results
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error performing similarity search with scores: {str(e)}")
            return []
    
    def get_relevant_context(self, query: str, max_context_length: int = 3000) -> str:
        """
        Get relevant context for a query
        
        Args:
            query: Search query
            max_context_length: Maximum length of context to return
            
        Returns:
            str: Relevant context text
        """
        try:
            # Get relevant documents
            relevant_docs = self.similarity_search(query)
            
            if not relevant_docs:
                self.logger.warning("No relevant documents found for query")
                return "No relevant context found."
            
            # Combine document content
            context_parts = []
            total_length = 0
            
            for doc in relevant_docs:
                content = doc.page_content.strip()