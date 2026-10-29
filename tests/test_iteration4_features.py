"""Iteration 4: photo uploads, admin approval workflow, nearby (map) search."""
import io
import os
import struct
import zlib

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "admin": ("admin@infoez.com", "Admin@123"),
    "owner": ("owner@infoez.com", "Owner@123"),
    "customer": ("customer@infoez.com", "Customer@123"),
}


def _png_bytes(w=8, h=8):
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


@pytest.fixture(scope="session")
def tokens():
    out = {}
    for role, (email, pwd) in CREDS.items():
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=30)
        if r.status_code != 200:
            pytest.fail(f"Login failed for {role}: {r.status_code} {r.text[:300]}")
        out[role] = r.json()["token"]
    return out


@pytest.fixture(scope="session")
def category_id():
    r = requests.get(f"{API}/categories", timeout=30)
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) > 0
    return cats[0]["id"]


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


created_biz = []


@pytest.fixture(scope="session", autouse=True)
def cleanup(tokens):
    yield
    for bid in created_biz:
        requests.delete(f"{API}/businesses/{bid}", headers=h(tokens["admin"]), timeout=30)


# ---------- Uploads ----------
class TestUploads:
    uploaded = {}

    def test_upload_requires_auth(self):
        r = requests.post(f"{API}/uploads", files={"file": ("a.png", _png_bytes(), "image/png")}, timeout=60)
        assert r.status_code in (401, 403), r.text[:300]

    def test_upload_png_success(self, tokens):
        img = _png_bytes(16, 16)
        r = requests.post(f"{API}/uploads", headers=h(tokens["owner"]),
                          files={"file": ("TEST_photo.png", img, "image/png")}, timeout=120)
        assert r.status_code == 200, r.text[:500]
        d = r.json()
        assert set(["path", "url", "size"]).issubset(d.keys())
        assert d["url"] == f"/api/files/{d['path']}"
        assert d["size"] == len(img)
        TestUploads.uploaded["png"] = d

    def test_upload_jpg_and_webp(self, tokens):
        for name, ct in [("TEST_a.jpg", "image/jpeg"), ("TEST_a.webp", "image/webp")]:
            r = requests.post(f"{API}/uploads", headers=h(tokens["owner"]),
                              files={"file": (name, _png_bytes(), ct)}, timeout=120)
            assert r.status_code == 200, f"{name}: {r.status_code} {r.text[:300]}"

    def test_upload_rejects_non_image(self, tokens):
        r = requests.post(f"{API}/uploads", headers=h(tokens["owner"]),
                          files={"file": ("evil.txt", b"hello world", "text/plain")}, timeout=60)
        assert r.status_code == 400, r.text[:300]

    def test_upload_rejects_oversize(self, tokens):
        big = b"\x89PNG\r\n\x1a\n" + os.urandom(9 * 1024 * 1024)
        r = requests.post(f"{API}/uploads", headers=h(tokens["owner"]),
                          files={"file": ("TEST_big.png", big, "image/png")}, timeout=180)
        assert r.status_code in (400, 413), f"expected reject, got {r.status_code}"

    def test_get_file_serves_image(self, tokens):
        d = TestUploads.uploaded.get("png")
        assert d, "upload test must run first"
        r = requests.get(f"{BASE_URL}{d['url']}", timeout=60)
        assert r.status_code == 200, r.text[:200]
        assert r.headers.get("content-type", "").startswith("image/png")
        # Note: preview ingress rewrites Cache-Control to no-store; backend sets max-age=86400.
        assert r.headers.get("cache-control") is not None
        assert len(r.content) == d["size"]

    def test_get_file_unknown_404(self):
        r = requests.get(f"{API}/files/infoez/uploads/nope/does-not-exist.png", timeout=60)
        assert r.status_code == 404


