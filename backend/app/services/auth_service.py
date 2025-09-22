# backend/app/services/auth_service.py
"""
Authentication service
"""

import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def register_user(self, email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Register new user"""
        try:
            # Use Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "display_name": display_name or email.split("@")[0]
                    }
                }
            })
            
            if auth_response.user:
                return {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "display_name": display_name
                }
            else:
                raise Exception("User registration failed")
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                return {
                    "access_token": auth_response.session.access_token,
                    "token_type": "bearer",
                    "expires_in": auth_response.session.expires_in,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "display_name": auth_response.user.user_metadata.get("display_name")
                    }
                }
            else:
                raise Exception("Login failed")
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            # Use Supabase to verify token
            auth_response = self.supabase.auth.get_user(token)
            
            if auth_response.user:
                return {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "display_name": auth_response.user.user_metadata.get("display_name")
                }
            else:
                raise Exception("Invalid token")
                
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise
    
    async def logout_user(self, user_id: str):
        """Logout user"""
        try:
            self.supabase.auth.sign_out()
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            raise
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        response = self.supabase.table('user_profiles').select('*').eq('id', user_id).single().execute()
        
        if response.data:
            return response.data
        else:
            raise Exception("Profile not found")
    
    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user usage statistics"""
        try:
            # Get usage from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            usage_response = self.supabase.table('api_usage').select('*').eq('user_id', user_id).gte('created_at', thirty_days_ago.isoformat()).execute()
            
            usage_data = usage_response.data or []
            
            total_requests = len(usage_data)
            total_tokens = sum(record.get('tokens_used', 0) for record in usage_data)
            
            # Get today's usage
            today = datetime.utcnow().date()
            today_usage = [record for record in usage_data if record['created_at'].startswith(str(today))]
            
            return {
                "total_requests": total_requests,
                "requests_today": len(today_usage),
                "total_tokens_used": total_tokens,
                "tokens_today": sum(record.get('tokens_used', 0) for record in today_usage),
                "average_response_time": sum(record.get('response_time', 0) for record in usage_data) / max(len(usage_data), 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise
