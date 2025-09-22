# backend/app/services/document_service.py
"""
Document processing service
"""

import os
import uuid
import tempfile
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import UploadFile, HTTPException
from supabase import create_client

from app.config import settings
from app.database import get_supabase_client
from app.services.vector_service import VectorService
from app.utils.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
        self.pdf_processor = PDFProcessor()
    
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
            storage_response = self.supabase.storage.from_('documents').upload(
                storage_path,
                file_content,
                file_options={
                    'content-type': file.content_type or 'application/pdf'
                }
            )
            
            if storage_response.get('error'):
                raise Exception(f"Storage upload failed: {storage_response['error']}")
            
            # Create document record
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
        """Process uploaded document: extract text, chunk, and create embeddings"""
        start_time = datetime.utcnow()
        
        try:
            # Get document record
            doc_response = self.supabase.table('documents').select('*').eq('id', document_id).single().execute()
            
            if not doc_response.data:
                raise Exception("Document not found")
            
            document = doc_response.data
            
            # Download file from storage
            file_response = self.supabase.storage.from_('documents').download(document['file_path'])
            
            if not file_response:
                raise Exception("Failed to download file from storage")
            
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(file_response)
                tmp_file_path = tmp_file.name
            
            try:
                # Process PDF
                processing_result = await self.pdf_processor.process_pdf(tmp_file_path)
                
                # Create embeddings and store chunks
                await self.vector_service.create_document_embeddings(
                    document_id=document_id,
                    chunks=processing_result['chunks']
                )
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update document with processing results
                update_data = {
                    'status': 'completed',
                    'processing_time': processing_time,
                    'page_count': processing_result['stats']['total_pages'],
                    'total_chunks': processing_result['stats']['total_chunks'],
                    'total_characters': processing_result['stats']['total_characters'],
                    'total_words': processing_result['stats']['total_words'],
                    'preview_text': processing_result['preview'],
                    'processed_at': datetime.utcnow().isoformat()
                }
                
                update_response = self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
                
                if update_response.data:
                    return update_response.data[0]
                else:
                    raise Exception("Failed to update document status")
                    
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            
            # Update document status to failed
            error_update = {
                'status': 'failed',
                'error_message': str(e),
                'processing_time': (datetime.utcnow() - start_time).total_seconds()
            }
            
            self.supabase.table('documents').update(error_update).eq('id', document_id).execute()
            raise
    
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
        # Verify ownership
        document = await self.get_document(document_id, user_id)
        
        # Delete from storage
        storage_response = self.supabase.storage.from_('documents').remove([document['file_path']])
        
        # Delete chunks
        self.supabase.table('document_chunks').delete().eq('document_id', document_id).execute()
        
        # Mark document as deleted
        self.supabase.table('documents').update({'status': 'deleted'}).eq('id', document_id).execute()

