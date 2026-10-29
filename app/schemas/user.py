"""User Pydantic schemas."""

from typing import Optional, Literal
from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    status: str = "active"
    phone: Optional[str] = None
    avatar: Optional[str] = None
    created_at: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None

class UserInDB(UserResponse):
    password: str
