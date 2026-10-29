"""Review Pydantic schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str

class ReviewResponse(BaseModel):
    id: str
    business_id: str
    user_id: str
    rating: int
    comment: str
    created_at: Optional[str] = None
    customer_name: str = "Customer"
    helpful_count: int = 0
    owner_reply: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    business: Optional[Dict[str, Any]] = None
