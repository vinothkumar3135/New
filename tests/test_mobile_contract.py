"""Test suite verifying Expo React Native Mobile App contract compatibility."""

import pytest
from starlette.testclient import TestClient

def test_locations_endpoint(client: TestClient):
    """Mobile app requires GET /api/locations returning [{ city: str, areas: str[] }]."""
    res = client.get("/api/locations")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "city" in first
    assert "areas" in first
    assert isinstance(first["areas"], list)

def test_businesses_list_mobile_format(client: TestClient):
    """Mobile app requires { items: Business[], total: number, pages: number }."""
    res = client.get("/api/businesses")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "pages" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["pages"], int)

    if data["items"]:
        item = data["items"][0]
        # Mobile specific fields
        assert "category_name" in item
        assert "area" in item
        assert "pincode" in item
        assert "image_color" in item
        assert "opening_hours" in item
        assert "whatsapp" in item
        assert "photos" in item
        assert isinstance(item["photos"], list)

def test_plans_endpoint(client: TestClient):
    """Mobile app requires GET /api/plans returning subscription tiers."""
    res = client.get("/api/plans")
    assert res.status_code == 200
    plans = res.json()
    assert isinstance(plans, list)
    assert any(p["id"] == "free" for p in plans)

def test_business_detail_dual_compatibility(client: TestClient):
    """
    Mobile expects { business: Business, reviews: Review[], similar: Business[] }.
    Web expects flat business fields at the root.
    Both must be satisfied on GET /api/businesses/{id}.
    """
    list_res = client.get("/api/businesses")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No businesses to test")
    biz_id = items[0]["id"]

    res = client.get(f"/api/businesses/{biz_id}")
    assert res.status_code == 200
    data = res.json()

    # Flat web fields
    assert data["id"] == biz_id
    assert "name" in data
    assert "rating" in data
    assert "city" in data

    # Nested mobile fields
    assert "business" in data
    assert data["business"]["id"] == biz_id
    assert "reviews" in data
    assert isinstance(data["reviews"], list)
    assert "similar" in data
    assert isinstance(data["similar"], list)

def test_track_event(client: TestClient):
    """Mobile app tracks view/call/whatsapp events."""
    list_res = client.get("/api/businesses")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No businesses to test")
    biz_id = items[0]["id"]

    res = client.post(f"/api/businesses/{biz_id}/events?kind=call")
    assert res.status_code == 200
    assert res.json() == {"tracked": "call"}

def test_review_eligibility(client: TestClient):
    """Mobile app checks review eligibility before presenting the review modal."""
    list_res = client.get("/api/businesses")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No businesses to test")
    biz_id = items[0]["id"]

    res = client.get(f"/api/businesses/{biz_id}/reviews/eligibility")
    assert res.status_code == 200
    data = res.json()
    assert "eligible" in data

def test_owner_mobile_endpoints(client: TestClient):
    """Verify all owner dashboard endpoints called by Mobile-App/app/owner/dashboard.tsx."""
    # Register an owner
    import uuid
    uid = str(uuid.uuid4())[:8]
    email = f"owner_{uid}@infoez.com"
    reg = client.post("/api/auth/register", json={
        "name": "Owner Mobile",
        "email": email,
        "password": "Password123!",
        "role": "business_owner",
    })
    assert reg.status_code == 200
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/owner/businesses
    res = client.get("/api/owner/businesses", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 2. GET /api/leads
    res = client.get("/api/leads", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 3. GET /api/owner/reviews
    res = client.get("/api/owner/reviews", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 4. GET /api/owner/analytics
    res = client.get("/api/owner/analytics", headers=headers)
    assert res.status_code == 200
    an = res.json()
    for field in ["views", "calls", "whatsapp", "directions", "website", "leads", "businesses", "average_rating"]:
        assert field in an

    # 5. GET /api/owner/analytics/trends
    res = client.get("/api/owner/analytics/trends", headers=headers)
    assert res.status_code == 200
    tr = res.json()
    assert "days" in tr
    assert isinstance(tr["days"], list)
    assert len(tr["days"]) == 7

    # 6. Favorites flow
    b_res = client.get("/api/businesses")
    b_items = b_res.json()["items"]
    if b_items:
        target_bid = b_items[0]["id"]
        # Save
        save_res = client.post(f"/api/favorites/{target_bid}", headers=headers)
        assert save_res.status_code == 200
        assert save_res.json().get("saved") is True

        # List
        favs = client.get("/api/favorites", headers=headers)
        assert favs.status_code == 200
        assert any(b["id"] == target_bid for b in favs.json())

        # Unsave
        unsave_res = client.delete(f"/api/favorites/{target_bid}", headers=headers)
        assert unsave_res.status_code == 200
        assert unsave_res.json().get("saved") is False

def test_admin_mobile_endpoints(client: TestClient):
    """Verify admin overview and moderation endpoints called by Mobile-App/app/admin.tsx."""
    login_res = client.post("/api/auth/login", json={
        "email": "admin@infoez.com",
        "password": "Admin@123",
    })
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/admin/overview
    res = client.get("/api/admin/overview", headers=headers)
    assert res.status_code == 200
    ov = res.json()
    for field in ["users", "businesses", "pending_businesses", "reviews", "enquiries", "pending_claims", "categories"]:
        assert field in ov

    # 2. GET /api/admin/businesses?status_filter=pending
    res = client.get("/api/admin/businesses?status_filter=pending", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 3. GET /api/admin/claims
    res = client.get("/api/admin/claims", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 4. GET /api/categories?include_inactive=true
    res = client.get("/api/categories?include_inactive=true")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
