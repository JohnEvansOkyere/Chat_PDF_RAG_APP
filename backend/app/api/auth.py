# app/api/auth.py
"""
Authentication API endpoints
Handles user registration, login, logout, and profile retrieval
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth_service import AuthService
from app.models import UserRegistrationRequest, UserLoginRequest

# Initialize router and auth service
router = APIRouter()
auth_service = AuthService()
security = HTTPBearer()

@router.post("/register")
async def register_user(data: UserRegistrationRequest):
    """
    Register a new user account.
    
    Args:
        data (UserRegistrationRequest): Email, password, and optional display_name.
    
    Returns:
        dict: A success message with the newly created user object.
    
    Raises:
        HTTPException (400): If registration fails (e.g., user already exists).
    """
    try:
        user = await auth_service.register_user(
            email=data.email,
            password=data.password,
            display_name=data.display_name
        )
        return {"user": user, "message": "Registration successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login_user(data: UserLoginRequest):
    """
    Authenticate an existing user.
    
    Args:
        data (UserLoginRequest): Email and password.
    
    Returns:
        dict: Login result including access token and user info.
    
    Raises:
        HTTPException (401): If credentials are invalid.
    """
    try:
        result = await auth_service.login_user(data.email, data.password)
        return result
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout a user by invalidating their token.
    
    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token from Authorization header.
    
    Returns:
        dict: Logout success message.
    
    Raises:
        HTTPException (400): If logout fails (e.g., invalid token).
    """
    try:
        # Verify and decode the JWT token
        user = await auth_service.verify_token(credentials.credentials)
        # Mark the user session as logged out
        await auth_service.logout_user(user["id"])
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Retrieve the authenticated user's profile.
    
    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token from Authorization header.
    
    Returns:
        dict: User profile details.
    
    Raises:
        HTTPException (404): If profile not found or token is invalid.
    """
    try:
        # Verify and decode the JWT token
        user = await auth_service.verify_token(credentials.credentials)
        # Fetch the user's profile data
        profile = await auth_service.get_user_profile(user["id"])
        return profile
    except Exception as e:
        raise HTTPException(status_code=404, detail="Profile not found")
