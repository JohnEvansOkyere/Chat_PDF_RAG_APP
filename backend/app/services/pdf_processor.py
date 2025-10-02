# backend/app/services/pdf_processor.py
"""
Cloud-adapted PDF processing service
------------------------------------

This service is responsible for handling all PDF-related tasks in a cloud-friendly way:
    - Validating PDF files (size, format, existence)
    - Extracting text content from PDF pages using PyMuPDF
    - Splitting large documents into smaller chunks for LLM processing
    - Generating statistics & text previews for downstream use

This version is adapted from your original processor, optimized for cloud deployments.
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile

import fitz  # PyMuPDF → fast & reliable PDF parsing, better than pdfplumber in cloud
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)

class CloudPDFProcessor:
    """Main class for PDF processing in a cloud environment"""
    
    def __init__(self):
        # Initialize text splitter → breaks large texts into chunks for embeddings/LLMs
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.logger = logger
    
    # ---------------------------------------------------------
    # STEP 1: PDF Validation
    # ---------------------------------------------------------
    def validate_pdf_file(self, file_path: str) -> bool:
        """Check if a given file is a valid PDF and within allowed size"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            if not file_path.lower().endswith('.pdf'):
                self.logger.error(f"Invalid file extension: {file_path}")
                return False
            
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                self.logger.error(f"File too large: {file_size_mb:.2f}MB > {settings.max_file_size_mb}MB")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating PDF file: {str(e)}")
            return False
    
    # ---------------------------------------------------------
    # STEP 2: PDF Loading & Extraction
    # ---------------------------------------------------------
    async def load_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Open and read PDF file using PyMuPDF.
        Extracts plain text from each page along with metadata.
        """
        try:
            if not self.validate_pdf_file(file_path):
                raise ValueError(f"Invalid PDF file: {file_path}")
            
            self.logger.info(f"Loading PDF: {file_path}")
            
            # Open PDF → page by page
            doc = fitz.open(file_path)
            documents = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                
                if page_text.strip():  # Skip empty pages
                    doc_data = {
                        'page_content': page_text,
                        'metadata': {
                            'source_file': os.path.basename(file_path),
                            'page_number': page_num + 1,
                            'total_pages': doc.page_count,
                            'file_size': os.path.getsize(file_path),
                            'processing_timestamp': str(Path(file_path).stat().st_mtime)
                        }
                    }
                    documents.append(doc_data)
            
            doc.close()
            
            if not documents:
                raise ValueError("No content found in PDF")
            
            self.logger.info(f"Successfully loaded {len(documents)} pages from PDF")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error loading PDF {file_path}: {str(e)}")
            raise Exception(f"Failed to load PDF: {str(e)}")
    
    # ---------------------------------------------------------
    # STEP 3: Document Splitting
    # ---------------------------------------------------------
    async def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Break down extracted PDF text into smaller chunks
        → Makes it easier for embeddings & LLM context handling
        """
        try:
            self.logger.info(f"Splitting {len(documents)} documents into chunks")
            
            all_chunks = []
            chunk_id = 0
            
            for doc in documents:
                # Use text splitter for recursive chunking
                chunks = self.text_splitter.split_text(doc['page_content'])
                
                for chunk_text in chunks:
                    chunk_data = {
                        'content': chunk_text,
                        'metadata': {
                            **doc['metadata'],
                            'chunk_id': chunk_id,
                            'chunk_size': len(chunk_text),
                            'chunk_index': len(all_chunks)
                        }
                    }
                    all_chunks.append(chunk_data)
                    chunk_id += 1
            
            # Attach total chunk info for reference
            for chunk in all_chunks:
                chunk['metadata']['total_chunks'] = len(all_chunks)
            
            self.logger.info(f"Created {len(all_chunks)} chunks")
            return all_chunks
            
        except Exception as e:
            self.logger.error(f"Error splitting documents: {str(e)}")
            raise Exception(f"Failed to split documents: {str(e)}")
    
    # ---------------------------------------------------------
    # STEP 4: Full Pipeline
    # ---------------------------------------------------------
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline:
            1. Load PDF pages
            2. Split into chunks
            3. Generate statistics
            4. Create text preview
        """
        try:
            documents = await self.load_pdf(file_path)          # Load
            chunked_documents = await self.split_documents(documents)  # Split
            stats = self.get_document_stats(chunked_documents)  # Stats
            preview = self.extract_text_preview(chunked_documents)  # Preview
            
            return {
                'chunks': chunked_documents,
                'stats': stats,
                'preview': preview
            }
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    # ---------------------------------------------------------
    # STEP 5: Utilities (Stats + Preview)
    # ---------------------------------------------------------
    def get_document_stats(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate basic statistics from chunked documents"""
        if not documents:
            return {}
        
        total_chars = sum(len(doc['content']) for doc in documents)
        total_words = sum(len(doc['content'].split()) for doc in documents)
        
        source_files = set(doc['metadata'].get('source_file', 'unknown') for doc in documents)
        pages = set(doc['metadata'].get('page_number', 0) for doc in documents)
        
        stats = {
            'total_chunks': len(documents),
            'total_characters': total_chars,
            'total_words': total_words,
            'average_chunk_size': total_chars // len(documents) if documents else 0,
            'source_files': list(source_files),
            'total_pages': len(pages) if 0 not in pages else 0,
            'chunk_size_config': settings.chunk_size,
            'chunk_overlap_config': settings.chunk_overlap
        }
        
        return stats
    
    def extract_text_preview(self, documents: List[Dict[str, Any]], max_length: int = 500) -> str:
        """Return a short preview (first few chunks of extracted text)"""
        if not documents:
            return "No content available"
        
        preview_text = ""
        for doc in documents[:3]:  # Take first 3 chunks only
            preview_text += doc['content'] + "\n\n"
            if len(preview_text) > max_length:
                break
        
        # Truncate if too long
        if len(preview_text) > max_length:
            preview_text = preview_text[:max_length] + "..."
        
        return preview_text.strip()
