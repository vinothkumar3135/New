"""Slug utility functions."""
import re

def slugify(text: str) -> str:
    """Convert arbitrary text into a URL-friendly slug."""
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:80]
