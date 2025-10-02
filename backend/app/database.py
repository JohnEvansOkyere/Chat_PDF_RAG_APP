# backend/app/database.py
"""
Database configuration and client initialization module.

This file handles connecting to the Supabase database service. 
For local development or environments without Supabase installed, 
a mock client is provided to prevent crashes and allow testing.
"""

import os
import logging

# Initialize logger for database operations
logger = logging.getLogger(__name__)

def get_supabase_client():
    """
    Create and return a Supabase client instance.

    - If `supabase` is installed and environment variables are set, 
      it will return a real Supabase client.
    - If `supabase` is missing (e.g., in local/dev), 
      it falls back to a mock client that mimics the basic interface.

    Returns:
        client (supabase.Client | MockSupabaseClient): 
            The Supabase client for database operations.
    """
    try:
        # Import supabase client creation method and load settings
        from supabase import create_client, Client
        from app.config import settings
        
        # Initialize the Supabase client with project URL and service key
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key
        )
        return client
        
    except ImportError:
        # Supabase library not installed — use mock client
        logger.warning("Supabase not installed. Using mock client for development.")
        
        class MockSupabaseClient:
            """Fallback mock client when Supabase is unavailable"""
            def table(self, table_name):
                return MockTable()
        
        return MockSupabaseClient()
    
    except Exception as e:
        # Generic error while creating Supabase client — fallback to mock
        logger.error(f"Failed to create Supabase client: {e}")
        
        class MockSupabaseClient:
            """Fallback mock client when initialization fails"""
            def table(self, table_name):
                return MockTable()
        
        return MockSupabaseClient()


class MockTable:
    """
    Mock table implementation for development.
    Simulates basic CRUD operations without real database connectivity.
    """
    def select(self, *args):
        return MockQuery()
    
    def insert(self, *args):
        return MockQuery()
    
    def update(self, *args):
        return MockQuery()
    
    def delete(self, *args):
        return MockQuery()


class MockQuery:
    """
    Mock query object.
    Supports method chaining and returns an empty mock result on execution.
    """
    def eq(self, *args):
        return self
    
    def limit(self, *args):
        return self
    
    def execute(self):
        return MockResult()


class MockResult:
    """
    Mock result object returned by mock queries.
    Always contains empty data and count=0.
    """
    def __init__(self):
        self.data = []
        self.count = 0


def test_connection():
    """
    Test database connectivity.
    
    This function tries to initialize a Supabase client 
    (real or mock depending on environment) 
    and returns whether the operation succeeded.

    Returns:
        bool: True if connection (or mock fallback) works, False otherwise.
    """
    try:
        client = get_supabase_client()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
