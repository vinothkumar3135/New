"""Serialization and data normalization utilities to ensure consistent API responses."""

from typing import Any, Dict, List, Optional

def serialize_mongo_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Remove MongoDB internal `_id` field and ensure all keys are JSON-serializable."""
    if doc is None:
        return None
    return {k: v for k, v in doc.items() if k != "_id"}

def normalize_services(services: Any) -> List[str]:
    """Normalize services to guaranteed list of clean strings."""
    if services is None:
        return []
    if isinstance(services, str):
        return [s.strip() for s in services.split(",") if s.strip()]
    if isinstance(services, (list, tuple)):
        result = []
        for s in services:
            if s is not None and str(s).strip():
                result.append(str(s).strip())
        return result
    return []

def normalize_images(images: Any) -> List[str]:
    """Normalize images to guaranteed list of string URLs."""
    if images is None:
        return []
    if isinstance(images, str):
        return [images] if images.strip() else []
    if isinstance(images, (list, tuple)):
        return [str(img).strip() for img in images if img and str(img).strip()]
    return []

def normalize_business(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure every business document contains all required attributes with safe defaults.
    Guarantees no crashes in mobile or web frontends from `undefined` or unexpected types.
    """
    clean = serialize_mongo_doc(doc) or {}

    clean["id"] = str(clean.get("id") or "")
    clean["name"] = str(clean.get("name") or "")
    clean["slug"] = str(clean.get("slug") or "")
    clean["description"] = str(clean.get("description") or "")
    clean["category_id"] = str(clean.get("category_id") or "")
    clean["address"] = str(clean.get("address") or "")
    clean["city"] = str(clean.get("city") or "")
    clean["phone"] = str(clean.get("phone") or "")
    clean["email"] = str(clean.get("email") or "")
    clean["website"] = str(clean.get("website") or "")
    clean["price_range"] = str(clean.get("price_range") or "$$")
    clean["hours"] = str(clean.get("hours") or "")
    clean["services"] = normalize_services(clean.get("services"))
    clean["images"] = normalize_images(clean.get("images"))
    clean["rating"] = round(float(clean.get("rating") or 0.0), 1)
    clean["review_count"] = int(clean.get("review_count") or 0)
    clean["view_count"] = int(clean.get("view_count") or 0)
    clean["verified"] = bool(clean.get("verified", False))
    clean["featured"] = bool(clean.get("featured", False))
    clean["status"] = str(clean.get("status") or "active")
    clean["owner_id"] = str(clean.get("owner_id") or "")
    clean["created_at"] = str(clean.get("created_at") or "")

    # Mobile App Contract compatibility
    images = clean["images"]
    clean["photos"] = images
    clean["logo_url"] = clean.get("logo_url") or (images[0] if images else None)
    clean["image_color"] = str(clean.get("image_color") or "#104838")
    clean["opening_hours"] = str(clean.get("opening_hours") or clean["hours"] or "Mon-Sun 9:00 AM - 10:00 PM")
    clean["whatsapp"] = str(clean.get("whatsapp") or clean["phone"])
    clean["pincode"] = str(clean.get("pincode") or "560001")
    
    # Area parsing
    if clean.get("area"):
        clean["area"] = str(clean["area"])
    elif clean["address"]:
        clean["area"] = clean["address"].split(",")[0].strip()
    else:
        clean["area"] = clean["city"]

    # Category name
    if clean.get("category_name"):
        clean["category_name"] = str(clean["category_name"])
    elif clean.get("category") and isinstance(clean["category"], dict):
        clean["category_name"] = str(clean["category"].get("name") or "")
    else:
        clean["category_name"] = ""

    clean["products"] = clean.get("products") or []
    clean["amenities"] = clean.get("amenities") or ["Wi-Fi", "Card Accepted", "Air Conditioned"]

    # Coordinates
    lat = clean.get("lat")
    lng = clean.get("lng")
    clean["lat"] = float(lat) if lat is not None else None
    clean["lng"] = float(lng) if lng is not None else None

    # Optional fields
    if "distance_km" in clean and clean["distance_km"] is not None:
        clean["distance_km"] = round(float(clean["distance_km"]), 2)
    if "is_favorited" in clean:
        clean["is_favorited"] = bool(clean["is_favorited"])
    if "category" in clean and isinstance(clean["category"], dict):
        clean["category"] = serialize_mongo_doc(clean["category"])

    return clean

def normalize_user(doc: Dict[str, Any], include_sensitive: bool = False) -> Dict[str, Any]:
    """Normalize user document, safely omitting password by default."""
    clean = serialize_mongo_doc(doc) or {}
    result = {
        "id": str(clean.get("id") or ""),
        "name": str(clean.get("name") or ""),
        "email": str(clean.get("email") or "").lower(),
        "role": str(clean.get("role") or "customer"),
        "status": str(clean.get("status") or "active"),
        "phone": clean.get("phone"),
        "avatar": clean.get("avatar"),
        "created_at": clean.get("created_at"),
    }
    if include_sensitive and "password" in clean:
        result["password"] = clean["password"]
    return result
