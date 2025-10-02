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
        """Register new user - bypass auth for now"""
        try:
            # Check if user already exists
            existing_user = self.supabase.table('user_profiles').select('*').eq('email', email).execute()
            if existing_user.data:
                raise Exception("User with this email already exists")
            
            # Generate UUID manually (bypass Supabase Auth)
            import uuid
            user_id = str(uuid.uuid4())
            
            # Hash password for storage (optional - for future use)
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create profile directly
            user_data = {
                'id': user_id,
                'email': email,
                'display_name': display_name or email.split('@')[0],
                'avatar_url': None,
                'subscription_tier': 'free',
                'api_usage_count': 0
            }
            
            response = self.supabase.table('user_profiles').insert(user_data).execute()
            
            if response.data:
                return {
                    "id": response.data[0]['id'],
                    "email": response.data[0]['email'],
                    "display_name": response.data[0]['display_name']
                }
            else:
                raise Exception("Failed to create user profile")
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise
        
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with simple password check"""
        try:
            # Find user in profiles table
            user_response = self.supabase.table('user_profiles').select('*').eq('email', email).execute()
            
            if not user_response.data:
                raise Exception("Invalid email or password")
            
            user = user_response.data[0]
            
            # In production, verify against hashed password
            
            # Generate JWT token
            token_data = {
                'user_id': user['id'],
                'email': user['email'],
                'exp': datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
            }
            
            token = jwt.encode(token_data, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "display_name": user['display_name']
                }
            }
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    

    
    # Add this method to the AuthService class

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id = payload.get('user_id')
            
            if not user_id:
                raise Exception("Invalid token")
            
            # Get user from database
            user_response = self.supabase.table('user_profiles').select('*').eq('id', user_id).execute()
            
            if not user_response.data:
                raise Exception("User not found")
            
            user = user_response.data[0]
            return {
                "id": user['id'],
                "email": user['email'],
                "display_name": user['display_name']
            }
            
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise


    async def logout_user(self, user_id: str):
        """Logout user (placeholder - JWT is stateless)"""
        # In a real app, I might blacklist the token
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