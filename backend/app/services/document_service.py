# backend/app/services/document_service.py
"""
Document processing service with PDF text extraction and chunking
"""

import os
import uuid
import tempfile
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import UploadFile, HTTPException
import PyPDF2
import io

from app.config import settings
from app.database import get_supabase_client
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
    
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
            try:
                storage_response = self.supabase.storage.from_('documents').upload(
                    storage_path,
                    file_content,
                    file_options={
                        'content-type': file.content_type or 'application/pdf'
                    }
                )
                logger.info(f"Storage upload completed for {storage_path}")
            except Exception as storage_error:
                logger.error(f"Storage upload failed: {storage_error}")
                raise Exception(f"Storage upload failed: {storage_error}")
            
            # Create document record with 'processing' status
            document_data = {
                'id': document_id,
                'user_id': user_id,
                'filename': storage_filename,
                'original_filename': file.filename,
                'file_path': storage_path,
                'file_size': file_size,
                'mime_type': file.content_type or 'application/pdf',
                'status': 'processing'  # Changed from 'completed' to 'processing'
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
        """Process uploaded document - extract text, chunk, and create embeddings"""
        try:
            logger.info(f"Processing document {document_id} for user {user_id}")
            
            # Get document record
            doc_response = self.supabase.table('documents').select('*').eq('id', document_id).single().execute()
            if not doc_response.data:
                raise Exception("Document not found")
            
            document = doc_response.data
            
            # Download file from storage
            try:
                file_response = self.supabase.storage.from_('documents').download(document['file_path'])
                if not file_response:
                    raise Exception("Failed to download file from storage")
                
                pdf_content = file_response
            except Exception as e:
                logger.error(f"Failed to download file: {e}")
                raise Exception(f"Failed to download file: {e}")
            
            # Extract text from PDF
            try:
                extracted_text = await self.extract_text_from_pdf(pdf_content)
                if not extracted_text.strip():
                    raise Exception("No text could be extracted from the PDF")
                
                logger.info(f"Extracted {len(extracted_text)} characters from PDF")
            except Exception as e:
                logger.error(f"Text extraction failed: {e}")
                raise Exception(f"Text extraction failed: {e}")
            
            # Create chunks
            try:
                chunks = await self.create_text_chunks(extracted_text, document_id)
                logger.info(f"Created {len(chunks)} chunks from document")
            except Exception as e:
                logger.error(f"Chunking failed: {e}")
                raise Exception(f"Chunking failed: {e}")
            
            # Create embeddings and store chunks
            try:
                await self.vector_service.create_document_embeddings(document_id, chunks)
                logger.info(f"Created embeddings for {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Embedding creation failed: {e}")
                raise Exception(f"Embedding creation failed: {e}")
            
            # Update document status to completed
            update_data = {
                'status': 'completed',
                'processed_at': datetime.utcnow().isoformat(),
                'chunk_count': len(chunks),
                'text_length': len(extracted_text)
            }
            
            response = self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
            
            if response.data:
                logger.info(f"Document {document_id} processed successfully")
                return response.data[0]
            else:
                raise Exception("Failed to update document status")
                
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            
            # Update document status to failed
            error_update = {
                'status': 'failed',
                'error_message': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('documents').update(error_update).eq('id', document_id).execute()
            raise
    
    async def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n\n--- Page {page_num + 1} ---\n\n"
                    text += page_text
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise Exception(f"PDF text extraction failed: {e}")
    
    async def create_text_chunks(self, text: str, document_id: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Create overlapping text chunks"""
        try:
            chunks = []
            
            # Split text into sentences first for better chunking
            sentences = text.split('. ')
            
            current_chunk = ""
            current_size = 0
            chunk_index = 0
            start_index = 0
            
            for i, sentence in enumerate(sentences):
                sentence_with_period = sentence + ('. ' if i < len(sentences) - 1 else '')
                sentence_length = len(sentence_with_period)
                
                # If adding this sentence would exceed chunk_size, create a chunk
                if current_size + sentence_length > chunk_size and current_chunk:
                    chunk_data = {
                        'content': current_chunk.strip(),
                        'chunk_index': chunk_index,
                        'start_index': start_index,
                        'end_index': start_index + len(current_chunk),
                        'metadata': {
                            'chunk_size': len(current_chunk),
                            'sentence_count': current_chunk.count('. ') + 1,
                            'document_id': document_id
                        }
                    }
                    chunks.append(chunk_data)
                    
                    # Create overlap for next chunk
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + sentence_with_period
                    current_size = len(current_chunk)
                    chunk_index += 1
                    start_index += len(current_chunk) - len(overlap_text)
                else:
                    current_chunk += sentence_with_period
                    current_size += sentence_length
            
            # Add final chunk if it has content
            if current_chunk.strip():
                chunk_data = {
                    'content': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'start_index': start_index,
                    'end_index': start_index + len(current_chunk),
                    'metadata': {
                        'chunk_size': len(current_chunk),
                        'sentence_count': current_chunk.count('. ') + 1,
                        'document_id': document_id
                    }
                }
                chunks.append(chunk_data)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            raise Exception(f"Text chunking failed: {e}")
    
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
        try:
            # Get document first
            document = await self.get_document(document_id, user_id)
            
            # Try to delete from storage
            try:
                self.supabase.storage.from_('documents').remove([document['file_path']])
            except Exception as e:
                logger.warning(f"Failed to delete file from storage: {e}")
            
            # Delete chunks if they exist
            try:
                self.supabase.table('document_chunks').delete().eq('document_id', document_id).execute()
            except Exception as e:
                logger.warning(f"Failed to delete chunks: {e}")
            
            # Mark document as deleted
            self.supabase.table('documents').update({'status': 'deleted'}).eq('id', document_id).execute()
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise