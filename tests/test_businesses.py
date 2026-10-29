"""Business schema normalization and distance calculation unit tests."""

from app.utils.response import normalize_business, normalize_services, normalize_images
from app.utils.distance import haversine_distance
from app.utils.slug import slugify

def test_slugify():
    assert slugify("Sundara Coffee Roasters") == "sundara-coffee-roasters"
    assert slugify("Cafe & Bistro 100%!") == "cafe-bistro-100"
    assert slugify("   Leading Spaces   ") == "leading-spaces"

def test_haversine_distance():
    # Bengaluru (12.9716, 77.5946) to Chennai (13.0827, 80.2707) is approx 290 km
    dist = haversine_distance(12.9716, 77.5946, 13.0827, 80.2707)
    assert 280 < dist < 300

def test_normalize_services_fixes_legacy_data():
    # String comma separated
    assert normalize_services("Plumbing, Electrical, Painting") == ["Plumbing", "Electrical", "Painting"]
    # None or missing
    assert normalize_services(None) == []
    # Empty string
    assert normalize_services("") == []
    # Clean list
    assert normalize_services(["AC Repair", "Cleaning"]) == ["AC Repair", "Cleaning"]
    # Dirty list with empty elements
    assert normalize_services(["AC Repair", "", None, "  "]) == ["AC Repair"]

def test_normalize_images_fixes_legacy_data():
    assert normalize_images(None) == []
    assert normalize_images("") == []
    assert normalize_images("http://example.com/img.jpg") == ["http://example.com/img.jpg"]
    assert normalize_images(["http://example.com/img.jpg", ""]) == ["http://example.com/img.jpg"]

def test_normalize_business_prevents_undefined_errors():
    # Incomplete legacy MongoDB document
    legacy_doc = {
        "_id": "65e000000000000000000001",
        "id": "biz-123",
        "name": "Legacy Shop",
        "services": "Repairs, Maintenance",
        "images": None,
        "hours": None,
        "address": None,
        "phone": None,
    }
    normalized = normalize_business(legacy_doc)

    # Must NOT contain internal _id
    assert "_id" not in normalized

    # Critical contract guarantees to prevent frontend runtime crashes
    assert isinstance(normalized["services"], list)
    assert normalized["services"] == ["Repairs", "Maintenance"]

    assert isinstance(normalized["images"], list)
    assert normalized["images"] == []

    assert isinstance(normalized["hours"], str)
    assert normalized["hours"] == ""

    assert isinstance(normalized["phone"], str)
    assert normalized["phone"] == ""

    assert isinstance(normalized["rating"], float)
    assert normalized["rating"] == 0.0

    assert isinstance(normalized["review_count"], int)
    assert normalized["review_count"] == 0

    assert isinstance(normalized["verified"], bool)
    assert normalized["verified"] is False
