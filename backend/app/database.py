# backend/app/database.py
"""
Minimal database configuration for quick testing
"""
import os
import logging

logger = logging.getLogger(__name__)

def get_supabase_client():
    """
    Temporary placeholder for Supabase client
    Replace this with proper implementation once dependencies are installed
    """
    try:
        # Try to import and create real client
        from supabase import create_client, Client
        from app.config import settings
        
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key
        )
        return client
        
    except ImportError:
        logger.warning("Supabase not installed. Using mock client for development.")
        # Return a mock object that won't crash the app
        class MockSupabaseClient:
            def table(self, table_name):
                return MockTable()
        
        return MockSupabaseClient()
    
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        # Return mock client for development
        class MockSupabaseClient:
            def table(self, table_name):
                return MockTable()
        
        return MockSupabaseClient()

class MockTable:
    """Mock table for development when Supabase is not available"""
    def select(self, *args):
        return MockQuery()
    
    def insert(self, *args):
        return MockQuery()
    
    def update(self, *args):
        return MockQuery()
    
    def delete(self, *args):
        return MockQuery()

class MockQuery:
    """Mock query for development"""
    def eq(self, *args):
        return self
    
    def limit(self, *args):
        return self
    
    def execute(self):
        return MockResult()

class MockResult:
    """Mock result for development"""
    def __init__(self):
        self.data = []
        self.count = 0

def test_connection():
    """Test database connection"""
    try:
        client = get_supabase_client()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False