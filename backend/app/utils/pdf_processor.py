# backend/app/utils/pdf_processor.py
"""
PDF processor utility
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF

from app.config import settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.config = settings
        self.logger = logger
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """Validate PDF file"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            if not file_path.lower().endswith('.pdf'):
                self.logger.error(f"Invalid file extension: {file_path}")
                return False
            
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                self.logger.error(f"File too large: {file_size_mb:.2f}MB")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating PDF: {e}")
            return False
    
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF file"""
        try:
            if not self.validate_pdf_file(file_path):
                raise ValueError(f"Invalid PDF file: {file_path}")
            
            self.logger.info(f"Processing PDF: {file_path}")
            
            doc = fitz.open(file_path)
            chunks = []
            total_text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                
                if page_text.strip():
                    total_text += page_text + "\n\n"
            
            doc.close()
            
            if not total_text.strip():
                raise ValueError("No content found in PDF")
            
            # Simple chunking - split by double newlines and limit size
            raw_chunks = total_text.split('\n\n')
            
            for i, chunk_text in enumerate(raw_chunks):
                if len(chunk_text.strip()) > 50:  # Only include substantial chunks
                    chunks.append({
                        'content': chunk_text.strip(),
                        'metadata': {
                            'source_file': os.path.basename(file_path),
                            'chunk_index': i
                        }
                    })
            
            stats = {
                'total_pages': doc.page_count if 'doc' in locals() else 0,
                'total_chunks': len(chunks),
                'total_characters': len(total_text),
                'total_words': len(total_text.split())
            }
            
            preview = total_text[:500] + "..." if len(total_text) > 500 else total_text
            
            return {
                'chunks': chunks,
                'stats': stats,
                'preview': preview
            }
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            raise