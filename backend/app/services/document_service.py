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

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
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
            
            # Create document record
            document_data = {
                'id': document_id,
                'user_id': user_id,
                'filename': storage_filename,
                'original_filename': file.filename,
                'file_path': storage_path,
                'file_size': file_size,
                'mime_type': file.content_type or 'application/pdf',
                'status': 'completed'  # Set to completed for now, no processing
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
        """Process uploaded document - placeholder implementation"""
        try:
            logger.info(f"Processing document {document_id} for user {user_id}")
            
            # Update document status to completed
            update_data = {
                'status': 'completed',
                'processed_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Failed to update document status")
                
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            
            # Update document status to failed
            error_update = {
                'status': 'failed',
                'error_message': str(e)
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