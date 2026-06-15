# backend/app/api/routers/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(request: LoginRequest):
    # TODO: Sau này thay bằng database authentication
    if request.username == "admin@odoo.ai" and request.password == "admin":
        token = create_access_token({"sub": request.username})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": request.username,
                "role": "admin"
            }
        }

    raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")