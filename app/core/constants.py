"""Core constants for Infoez backend."""

from enum import Enum
from typing import List, Dict, Any

class UserRole(str, Enum):
    CUSTOMER = "customer"
    BUSINESS_OWNER = "business_owner"
    ADMIN = "admin"

class BusinessStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    REJECTED = "rejected"

class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class EnquiryStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"

# Pre-defined subscription plans
PLANS: List[Dict[str, Any]] = [
    {
        "id": "free",
        "name": "Free",
        "price": 0,
        "features": ["Basic listing", "Up to 5 photos", "Customer reviews"],
    },
    {
        "id": "starter",
        "name": "Starter",
        "price": 19,
        "features": [
            "Everything in Free",
            "Up to 20 photos",
            "Priority support",
            "Lead tracking",
        ],
    },
    {
        "id": "pro",
        "name": "Pro",
        "price": 49,
        "features": [
            "Everything in Starter",
            "Featured placement",
            "Verified badge fast-track",
            "Analytics dashboard",
        ],
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "price": 149,
        "features": [
            "Everything in Pro",
            "Multiple locations",
            "Dedicated success manager",
            "API access",
        ],
    },
]

# File upload configuration
ALLOWED_MIME_TYPES: Dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}

MAX_UPLOAD_BYTES: int = 8 * 1024 * 1024  # 8MB per file
