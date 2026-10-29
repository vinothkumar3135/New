"""Datetime and ID utility functions."""
import uuid
from datetime import datetime, timezone, timedelta

def now_iso() -> str:
    """Return current UTC time formatted as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()

def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)

def new_id() -> str:
    """Generate a new UUIDv4 string."""
    return str(uuid.uuid4())
