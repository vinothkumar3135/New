"""Category Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel

class CategoryIn(BaseModel):
    name: str
    icon: Optional[str] = "Store"
    color: Optional[str] = "#D97706"
    description: Optional[str] = ""

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    icon: Optional[str] = "Store"
    color: Optional[str] = "#D97706"
    description: Optional[str] = ""
    is_active: bool = True
    sort_order: int = 1
    business_count: Optional[int] = 0
    created_at: Optional[str] = None
