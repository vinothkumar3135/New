"""Iteration-2 regression tests: 404 on unknown business ids (verify/feature/delete),
regex escaping in search filters, and seeded rating/review_count coherence."""
import os
import re
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE = base_url.rstrip("/") + "/api"

CREDS_PATH = Path("/app/memory/test_credentials.md")


def _creds():
    text = CREDS_PATH.read_text()
    emails = re.findall(r"Email:\s*`([^`]+)`", text)
    pws = re.findall(r"Password:\s*`([^`]+)`", text)
    roles = re.findall(r"Role:\s*`([^`]+)`", text)
    return {r: (e, p) for r, e, p in zip(roles, emails, pws)}


CREDS = _creds()


def login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"Login failed for {email}: {r.status_code} {r.text[:300]}")
    return r.json()


@pytest.fixture(scope="module")
def admin_h():
    e, p = CREDS["admin"]
    return {"Authorization": f"Bearer {login(e, p)['token']}"}


UNKNOWN = f"nope-{uuid.uuid4()}"


# --- 404 handling on unknown business ids ---
class TestUnknownBusinessIds:
    def test_verify_unknown_returns_404(self, admin_h):
        r = requests.post(f"{BASE}/businesses/{UNKNOWN}/verify", headers=admin_h, timeout=30)
        assert r.status_code == 404, f"got {r.status_code}: {r.text[:200]}"
        assert "not found" in r.text.lower()

    def test_feature_unknown_returns_404(self, admin_h):
        r = requests.post(f"{BASE}/businesses/{UNKNOWN}/feature", headers=admin_h, timeout=30)
        assert r.status_code == 404, f"got {r.status_code}: {r.text[:200]}"

    def test_delete_unknown_returns_404(self, admin_h):
        r = requests.delete(f"{BASE}/businesses/{UNKNOWN}", headers=admin_h, timeout=30)
        assert r.status_code == 404, f"got {r.status_code}: {r.text[:200]}"

    def test_update_unknown_returns_404(self, admin_h):
        r = requests.put(f"{BASE}/businesses/{UNKNOWN}", headers=admin_h, json={"name": "x"}, timeout=30)
        assert r.status_code == 404, f"got {r.status_code}: {r.text[:200]}"


# --- regex escaping in list_businesses filters ---
class TestRegexEscaping:
    @pytest.mark.parametrize("q", ["(", ")", "[", "*", "+", "a(b", "\\"])
    def test_q_special_chars_no_500(self, q):
        r = requests.get(f"{BASE}/businesses", params={"q": q}, timeout=30)
        assert r.status_code == 200, f"q={q!r} -> {r.status_code}: {r.text[:200]}"
        body = r.json()
        assert isinstance(body.get("items"), list)
        assert body["items"] == [], f"q={q!r} unexpectedly matched {len(body['items'])} items"

    @pytest.mark.parametrize("city", ["(", "[a-", "*"])
    def test_city_special_chars_no_500(self, city):
        r = requests.get(f"{BASE}/businesses", params={"city": city}, timeout=30)
        assert r.status_code == 200, f"city={city!r} -> {r.status_code}: {r.text[:200]}"
        assert r.json()["items"] == []

    def test_normal_query_still_matches(self):
        r = requests.get(f"{BASE}/businesses", params={"q": "a"}, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json()["items"], list)


# --- seeded ratings coherence ---
class TestSeedRatingCoherence:
    def test_every_business_with_rating_has_reviews(self):
        r = requests.get(f"{BASE}/businesses", params={"limit": 100}, timeout=30)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 10
        bad = [(b["name"], b.get("rating"), b.get("review_count")) for b in items
               if (b.get("rating") or 0) > 0 and (b.get("review_count") or 0) == 0]
        assert not bad, f"businesses with rating but zero reviews: {bad}"

    def test_review_count_matches_actual_reviews(self):
        r = requests.get(f"{BASE}/businesses", params={"limit": 5}, timeout=30)
        for b in r.json()["items"]:
            rev = requests.get(f"{BASE}/businesses/{b['id']}/reviews", timeout=30)
            assert rev.status_code == 200
            reviews = rev.json()
            assert len(reviews) == b["review_count"], (
                f"{b['name']}: review_count={b['review_count']} but {len(reviews)} reviews returned")
            if reviews:
                avg = round(sum(x["rating"] for x in reviews) / len(reviews), 1)
                assert abs(avg - b["rating"]) <= 0.15, (
                    f"{b['name']}: stored rating {b['rating']} vs computed {avg}")


# --- enquiry payload validation (bug: phone is required & non-nullable) ---
class TestEnquiryPhoneOptional:
    @pytest.fixture(scope="class")
    def bid(self):
        r = requests.get(f"{BASE}/businesses", params={"limit": 1}, timeout=30)
        return r.json()["items"][0]["id"]

    def test_enquiry_accepts_null_phone(self, bid):
        """UI prefills phone from user profile; users without a phone send null -> 422."""
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries",
                          json={"name": "TEST QA", "email": "TESTqa@example.com",
                                "phone": None, "message": "TEST QA phone null"}, timeout=30)
        assert r.status_code in (200, 201), f"null phone rejected: {r.status_code} {r.text[:300]}"

    def test_enquiry_accepts_missing_phone(self, bid):
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries",
                          json={"name": "TEST QA", "email": "TESTqa@example.com",
                                "message": "TEST QA phone missing"}, timeout=30)
        assert r.status_code in (200, 201), f"missing phone rejected: {r.status_code} {r.text[:300]}"
