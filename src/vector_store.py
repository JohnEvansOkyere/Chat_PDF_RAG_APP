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
        self.logger = self._setup_logger()


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
        """
        try:
            if not documents:
                self.logger.warning("No documents provided for indexing")
                return False

            self.logger.info(f"Indexing {len(documents)} documents...")

            # Clear existing
            self.clear_index()

            # Add texts + metadata
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            self.vector_store.add_texts(texts=texts, metadatas=metadatas)

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
                
                # Add source information if available
                if 'source_file' in doc.metadata:
                    source_info = f"[Source: {doc.metadata['source_file']}"
                    if 'page_number' in doc.metadata:
                        source_info += f", Page {doc.metadata['page_number']}"
                    source_info += "]"
                    content = f"{source_info}\n{content}"
                
                # Check if adding this content would exceed max length
                if total_length + len(content) > max_context_length:
                    # Add partial content if there's room
                    remaining_space = max_context_length - total_length
                    if remaining_space > 100:  # Only add if there's meaningful space
                        content = content[:remaining_space] + "..."
                        context_parts.append(content)
                    break
                
                context_parts.append(content)
                total_length += len(content)
            
            context = "\n\n".join(context_parts)
            self.logger.debug(f"Generated context of length {len(context)}")
            return context
            
        except Exception as e:
            self.logger.error(f"Error generating relevant context: {str(e)}")
            return "Error retrieving context."
    
    def clear_index(self):
        """Clear all indexed documents from the vector store"""
        try:
            # Recreate the vector store to clear all data
            self.vector_store = self._create_vector_store()
            self._indexed_documents = []
            self.logger.info("Cleared vector store index")
        except Exception as e:
            self.logger.error(f"Error clearing index: {str(e)}")
    
    def get_index_stats(self) -> dict:
        """
        Get statistics about the current index
        
        Returns:
            dict: Index statistics
        """
        try:
            stats = {
                'total_documents': len(self._indexed_documents),
                'embedding_model': self.config.EMBEDDING_MODEL,
                'search_k': self.config.SIMILARITY_SEARCH_K,
                'has_documents': len(self._indexed_documents) > 0
            }
            
            if self._indexed_documents:
                # Calculate additional statistics
                total_chars = sum(len(doc.page_content) for doc in self._indexed_documents)
                source_files = set(
                    doc.metadata.get('source_file', 'unknown') 
                    for doc in self._indexed_documents
                )
                
                stats.update({
                    'total_characters': total_chars,
                    'average_doc_length': total_chars // len(self._indexed_documents),
                    'source_files': list(source_files),
                    'unique_sources': len(source_files)
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting index stats: {str(e)}")
            return {'error': str(e)}
    
    def is_ready(self) -> bool:
        """
        Check if vector store is ready for queries
        
        Returns:
            bool: True if ready, False otherwise
        """
        return len(self._indexed_documents) > 0
    
    def test_embeddings(self) -> bool:
        """
        Test if embeddings are working correctly
        
        Returns:
            bool: True if embeddings work, False otherwise
        """
        try:
            test_text = "This is a test document."
            embedding = self.embeddings.embed_query(test_text)
            
            if embedding and len(embedding) > 0:
                self.logger.info("Embeddings test passed")
                return True
            else:
                self.logger.error("Embeddings test failed: empty embedding")
                return False
                
        except Exception as e:
            self.logger.error(f"Embeddings test failed: {str(e)}")
            return False
    
    def add_single_document(self, document: Document) -> bool:
        try:
            self.vector_store.add_texts(
                texts=[document.page_content],
                metadatas=[document.metadata]
            )
            self._indexed_documents.append(document)
            self.logger.info("Added single document to index")
            return True
        except Exception as e:
            self.logger.error(f"Error adding single document: {str(e)}")
            return False

    
    def remove_documents_by_source(self, source_file: str) -> bool:
        """
        Remove documents from a specific source file
        
        Args:
            source_file: Source file name to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Filter out documents from the specified source
            remaining_docs = [
                doc for doc in self._indexed_documents
                if doc.metadata.get('source_file') != source_file
            ]
            
            if len(remaining_docs) != len(self._indexed_documents):
                # Re-index remaining documents
                if remaining_docs:
                    self.index_documents(remaining_docs)
                else:
                    self.clear_index()
                
                removed_count = len(self._indexed_documents) - len(remaining_docs)
                self.logger.info(f"Removed {removed_count} documents from source: {source_file}")
                return True
            else:
                self.logger.warning(f"No documents found for source: {source_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing documents by source: {str(e)}")
            return False