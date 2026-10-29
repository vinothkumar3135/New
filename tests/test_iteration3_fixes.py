"""Iteration-3 verification: enquiry phone optional, 422 detail shape, seed review_count."""
import os
import pytest
import requests
from dotenv import dotenv_values

fe = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or fe.get("REACT_APP_BACKEND_URL")).rstrip("/")
BASE = f"{BASE_URL}/api"


def _login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, r.text[:300]
    return r.json()["access_token"] if "access_token" in r.json() else r.json()["token"]


@pytest.fixture(scope="module")
def bid():
    r = requests.get(f"{BASE}/businesses", params={"limit": 1}, timeout=30)
    assert r.status_code == 200
    return r.json()["items"][0]["id"]


@pytest.fixture(scope="module")
def customer_h():
    return {"Authorization": f"Bearer {_login('customer@infoez.com', 'Customer@123')}"}


# --- CRITICAL FIX: EnquiryIn.phone Optional ---
class TestEnquiryPhoneOptional:
    def test_no_phone_key_anonymous(self, bid):
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries",
                          json={"name": "TEST_QA3", "email": "test_qa3@example.com",
                                "message": "TEST_QA3 no phone key"}, timeout=30)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        d = r.json()
        assert d["name"] == "TEST_QA3"
        assert d["email"] == "test_qa3@example.com"
        assert d["message"] == "TEST_QA3 no phone key"
        assert d.get("phone") in (None, "")
        assert isinstance(d.get("id"), str) and d["id"]
        assert "_id" not in d

    def test_null_phone_logged_in_customer(self, bid, customer_h):
        # customer profile has no phone -> UI sends phone: null
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries", headers=customer_h,
                          json={"name": "TEST_QA3 Cust", "email": "customer@infoez.com",
                                "phone": None, "message": "TEST_QA3 null phone"}, timeout=30)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        assert r.json()["message"] == "TEST_QA3 null phone"

    def test_empty_string_phone(self, bid):
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries",
                          json={"name": "TEST_QA3 Empty", "email": "test_qa3@example.com",
                                "phone": "", "message": "TEST_QA3 empty phone"}, timeout=30)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"

    def test_enquiry_persists_for_customer(self, bid, customer_h):
        r = requests.get(f"{BASE}/enquiries/me", headers=customer_h, timeout=30)
        assert r.status_code == 200
        msgs = [e["message"] for e in r.json()]
        assert "TEST_QA3 null phone" in msgs

    def test_empty_name_returns_422_with_list_detail(self, bid):
        """apiError must normalise this shape - assert it is indeed a list of dicts."""
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries",
                          json={"name": "", "email": "test_qa3@example.com",
                                "message": "TEST_QA3 bad"}, timeout=30)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
        detail = r.json()["detail"]
        assert isinstance(detail, list) and isinstance(detail[0], dict)
        assert "msg" in detail[0]

    def test_empty_message_returns_422(self, bid):
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries",
                          json={"name": "TEST_QA3", "email": "test_qa3@example.com",
                                "message": ""}, timeout=30)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"


# --- MEDIUM FIX: seed review_count matches actual reviews ---
class TestReviewCount:
    def test_web_infoez_slug_review_count(self):
        r = requests.get(f"{BASE}/businesses", params={"limit": 100}, timeout=30)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 10
        mismatch = []
        for b in items:
            rev = requests.get(f"{BASE}/businesses/{b['id']}/reviews", timeout=30)
            assert rev.status_code == 200
            if len(rev.json()) != b["review_count"]:
                mismatch.append((b["name"], b["review_count"], len(rev.json())))
        assert not mismatch, f"review_count mismatch: {mismatch}"

    def test_detail_by_slug_matches(self):
        lst = requests.get(f"{BASE}/businesses", params={"limit": 1}, timeout=30).json()["items"][0]
        d = requests.get(f"{BASE}/businesses/{lst['slug']}", timeout=30)
        assert d.status_code == 200, d.text[:200]
        body = d.json()
        assert body["id"] == lst["id"]
        revs = requests.get(f"{BASE}/businesses/{body['id']}/reviews", timeout=30).json()
        assert body["review_count"] == len(revs)


# --- MEDIUM FIX: unknown slug -> 404 (frontend not-found state depends on it) ---
class TestUnknownSlug:
    def test_unknown_slug_404(self):
        r = requests.get(f"{BASE}/businesses/does-not-exist-xyz", timeout=30)
        assert r.status_code == 404, f"{r.status_code}: {r.text[:200]}"
        assert isinstance(r.json().get("detail"), str)
