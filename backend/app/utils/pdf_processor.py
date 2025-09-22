# # backend/app/utils/pdf_processor.py
# """
# PDF processor utility
# """

# import os
# import logging
# from typing import List, Dict, Any
# from pathlib import Path
# import fitz  # PyMuPDF

# from app.config import settings

# logger = logging.getLogger(__name__)

# class PDFProcessor:
#     def __init__(self):
#         self.config = settings
#         self.logger = logger
    
#     def validate_pdf_file(self, file_path: str) -> bool:
#         """Validate PDF file"""
#         try:
#             if not os.path.exists(file_path):
#                 self.logger.error(f"File not found: {file_path}")
#                 return False
            
#             if not file_path.lower().endswith('.pdf'):
#                 self.logger.error(f"Invalid file extension: {file_path}")
#                 return False
            
#             file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
#             if file_size_mb > self.config.max_file_size_mb:
#                 self.logger.error(f"File too large: {file_size_mb:.2f}MB")
#                 return False
            
#             return True
            
#         except Exception as e:
#             self.logger.error(f"Error validating PDF: {e}")
#             return False
    
#     async def process_pdf(self, file_path: str) -> Dict[str, Any]:
#         """Process PDF file"""
#         try:
#             if not self.validate_pdf_file(file_path):
#                 raise ValueError(f"Invalid PDF file: {file_path}")
            
#             self.logger.info(f"Processing PDF: {file_path}")
            
#             doc = fitz.open(file_path)
#             chunks = []
#             total_text = ""
            
#             for page_num in range(doc.page_count):
#                 page = doc[page_num]
#                 page_text = page.get_text()
                
#                 if page_text.strip():
#                     total_text += page_text + "\n\n"
            
#             doc.close()
            
#             if not total_text.strip():
#                 raise ValueError("No content found in PDF")
            
#             # Simple chunking - split by double newlines and limit size
#             raw_chunks = total_text.split('\n\n')
            
#             for i, chunk_text in enumerate(raw_chunks):
#                 if len(chunk_text.strip()) > 50:  # Only include substantial chunks
#                     chunks.append({
#                         'content': chunk_text.strip(),
#                         'metadata': {
#                             'source_file': os.path.basename(file_path),
#                             'chunk_index': i
#                         }
#                     })
            
#             stats = {
#                 'total_pages': doc.page_count if 'doc' in locals() else 0,
#                 'total_chunks': len(chunks),
#                 'total_characters': len(total_text),
#                 'total_words': len(total_text.split())
#             }
            
#             preview = total_text[:500] + "..." if len(total_text) > 500 else total_text
            
#             return {
#                 'chunks': chunks,
#                 'stats': stats,
#                 'preview': preview
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error processing PDF: {e}")
#             raise





# backend/app/utils/pdf_processor.py
"""
PDF processing utility adapted from original code
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """Validate PDF file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            if not file_path.lower().endswith('.pdf'):
                logger.error(f"Invalid file extension: {file_path}")
                return False
            
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                logger.error(f"File too large: {file_size_mb:.2f}MB > {settings.max_file_size_mb}MB")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating PDF file: {str(e)}")
            return False
    
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF file and return chunks with metadata"""
        try:
            if not self.validate_pdf_file(file_path):
                raise ValueError(f"Invalid PDF file: {file_path}")
            
            logger.info(f"Processing PDF: {file_path}")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(file_path)
            
            pages_text = []
            total_text = ""
            
            # Extract text from each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                
                pages_text.append({
                    'page_number': page_num + 1,
                    'content': page_text,
                    'metadata': {
                        'source_file': os.path.basename(file_path),
                        'page_number': page_num + 1,
                        'total_pages': doc.page_count
                    }
                })
                
                total_text += page_text + "\n\n"
            
            doc.close()
            
            if not total_text.strip():
                raise ValueError("No content found in PDF")
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(total_text)
            
            # Create chunk objects with metadata
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Find which page this chunk belongs to
                page_number = self._find_page_for_chunk(chunk, pages_text)
                
                chunk_obj = {
                    'content': chunk,
                    'chunk_index': i,
                    'metadata': {
                        'source_file': os.path.basename(file_path),
                        'chunk_id': i,
                        'page_number': page_number,
                        'total_chunks': len(chunks)
                    },
                    'page_number': page_number,
                    'start_index': total_text.find(chunk)
                }
                
                processed_chunks.append(chunk_obj)
            
            # Generate statistics
            stats = {
                'total_pages': doc.page_count if 'doc' in locals() else len(pages_text),
                'total_chunks': len(processed_chunks),
                'total_characters': len(total_text),
                'total_words': len(total_text.split()),
                'average_chunk_size': len(total_text) // len(processed_chunks) if processed_chunks else 0
            }
            
            # Generate preview
            preview = total_text[:500] + "..." if len(total_text) > 500 else total_text
            
            logger.info(f"Successfully processed PDF: {stats['total_chunks']} chunks from {stats['total_pages']} pages")
            
            return {
                'chunks': processed_chunks,
                'stats': stats,
                'preview': preview
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    def _find_page_for_chunk(self, chunk: str, pages_text: List[Dict]) -> int:
        """Find which page a chunk belongs to"""
        for page_data in pages_text:
            if chunk[:100] in page_data['content']:
                return page_data['page_number']
        return 1  # Default to page 1 if not found
