# backend/app/services/auth_service.py
"""
Authentication service with Supabase integration
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.jwt_secret = settings.jwt_secret
        self.jwt_algorithm = settings.jwt_algorithm
    
    async def register_user(self, email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Register new user using Supabase Auth"""
        try:
            # Check if user already exists in profiles
            existing_user = self.supabase.table('user_profiles').select('*').eq('email', email).execute()
            if existing_user.data:
                raise Exception("User with this email already exists")
            
            # Create user with Supabase Auth first
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Create profile with the auth user's ID
                user_data = {
                    'id': auth_response.user.id,  # Use the auth user's UUID
                    'email': email,
                    'display_name': display_name or email.split('@')[0],
                    'avatar_url': None,
                    'subscription_tier': 'free',
                    'api_usage_count': 0
                }
                
                # Insert into user_profiles
                response = self.supabase.table('user_profiles').insert(user_data).execute()
                
                if response.data:
                    return {
                        "id": response.data[0]['id'],
                        "email": response.data[0]['email'],
                        "display_name": response.data[0]['display_name']
                    }
                else:
                    raise Exception("Failed to create user profile")
            else:
                raise Exception("Failed to create auth user")
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise
        
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user using Supabase Auth"""
        try:
            # Use Supabase Auth for login
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                # Get user profile
                user_response = self.supabase.table('user_profiles').select('*').eq('id', auth_response.user.id).execute()
                
                if user_response.data:
                    user = user_response.data[0]
                    return {
                        "access_token": auth_response.session.access_token,
                        "token_type": "bearer",
                        "expires_in": auth_response.session.expires_in or 3600,
                        "user": {
                            "id": user['id'],
                            "email": user['email'],
                            "display_name": user['display_name']
                        }
                    }
                else:
                    raise Exception("User profile not found")
            else:
                raise Exception("Invalid email or password")
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    async def logout_user(self, user_id: str):
        """Logout user (placeholder - JWT is stateless)"""
        # In a real app, you might blacklist the token
        logger.info(f"User {user_id} logged out")
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        response = self.supabase.table('user_profiles').select('*').eq('id', user_id).single().execute()
        
        if response.data:
            return response.data
        else:
            raise Exception("Profile not found")
    
    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user usage statistics"""
        return {
            "total_requests": 0,
            "requests_today": 0,
            "total_tokens_used": 0,
            "tokens_today": 0
        }