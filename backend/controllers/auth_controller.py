from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from backend.services.command_handlers.auth_command_handler import AuthCommandHandler

router = APIRouter()
command_handler = AuthCommandHandler()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(request: RegisterRequest) -> dict:
    try:
        return await command_handler.register(request.email, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Detailed Register Error: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(exc)}") from exc


@router.post("/login")
async def login(request: LoginRequest) -> dict:
    try:
        return await command_handler.login(request.email, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Detailed Login Error: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(exc)}") from exc
