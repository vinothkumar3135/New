"""Notification Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    body: str = ""
    message: str = ""
    type: str = ""
    kind: str = ""
    read: bool = False
    created_at: Optional[str] = None