# ---------- Approval workflow ----------
class TestApprovalWorkflow:
    def _create(self, tok, name, cat, extra=None):
        payload = {"name": name, "description": "TEST listing for approval flow",
                   "category_id": cat, "address": "1 Test Rd", "city": "Bengaluru",
                   "phone": "9999900000", "services": ["testing"]}
        if extra:
            payload.update(extra)
        r = requests.post(f"{API}/businesses", headers=h(tok), json=payload, timeout=60)
        assert r.status_code in (200, 201), r.text[:400]
        b = r.json()
        created_biz.append(b["id"])
        return b

    def test_owner_create_is_pending(self, tokens, category_id):
        b = self._create(tokens["owner"], "TEST_Owner Pending Co", category_id)
        assert b["status"] == "pending"
        assert b.get("verified") is False

    def test_admin_create_is_active(self, tokens, category_id):
        b = self._create(tokens["admin"], "TEST_Admin Auto Active Co", category_id)
        assert b["status"] == "active"

    def test_customer_cannot_create(self, tokens, category_id):
        r = requests.post(f"{API}/businesses", headers=h(tokens["customer"]),
                          json={"name": "TEST_Cust", "description": "x", "category_id": category_id,
                                "address": "a", "city": "b", "phone": "1"}, timeout=30)
        assert r.status_code == 403

    def test_pending_hidden_from_public_list(self, tokens, category_id):
        b = self._create(tokens["owner"], "TEST_Hidden Pending Co", category_id)
        r = requests.get(f"{API}/businesses", params={"q": "TEST_Hidden Pending Co"}, timeout=30)
        assert r.status_code == 200
        assert all(x["id"] != b["id"] for x in r.json()["items"]), "pending listing leaked publicly"
        # include_pending without admin token must still hide it
        r2 = requests.get(f"{API}/businesses", params={"q": "TEST_Hidden Pending Co", "include_pending": True},
                          timeout=30)
        assert all(x["id"] != b["id"] for x in r2.json()["items"]), "pending leaked via include_pending anon"
        r3 = requests.get(f"{API}/businesses", params={"q": "TEST_Hidden Pending Co", "include_pending": True},
                          headers=h(tokens["customer"]), timeout=30)
        assert all(x["id"] != b["id"] for x in r3.json()["items"]), "pending leaked to customer"
        # admin can see it
        r4 = requests.get(f"{API}/businesses", params={"q": "TEST_Hidden Pending Co", "include_pending": True},
                          headers=h(tokens["admin"]), timeout=30)
        assert any(x["id"] == b["id"] for x in r4.json()["items"]), "admin cannot see pending"

    def test_admin_pending_list_and_permissions(self, tokens, category_id):
        b = self._create(tokens["owner"], "TEST_Queue Co", category_id)
        r = requests.get(f"{API}/admin/pending-businesses", headers=h(tokens["admin"]), timeout=30)
        assert r.status_code == 200
        items = r.json()
        match = [x for x in items if x["id"] == b["id"]]
        assert match, "new pending listing missing from admin queue"
        assert all(x["status"] == "pending" for x in items)
        assert match[0].get("owner") and match[0]["owner"].get("email") == CREDS["owner"][0]
        for role in ("owner", "customer"):
            rr = requests.get(f"{API}/admin/pending-businesses", headers=h(tokens[role]), timeout=30)
            assert rr.status_code == 403, f"{role} accessed admin queue"
        assert requests.get(f"{API}/admin/pending-businesses", timeout=30).status_code in (401, 403)

    def test_admin_notified_on_new_pending(self, tokens, category_id):
        b = self._create(tokens["owner"], "TEST_Notify Admin Co", category_id)
        r = requests.get(f"{API}/notifications/me", headers=h(tokens["admin"]), timeout=30)
        assert r.status_code == 200
        notes = r.json()
        assert any(n["title"] == "New listing pending review" and b["name"] in n["body"] for n in notes), \
            "admin not notified of new pending listing"

    def test_approve_flow(self, tokens, category_id):
        b = self._create(tokens["owner"], "TEST_Approve Me Co", category_id)
        r = requests.post(f"{API}/businesses/{b['id']}/approve", headers=h(tokens["admin"]), timeout=30)
        assert r.status_code == 200, r.text[:300]
        g = requests.get(f"{API}/businesses/{b['id']}", timeout=30)
        assert g.status_code == 200 and g.json()["status"] == "active"
        pub = requests.get(f"{API}/businesses", params={"q": b["name"]}, timeout=30)
        assert any(x["id"] == b["id"] for x in pub.json()["items"]), "approved listing not public"
        notes = requests.get(f"{API}/notifications/me", headers=h(tokens["owner"]), timeout=30).json()
        assert any(n["title"] == "Listing Approved" and b["name"] in n["body"] for n in notes)
        q = requests.get(f"{API}/admin/pending-businesses", headers=h(tokens["admin"]), timeout=30).json()
        assert all(x["id"] != b["id"] for x in q)

    def test_reject_flow(self, tokens, category_id):
        b = self._create(tokens["owner"], "TEST_Reject Me Co", category_id)
        reason = "TEST_incomplete details"
        r = requests.post(f"{API}/businesses/{b['id']}/reject", params={"reason": reason},
                          headers=h(tokens["admin"]), timeout=30)
        assert r.status_code == 200, r.text[:300]
        g = requests.get(f"{API}/businesses/{b['id']}", timeout=30)
        assert g.json()["status"] == "rejected"
        pub = requests.get(f"{API}/businesses", params={"q": b["name"]}, timeout=30)
        assert all(x["id"] != b["id"] for x in pub.json()["items"]), "rejected listing is public"
        notes = requests.get(f"{API}/notifications/me", headers=h(tokens["owner"]), timeout=30).json()
        assert any("reject" in n["title"].lower() and reason in n["body"] for n in notes)

    def test_approve_permissions_and_404(self, tokens, category_id):
        b = self._create(tokens["owner"], "TEST_Perm Co", category_id)
        for role in ("owner", "customer"):
            rr = requests.post(f"{API}/businesses/{b['id']}/approve", headers=h(tokens[role]), timeout=30)
            assert rr.status_code == 403, f"{role} could approve"
        r404 = requests.post(f"{API}/businesses/does-not-exist/approve", headers=h(tokens["admin"]), timeout=30)
        assert r404.status_code == 404


