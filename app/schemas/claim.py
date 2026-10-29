"""Business ownership claim Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr

class ClaimIn(BaseModel):
    reason: Optional[str] = None
    verification_details: Optional[str] = None
    proof_url: Optional[str] = None

class ClaimResponse(BaseModel):
    id: str
    business_id: str
    business_name: str = ""
    user_id: str = ""
    owner_id: str = ""
    user_name: str = ""
    user_email: Optional[EmailStr] = None
    reason: str = ""
    verification_details: str = ""
    proof_url: Optional[str] = None
    status: str = "pending"
    created_at: Optional[str] = None
    message: str = "Claim submitted successfully"
