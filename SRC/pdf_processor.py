"""
PDF Processing Module for VexaAI RAG Chat PDF Application
Handles PDF loading, text extraction, and document splitting
Developed by: John Evans Okyere
"""
import os
import logging
from typing import List, Optional
from pathlib import Path

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class PDFProcessor:
    """Handles PDF document processing and text splitting"""
    
    def __init__(self, config):
        """
        Initialize PDF processor with configuration
        
        Args:
            config: Configuration object containing processing parameters
        """
        self.config = config
        self.text_splitter = self._create_text_splitter()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for PDF processing"""
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
    
    def _create_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Create and configure text splitter"""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """
        Validate PDF file before processing
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            # Check file extension
            if not file_path.lower().endswith('.pdf'):
                self.logger.error(f"Invalid file extension: {file_path}")
                return False
            
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.config.MAX_FILE_SIZE_MB:
                self.logger.error(f"File too large: {file_size_mb:.2f}MB > {self.config.MAX_FILE_SIZE_MB}MB")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating PDF file: {str(e)}")
            return False
    
    def load_pdf(self, file_path: str) -> List[Document]:
        """
        Load PDF document and extract text
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List[Document]: List of loaded documents
            
        Raises:
            Exception: If PDF loading fails
        """
        try:
            # Validate file first
            if not self.validate_pdf_file(file_path):
                raise ValueError(f"Invalid PDF file: {file_path}")
            
            self.logger.info(f"Loading PDF: {file_path}")
            
            # Load PDF using PDFPlumberLoader
            loader = PDFPlumberLoader(file_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError("No content found in PDF")
            
            # Add metadata
            for i, doc in enumerate(documents):
                doc.metadata.update({
                    'source_file': os.path.basename(file_path),
                    'page_number': i + 1,
                    'total_pages': len(documents),
                    'file_size': os.path.getsize(file_path),
                    'processing_timestamp': str(Path(file_path).stat().st_mtime)
                })
            
            self.logger.info(f"Successfully loaded {len(documents)} pages from PDF")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error loading PDF {file_path}: {str(e)}")
            raise Exception(f"Failed to load PDF: {str(e)}")
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks
        
        Args:
            documents: List of documents to split
            
        Returns:
            List[Document]: List of chunked documents
        """
        try:
            self.logger.info(f"Splitting {len(documents)} documents into chunks")
            
            # Split documents using the text splitter
            chunked_documents = self.text_splitter.split_documents(documents)
            
            # Add chunk metadata
            for i, chunk in enumerate(chunked_documents):
                chunk.metadata.update({
                    'chunk_id': i,
                    'chunk_size': len(chunk.page_content),
                    'total_chunks': len(chunked_documents)
                })
            
            self.logger.info(f"Created {len(chunked_documents)} chunks")
            return chunked_documents
            
        except Exception as e:
            self.logger.error(f"Error splitting documents: {str(e)}")
            raise Exception(f"Failed to split documents: {str(e)}")
    
    def process_pdf(self, file_path: str) -> List[Document]:
        """
        Complete PDF processing pipeline
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List[Document]: List of processed and chunked documents
        """
        try:
            # Load PDF
            documents = self.load_pdf(file_path)
            
            # Split into chunks
            chunked_documents = self.split_documents(documents)
            
            return chunked_documents
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    def get_document_stats(self, documents: List[Document]) -> dict:
        """
        Get statistics about processed documents
        
        Args:
            documents: List of processed documents
            
        Returns:
            dict: Document statistics
        """
        if not documents:
            return {}
        
        total_chars = sum(len(doc.page_content) for doc in documents)
        total_words = sum(len(doc.page_content.split()) for doc in documents)
        
        # Get unique source files
        source_files = set(doc.metadata.get('source_file', 'unknown') for doc in documents)
        
        # Get page information if available
        pages = set(doc.metadata.get('page_number', 0) for doc in documents)
        
        stats = {
            'total_chunks': len(documents),
            'total_characters': total_chars,
            'total_words': total_words,
            'average_chunk_size': total_chars // len(documents) if documents else 0,
            'source_files': list(source_files),
            'total_pages': len(pages) if 0 not in pages else 0,
            'chunk_size_config': self.config.CHUNK_SIZE,
            'chunk_overlap_config': self.config.CHUNK_OVERLAP
        }
        
        return stats
    
    def extract_text_preview(self, documents: List[Document], max_length: int = 500) -> str:
        """
        Extract a preview of the document text
        
        Args:
            documents: List of documents
            max_length: Maximum length of preview text
            
        Returns:
            str: Preview text
        """
        if not documents:
            return "No content available"
        
        # Get text from first few chunks
        preview_text = ""
        for doc in documents[:3]:  # First 3 chunks
            preview_text += doc.page_content + "\n\n"
            if len(preview_text) > max_length:
                break
        
        # Truncate if necessary
        if len(preview_text) > max_length:
            preview_text = preview_text[:max_length] + "..."
        
        return preview_text.strip()