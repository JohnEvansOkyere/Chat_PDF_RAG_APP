# backend/app/services/auth_service.py
"""
Authentication service with Supabase integration
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt

from app.config import settings
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.jwt_secret = settings.jwt_secret
        self.jwt_algorithm = settings.jwt_algorithm

    def _build_app_token(self, user: Dict[str, Any]) -> str:
        """Create the app JWT used by the FastAPI auth dependency."""
        token_data = {
            'user_id': user['id'],
            'email': user['email'],
            'exp': datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        }
        return jwt.encode(token_data, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _serialize_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Return the profile payload expected by API consumers."""
        return {
            "id": profile["id"],
            "email": profile["email"],
            "display_name": profile.get("display_name"),
        }

    async def _get_profile_by_id_with_retry(self, user_id: str, attempts: int = 3, delay: float = 0.35) -> Optional[Dict[str, Any]]:
        """
        Fetch a user profile with small retries.

        This handles the common Supabase pattern where an auth trigger creates
        `user_profiles` shortly after the auth user is created.
        """
        for attempt in range(attempts):
            response = self.supabase.table('user_profiles').select('*').eq('id', user_id).execute()
            if response.data:
                return response.data[0]

            if attempt < attempts - 1:
                await asyncio.sleep(delay)

        return None
    
    async def register_user(self, email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user through Supabase Auth, then create the profile row."""
        try:
            # Check if user already exists
            existing_user = self.supabase.table('user_profiles').select('*').eq('email', email).execute()
            if existing_user.data:
                raise Exception("User with this email already exists")

            auth_response = self.supabase.auth.admin.create_user({
                'email': email,
                'password': password,
                'email_confirm': True,
                'user_metadata': {
                    'display_name': display_name or email.split('@')[0],
                },
            })

            auth_user = auth_response.user
            if not auth_user:
                raise Exception("Failed to create auth user")

            # If the database has an auth trigger that creates the profile,
            # prefer that row and avoid inserting a duplicate manually.
            existing_profile = await self._get_profile_by_id_with_retry(auth_user.id)
            if existing_profile:
                profile_update = {
                    'email': email,
                    'display_name': display_name or existing_profile.get('display_name') or email.split('@')[0],
                }
                updated = (
                    self.supabase
                    .table('user_profiles')
                    .update(profile_update)
                    .eq('id', auth_user.id)
                    .execute()
                )

                if updated.data:
                    return self._serialize_profile(updated.data[0])

                return self._serialize_profile(existing_profile)

            user_data = {
                'id': auth_user.id,
                'email': email,
                'display_name': display_name or email.split('@')[0],
                'avatar_url': None,
                'subscription_tier': 'free',
                'api_usage_count': 0
            }

            try:
                response = self.supabase.table('user_profiles').insert(user_data).execute()
                if response.data:
                    return self._serialize_profile(response.data[0])
            except Exception as insert_error:
                # Another process/trigger may have created the profile between the
                # read and insert; fetch the row and return it instead of failing.
                logger.warning(f"Profile insert raced with existing row: {insert_error}")
                raced_profile = await self._get_profile_by_id_with_retry(auth_user.id)
                if raced_profile:
                    return self._serialize_profile(raced_profile)
                raise

            raise Exception("Failed to create user profile")
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise
        
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with Supabase password auth, then issue the app JWT."""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                'email': email,
                'password': password,
            })

            auth_user = getattr(auth_response, 'user', None)
            if not auth_user:
                raise Exception("Invalid email or password")

            user_response = self.supabase.table('user_profiles').select('*').eq('id', auth_user.id).single().execute()
            if not user_response.data:
                raise Exception("User profile not found")

            user = user_response.data
            token = self._build_app_token(user)
            
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
