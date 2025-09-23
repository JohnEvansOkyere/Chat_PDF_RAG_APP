# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str

@router.post("/register")
async def register_user(data: RegisterRequest):
    try:
        user = await auth_service.register_user(
            email=data.email,
            password=data.password,
            display_name=data.display_name
        )
        return {"user": user, "message": "Registration successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
