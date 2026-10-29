"""Authentication Pydantic schemas."""

from typing import Optional, Literal
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponse

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["customer", "business_owner"] = "customer"
    phone: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str
    user: UserResponse
