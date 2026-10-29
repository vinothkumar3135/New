"""Enquiry / Lead Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class EnquiryIn(BaseModel):
    name: Optional[str] = None
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    requirement: Optional[str] = None
    message: Optional[str] = None

class EnquiryResponse(BaseModel):
    id: str
    business_id: str
    business_name: str = ""
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    name: str = ""
    customer_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    requirement: str = ""
    message: str = ""
    notes: str = ""
    status: str = "new"
    created_at: Optional[str] = None
    ok: bool = True
