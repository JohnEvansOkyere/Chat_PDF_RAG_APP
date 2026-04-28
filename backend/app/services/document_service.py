# backend/app/services/document_service.py
"""
Document processing service with PDF text extraction, chunking, 
and embedding creation for retrieval-augmented generation (RAG).
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
        """Initialize DocumentService with Supabase client and VectorService"""
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
        self.storage_bucket = settings.storage_bucket
    
    async def create_document(self, user_id: str, file: UploadFile) -> Dict[str, Any]:
        """
        Create a document record and upload file to storage.

        Steps:
            1. Generate unique ID and storage path.
            2. Upload file to Supabase storage.
            3. Save document record with status = 'processing'.

        Args:
            user_id (str): ID of the uploading user.
            file (UploadFile): Uploaded file object.

        Returns:
            Dict[str, Any]: Document record from database.
        """
        try:
            # Generate unique document ID and storage path
            document_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            storage_filename = f"{document_id}{file_extension}"
            storage_path = f"{user_id}/{storage_filename}"
            
            # Read file content in memory
            file_content = await file.read()
            file_size = len(file_content)
            
            # Upload to Supabase storage bucket
            try:
                storage_response = self.supabase.storage.from_(self.storage_bucket).upload(
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
            
            # Create DB record with "processing" status (not completed yet)
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
        """
        Process uploaded document:
            1. Download from storage.
            2. Extract text from PDF.
            3. Split into chunks.
            4. Generate embeddings for chunks.
            5. Update document status.

        Args:
            document_id (str): ID of document to process.
            user_id (str): ID of the user.

        Returns:
            Dict[str, Any]: Updated document record.
        """
        try:
            logger.info(f"Processing document {document_id} for user {user_id}")
            
            # Get document metadata from DB
            doc_response = self.supabase.table('documents').select('*').eq('id', document_id).single().execute()
            if not doc_response.data:
                raise Exception("Document not found")
            
            document = doc_response.data
            
            # Step 1: Download file from storage
            try:
                file_response = self.supabase.storage.from_(self.storage_bucket).download(document['file_path'])
                if not file_response:
                    raise Exception("Failed to download file from storage")
                pdf_content = file_response
            except Exception as e:
                logger.error(f"Failed to download file: {e}")
                raise Exception(f"Failed to download file: {e}")
            
            # Step 2: Extract raw text from PDF
            try:
                extracted_text = await self.extract_text_from_pdf(pdf_content)
                if not extracted_text.strip():
                    raise Exception("No text could be extracted from the PDF")
                
                logger.info(f"Extracted {len(extracted_text)} characters from PDF")
            except Exception as e:
                logger.error(f"Text extraction failed: {e}")
                raise Exception(f"Text extraction failed: {e}")
            
            # Step 3: Split text into overlapping chunks
            try:
                chunks = await self.create_text_chunks(extracted_text, document_id)
                logger.info(f"Created {len(chunks)} chunks from document")
            except Exception as e:
                logger.error(f"Chunking failed: {e}")
                raise Exception(f"Chunking failed: {e}")
            
            # Step 4: Generate embeddings and save
            try:
                await self.vector_service.create_document_embeddings(document_id, chunks)
                logger.info(f"Created embeddings for {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Embedding creation failed: {e}")
                raise Exception(f"Embedding creation failed: {e}")
            
            # Step 5: Update document status → completed
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
            
            # If processing fails, update DB status → failed
            error_update = {
                'status': 'failed',
                'error_message': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('documents').update(error_update).eq('id', document_id).execute()
            raise
    
    async def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract plain text from a PDF file.

        Args:
            pdf_content (bytes): PDF file bytes.

        Returns:
            str: Extracted text with page markers.
        """
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
        """
        Split text into overlapping chunks for embedding.

        Args:
            text (str): Raw document text.
            document_id (str): Document ID (for metadata).
            chunk_size (int): Maximum characters per chunk.
            overlap (int): Overlap size between chunks.

        Returns:
            List[Dict[str, Any]]: List of chunk dictionaries.
        """
        try:
            chunks = []
            
            # Break text by sentences for natural splits
            sentences = text.split('. ')
            
            current_chunk = ""
            current_size = 0
            chunk_index = 0
            start_index = 0
            
            for i, sentence in enumerate(sentences):
                sentence_with_period = sentence + ('. ' if i < len(sentences) - 1 else '')
                sentence_length = len(sentence_with_period)
                
                # If adding sentence exceeds chunk_size → save current chunk
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
                    
                    # Build new chunk with overlap
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + sentence_with_period
                    current_size = len(current_chunk)
                    chunk_index += 1
                    start_index += len(current_chunk) - len(overlap_text)
                else:
                    current_chunk += sentence_with_period
                    current_size += sentence_length
            
            # Add final chunk
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
        """
        Get single document metadata by ID.

        Args:
            document_id (str): Document ID.
            user_id (str): User ID (ownership check).

        Returns:
            Dict[str, Any]: Document record.
        """
        response = self.supabase.table('documents').select('*').eq('id', document_id).eq('user_id', user_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return response.data
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents belonging to a user.

        Args:
            user_id (str): User identifier.

        Returns:
            List[Dict[str, Any]]: List of documents.
        """
        response = self.supabase.table('documents').select('*').eq('user_id', user_id).neq('status', 'deleted').order('created_at', desc=True).execute()
        return response.data or []
    
    async def delete_document(self, document_id: str, user_id: str):
        """
        Delete document and associated data.

        Steps:
            1. Delete file from storage.
            2. Delete related chunks from DB.
            3. Mark document as 'deleted' in DB.

        Args:
            document_id (str): ID of the document.
            user_id (str): ID of the owner.
        """
        try:
            # Step 1: Fetch document metadata
            document = await self.get_document(document_id, user_id)
            
            # Step 2: Delete file from storage bucket
            try:
                self.supabase.storage.from_(self.storage_bucket).remove([document['file_path']])
            except Exception as e:
                logger.warning(f"Failed to delete file from storage: {e}")
            
            # Step 3: Delete all document chunks
            try:
                self.supabase.table('document_chunks').delete().eq('document_id', document_id).execute()
            except Exception as e:
                logger.warning(f"Failed to delete chunks: {e}")
            
            # Step 4: Mark document record as deleted
            self.supabase.table('documents').update({'status': 'deleted'}).eq('id', document_id).execute()
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