# ---------- Nearby / map search ----------
class TestNearbySearch:
    LAT, LNG = 12.9749, 77.6069

    def test_nearby_sorted_and_has_distance(self):
        r = requests.get(f"{API}/businesses", params={"near_lat": self.LAT, "near_lng": self.LNG,
                                                     "radius_km": 50, "limit": 50}, timeout=30)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) > 0, "no nearby results for seeded data"
        d = [x["distance_km"] for x in items]
        assert all(isinstance(x, (int, float)) for x in d)
        assert d == sorted(d), f"not sorted ascending: {d}"
        assert all(x <= 50 for x in d)

    def test_radius_excludes_far(self):
        small = requests.get(f"{API}/businesses", params={"near_lat": self.LAT, "near_lng": self.LNG,
                                                          "radius_km": 1, "limit": 50}, timeout=30).json()
        big = requests.get(f"{API}/businesses", params={"near_lat": self.LAT, "near_lng": self.LNG,
                                                        "radius_km": 100, "limit": 50}, timeout=30).json()
        assert small["total"] <= big["total"]
        assert all(x["distance_km"] <= 1 for x in small["items"])

    def test_excludes_without_coords(self, tokens, category_id):
        payload = {"name": "TEST_NoCoords Co", "description": "no coords", "category_id": category_id,
                   "address": "x", "city": "Bengaluru", "phone": "1"}
        b = requests.post(f"{API}/businesses", headers=h(tokens["admin"]), json=payload, timeout=30).json()
        created_biz.append(b["id"])
        assert b["status"] == "active"
        items = requests.get(f"{API}/businesses", params={"near_lat": self.LAT, "near_lng": self.LNG,
                                                          "radius_km": 20000, "limit": 200}, timeout=30).json()["items"]
        assert all(x["id"] != b["id"] for x in items), "business without lat/lng included in nearby"

    def test_nearby_excludes_pending(self, tokens, category_id):
        payload = {"name": "TEST_Pending Nearby Co", "description": "pending near", "category_id": category_id,
                   "address": "x", "city": "Bengaluru", "phone": "1", "lat": self.LAT, "lng": self.LNG}
        b = requests.post(f"{API}/businesses", headers=h(tokens["owner"]), json=payload, timeout=30).json()
        created_biz.append(b["id"])
        items = requests.get(f"{API}/businesses", params={"near_lat": self.LAT, "near_lng": self.LNG,
                                                          "radius_km": 50, "limit": 200}, timeout=30).json()["items"]
        assert all(x["id"] != b["id"] for x in items), "pending listing shown in nearby results"

    def test_nearby_with_category_filter(self, category_id):
        items = requests.get(f"{API}/businesses", params={"near_lat": self.LAT, "near_lng": self.LNG,
                                                          "radius_km": 200, "category_id": category_id,
                                                          "limit": 50}, timeout=30).json()["items"]
        assert all(x["category_id"] == category_id for x in items)


