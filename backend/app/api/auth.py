# app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth_service import AuthService
from app.models import UserRegistrationRequest, UserLoginRequest

router = APIRouter()
auth_service = AuthService()
security = HTTPBearer()

@router.post("/register")
async def register_user(data: UserRegistrationRequest):
    """Register a new user"""
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
    """Login user"""
    try:
        result = await auth_service.login_user(data.email, data.password)
        return result
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        await auth_service.logout_user(user["id"])
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user profile"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        profile = await auth_service.get_user_profile(user["id"])
        return profile
    except Exception as e:
        raise HTTPException(status_code=404, detail="Profile not found")