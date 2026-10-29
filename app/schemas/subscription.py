"""Subscription Pydantic schemas."""

from typing import List, Optional
from pydantic import BaseModel

class SubscribeIn(BaseModel):
    plan_id: str

class PlanResponse(BaseModel):
    id: str
    name: str
    price: float
    features: List[str]

class SubscriptionResponse(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    plan_id: str = "free"
    plan_name: Optional[str] = "Free"
    status: str = "active"
    started_at: Optional[str] = None
    renews_at: Optional[str] = None
    payment_method: Optional[str] = "free"
    payment_reference: Optional[str] = None