# ---------- lat/lng model + regression ----------
class TestLatLngAndRegression:
    def test_create_and_update_latlng(self, tokens, category_id):
        payload = {"name": "TEST_LatLng Co", "description": "coords", "category_id": category_id,
                   "address": "x", "city": "Bengaluru", "phone": "1", "lat": 12.9, "lng": 77.5}
        b = requests.post(f"{API}/businesses", headers=h(tokens["admin"]), json=payload, timeout=30).json()
        created_biz.append(b["id"])
        assert b["lat"] == 12.9 and b["lng"] == 77.5
        u = requests.put(f"{API}/businesses/{b['id']}", headers=h(tokens["admin"]),
                         json={"lat": 13.05, "lng": 77.62}, timeout=30)
        assert u.status_code == 200, u.text[:300]
        assert u.json()["lat"] == 13.05 and u.json()["lng"] == 77.62
        g = requests.get(f"{API}/businesses/{b['id']}", timeout=30).json()
        assert g["lat"] == 13.05 and g["lng"] == 77.62
        assert "_id" not in g

    def test_create_without_latlng_works(self, tokens, category_id):
        payload = {"name": "TEST_Plain Co", "description": "plain", "category_id": category_id,
                   "address": "x", "city": "Bengaluru", "phone": "1"}
        r = requests.post(f"{API}/businesses", headers=h(tokens["owner"]), json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text[:300]
        b = r.json()
        created_biz.append(b["id"])
        assert b.get("lat") is None and b.get("lng") is None

    def test_seeded_businesses_have_coords(self):
        items = requests.get(f"{API}/businesses", params={"limit": 50}, timeout=30).json()["items"]
        seeded = [x for x in items if not x["name"].startswith("TEST_")
                  and "Test" not in x["name"]]  # skip leftover manual-curl fixtures
        missing = [x["name"] for x in seeded if x.get("lat") is None or x.get("lng") is None]
        assert not missing, f"seeded businesses missing coords: {missing}"

    def test_owner_mine_includes_pending(self, tokens, category_id):
        payload = {"name": "TEST_Mine Pending Co", "description": "mine", "category_id": category_id,
                   "address": "x", "city": "Bengaluru", "phone": "1"}
        b = requests.post(f"{API}/businesses", headers=h(tokens["owner"]), json=payload, timeout=30).json()
        created_biz.append(b["id"])
        mine = requests.get(f"{API}/businesses/owner/me", headers=h(tokens["owner"]), timeout=30)
        assert mine.status_code == 200
        m = [x for x in mine.json() if x["id"] == b["id"]]
        assert m and m[0]["status"] == "pending"

    def test_categories_business_count_excludes_pending(self, tokens, category_id):
        """business_count must not count pending/rejected listings (public visibility parity)."""
        before = [c for c in requests.get(f"{API}/categories", timeout=30).json()
                  if c["id"] == category_id][0]["business_count"]
        payload = {"name": "TEST_Count Pending Co", "description": "cnt", "category_id": category_id,
                   "address": "x", "city": "Bengaluru", "phone": "1"}
        b = requests.post(f"{API}/businesses", headers=h(tokens["owner"]), json=payload, timeout=30).json()
        created_biz.append(b["id"])
        after = [c for c in requests.get(f"{API}/categories", timeout=30).json()
                 if c["id"] == category_id][0]["business_count"]
        assert after == before, (
            f"business_count incremented to {after} for a PENDING listing (was {before})")

    def test_categories_business_count(self):
        r = requests.get(f"{API}/categories", timeout=30)
        assert r.status_code == 200
        cats = r.json()
        for c in cats:
            assert isinstance(c["business_count"], int)
            assert "_id" not in c
            listed = requests.get(f"{API}/businesses", params={"category_id": c["id"], "limit": 100},
                                  timeout=30).json()["total"]
            assert c["business_count"] == listed, \
                f"category '{c['name']}' business_count={c['business_count']} but public list total={listed}"

    def test_health(self):
        r = requests.get(f"{API}/", timeout=30)
        assert r.status_code == 200 and r.json().get("status") == "ok"
