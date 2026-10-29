"""Infoez backend API tests (health, auth, categories, businesses, reviews,
favorites, enquiries, notifications, claims, admin, subscriptions, role protection)."""
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
    body = r.json()
    assert body.get("token")
    return body


@pytest.fixture(scope="session")
def admin():
    e, p = CREDS["admin"]
    return login(e, p)


@pytest.fixture(scope="session")
def owner():
    e, p = CREDS["business_owner"]
    return login(e, p)


@pytest.fixture(scope="session")
def customer():
    e, p = CREDS["customer"]
    return login(e, p)


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


# --- Health / seed ---
class TestHealth:
    def test_root(self):
        r = requests.get(f"{BASE}/", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_seed_idempotent(self):
        r = requests.post(f"{BASE}/seed", timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        if d.get("already_seeded"):
            assert d["categories"] == 10
            assert d["businesses"] >= 12
            assert d["users"] >= 3


# --- Auth ---
class TestAuth:
    def test_register_customer(self):
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{BASE}/auth/register", json={
            "name": "TEST User", "email": email, "password": "Passw0rd!", "role": "customer"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["user"]["email"] == email
        assert d["user"]["role"] == "customer"
        assert "password" not in d["user"]
        me = requests.get(f"{BASE}/auth/me", headers=h(d["token"]), timeout=30)
        assert me.status_code == 200
        assert me.json()["email"] == email

    def test_register_duplicate(self):
        e, p = CREDS["admin"]
        r = requests.post(f"{BASE}/auth/register", json={
            "name": "dup", "email": e, "password": p}, timeout=30)
        assert r.status_code == 400

    def test_login_roles(self, admin, owner, customer):
        assert admin["user"]["role"] == "admin"
        assert owner["user"]["role"] == "business_owner"
        assert customer["user"]["role"] == "customer"

    def test_login_bad_password(self):
        e, _ = CREDS["admin"]
        r = requests.post(f"{BASE}/auth/login", json={"email": e, "password": "wrong"}, timeout=30)
        assert r.status_code == 401

    def test_me_unauthenticated(self):
        assert requests.get(f"{BASE}/auth/me", timeout=30).status_code in (401, 403)

    def test_patch_me(self, customer):
        r = requests.patch(f"{BASE}/auth/me", headers=h(customer["token"]),
                           json={"phone": "+91 99999 00000"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["phone"] == "+91 99999 00000"
        g = requests.get(f"{BASE}/auth/me", headers=h(customer["token"]), timeout=30)
        assert g.json()["phone"] == "+91 99999 00000"


# --- Categories ---
class TestCategories:
    def test_list(self):
        r = requests.get(f"{BASE}/categories", timeout=30)
        assert r.status_code == 200
        cats = r.json()
        assert len(cats) == 10
        assert all("business_count" in c and isinstance(c["business_count"], int) for c in cats)
        assert sum(c["business_count"] for c in cats) >= 12
        assert all("_id" not in c for c in cats)

    def test_create_delete_admin(self, admin):
        r = requests.post(f"{BASE}/categories", headers=h(admin["token"]),
                          json={"name": "TEST Category"}, timeout=30)
        assert r.status_code == 200, r.text
        cid = r.json()["id"]
        assert r.json()["slug"] == "test-category"
        names = [c["name"] for c in requests.get(f"{BASE}/categories", timeout=30).json()]
        assert "TEST Category" in names
        d = requests.delete(f"{BASE}/categories/{cid}", headers=h(admin["token"]), timeout=30)
        assert d.status_code == 200
        names = [c["name"] for c in requests.get(f"{BASE}/categories", timeout=30).json()]
        assert "TEST Category" not in names

    def test_create_non_admin_forbidden(self, customer):
        r = requests.post(f"{BASE}/categories", headers=h(customer["token"]),
                          json={"name": "TEST Nope"}, timeout=30)
        assert r.status_code == 403


# --- Businesses listing/filters ---
class TestBusinesses:
    def test_list_default(self):
        r = requests.get(f"{BASE}/businesses", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["total"] >= 12
        assert len(d["items"]) >= 12
        assert all("_id" not in b for b in d["items"])

    def test_filters(self):
        cats = requests.get(f"{BASE}/categories", timeout=30).json()
        cat = next(c for c in cats if c["business_count"] > 0)
        r = requests.get(f"{BASE}/businesses", params={"category_id": cat["id"]}, timeout=30).json()
        assert r["total"] == cat["business_count"]
        assert all(b["category_id"] == cat["id"] for b in r["items"])

        r = requests.get(f"{BASE}/businesses", params={"q": "biryani"}, timeout=30).json()
        assert r["total"] >= 1
        assert any("biryani" in b["name"].lower() for b in r["items"])

        r = requests.get(f"{BASE}/businesses", params={"city": "bengaluru"}, timeout=30).json()
        assert r["total"] >= 1
        assert all(b["city"].lower() == "bengaluru" for b in r["items"])

        r = requests.get(f"{BASE}/businesses", params={"min_rating": 4.7}, timeout=30).json()
        assert all(b["rating"] >= 4.7 for b in r["items"])

        r = requests.get(f"{BASE}/businesses", params={"verified": "true"}, timeout=30).json()
        assert all(b["verified"] is True for b in r["items"])

        r = requests.get(f"{BASE}/businesses", params={"featured": "true"}, timeout=30).json()
        assert r["total"] >= 1
        assert all(b["featured"] is True for b in r["items"])

        r = requests.get(f"{BASE}/businesses", params={"sort": "rating", "limit": 5}, timeout=30).json()
        ratings = [b["rating"] for b in r["items"]]
        assert len(ratings) == 5
        assert ratings == sorted(ratings, reverse=True)

        r = requests.get(f"{BASE}/businesses", params={"sort": "popular", "limit": 5}, timeout=30).json()
        views = [b["view_count"] for b in r["items"]]
        assert views == sorted(views, reverse=True)

    def test_get_by_slug_and_id(self):
        first = requests.get(f"{BASE}/businesses", timeout=30).json()["items"][0]
        r = requests.get(f"{BASE}/businesses/{first['slug']}", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == first["id"]
        assert d["is_favorited"] is False
        assert d.get("category") and d["category"]["id"] == first["category_id"]
        r2 = requests.get(f"{BASE}/businesses/{first['id']}", timeout=30)
        assert r2.status_code == 200 and r2.json()["id"] == first["id"]

    def test_get_missing(self):
        assert requests.get(f"{BASE}/businesses/no-such-slug-xyz", timeout=30).status_code == 404

    def test_view_count_increments(self):
        first = requests.get(f"{BASE}/businesses", timeout=30).json()["items"][0]
        a = requests.get(f"{BASE}/businesses/{first['slug']}", timeout=30).json()["view_count"]
        b = requests.get(f"{BASE}/businesses/{first['slug']}", timeout=30).json()["view_count"]
        assert b == a + 1


# --- Owner business CRUD ---
class TestOwnerBusiness:
    created = []

    def test_owner_list(self, owner):
        r = requests.get(f"{BASE}/businesses/owner/me", headers=h(owner["token"]), timeout=30)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 1
        assert all(b["owner_id"] == owner["user"]["id"] for b in items)

    def test_customer_cannot_list_owner(self, customer):
        r = requests.get(f"{BASE}/businesses/owner/me", headers=h(customer["token"]), timeout=30)
        assert r.status_code == 403

    def test_create_update_business(self, owner, admin):
        cat = requests.get(f"{BASE}/categories", timeout=30).json()[0]
        payload = {"name": "TEST Owner Biz", "description": "TEST desc", "category_id": cat["id"],
                   "address": "1 Test Rd", "city": "Testville", "phone": "+91 90000 12345",
                   "services": ["A", "B"], "images": []}
        r = requests.post(f"{BASE}/businesses", headers=h(owner["token"]), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        biz = r.json()
        TestOwnerBusiness.created.append(biz["id"])
        assert biz["owner_id"] == owner["user"]["id"]
        assert biz["slug"].startswith("test-owner-biz")
        assert biz["verified"] is False and biz["rating"] == 0.0

        g = requests.get(f"{BASE}/businesses/{biz['slug']}", timeout=30)
        assert g.status_code == 200 and g.json()["name"] == "TEST Owner Biz"

        u = requests.put(f"{BASE}/businesses/{biz['id']}", headers=h(owner["token"]),
                         json={"description": "TEST updated"}, timeout=30)
        assert u.status_code == 200
        assert u.json()["description"] == "TEST updated"
        assert requests.get(f"{BASE}/businesses/{biz['id']}", timeout=30).json()["description"] == "TEST updated"

    def test_customer_cannot_create(self, customer):
        cat = requests.get(f"{BASE}/categories", timeout=30).json()[0]
        r = requests.post(f"{BASE}/businesses", headers=h(customer["token"]), json={
            "name": "TEST No", "description": "x", "category_id": cat["id"],
            "address": "a", "city": "c", "phone": "1"}, timeout=30)
        assert r.status_code == 403

    def test_non_owner_cannot_update(self, customer):
        bid = TestOwnerBusiness.created[0] if TestOwnerBusiness.created else None
        if not bid:
            pytest.skip("no created business")
        r = requests.put(f"{BASE}/businesses/{bid}", headers=h(customer["token"]),
                         json={"name": "hack"}, timeout=30)
        assert r.status_code == 403

    def test_verify_and_feature(self, admin):
        bid = TestOwnerBusiness.created[0]
        r = requests.post(f"{BASE}/businesses/{bid}/verify", headers=h(admin["token"]), timeout=30)
        assert r.status_code == 200 and r.json()["verified"] is True
        before = requests.get(f"{BASE}/businesses/{bid}", timeout=30).json()["featured"]
        r = requests.post(f"{BASE}/businesses/{bid}/feature", headers=h(admin["token"]), timeout=30)
        assert r.status_code == 200 and r.json()["featured"] is (not before)

    def test_non_admin_cannot_verify(self, owner):
        bid = TestOwnerBusiness.created[0]
        r = requests.post(f"{BASE}/businesses/{bid}/verify", headers=h(owner["token"]), timeout=30)
        assert r.status_code == 403

    def test_zz_delete_created(self, admin):
        for bid in TestOwnerBusiness.created:
            d = requests.delete(f"{BASE}/businesses/{bid}", headers=h(admin["token"]), timeout=30)
            assert d.status_code == 200
            assert requests.get(f"{BASE}/businesses/{bid}", timeout=30).status_code == 404


# --- Favorites ---
class TestFavorites:
    def test_favorite_flow(self, customer):
        biz = requests.get(f"{BASE}/businesses", timeout=30).json()["items"][0]
        tok = customer["token"]
        r = requests.post(f"{BASE}/favorites/{biz['id']}", headers=h(tok), timeout=30)
        assert r.status_code == 200 and r.json()["favorited"] is True
        favs = requests.get(f"{BASE}/favorites/me", headers=h(tok), timeout=30)
        assert favs.status_code == 200
        assert biz["id"] in [b["id"] for b in favs.json()]
        detail = requests.get(f"{BASE}/businesses/{biz['slug']}", headers=h(tok), timeout=30).json()
        assert detail["is_favorited"] is True
        # idempotent
        assert requests.post(f"{BASE}/favorites/{biz['id']}", headers=h(tok), timeout=30).status_code == 200
        assert len([b for b in requests.get(f"{BASE}/favorites/me", headers=h(tok), timeout=30).json()
                    if b["id"] == biz["id"]]) == 1
        d = requests.delete(f"{BASE}/favorites/{biz['id']}", headers=h(tok), timeout=30)
        assert d.status_code == 200 and d.json()["favorited"] is False
        assert biz["id"] not in [b["id"] for b in requests.get(f"{BASE}/favorites/me", headers=h(tok), timeout=30).json()]

    def test_favorites_unauthenticated(self):
        assert requests.get(f"{BASE}/favorites/me", timeout=30).status_code in (401, 403)


# --- Reviews ---
class TestReviews:
    def test_review_flow_and_rating_recompute(self, customer):
        tok = customer["token"]
        biz = requests.get(f"{BASE}/businesses", params={"q": "biryani"}, timeout=30).json()["items"][0]
        bid = biz["id"]
        r = requests.post(f"{BASE}/businesses/{bid}/reviews", headers=h(tok),
                          json={"rating": 4, "comment": "TEST good"}, timeout=30)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        lst = requests.get(f"{BASE}/businesses/{bid}/reviews", timeout=30)
        assert lst.status_code == 200
        mine = [x for x in lst.json() if x["id"] == rid]
        assert len(mine) == 1
        assert mine[0]["user"]["name"] == customer["user"]["name"]
        after = requests.get(f"{BASE}/businesses/{bid}", timeout=30).json()
        assert after["review_count"] >= 1
        assert after["rating"] == 4.0 if after["review_count"] == 1 else True

        # overwrite
        r2 = requests.post(f"{BASE}/businesses/{bid}/reviews", headers=h(tok),
                           json={"rating": 5, "comment": "TEST better"}, timeout=30)
        assert r2.status_code == 200
        rid2 = r2.json()["id"]
        reviews = requests.get(f"{BASE}/businesses/{bid}/reviews", timeout=30).json()
        assert len([x for x in reviews if x["user_id"] == customer["user"]["id"]]) == 1
        assert not any(x["id"] == rid for x in reviews)

        mine_list = requests.get(f"{BASE}/reviews/me", headers=h(tok), timeout=30)
        assert mine_list.status_code == 200
        entry = next(x for x in mine_list.json() if x["id"] == rid2)
        assert entry["business"]["name"] == biz["name"]

        # cleanup
        assert requests.delete(f"{BASE}/reviews/{rid2}", headers=h(tok), timeout=30).status_code == 200

    def test_invalid_rating(self, customer):
        biz = requests.get(f"{BASE}/businesses", timeout=30).json()["items"][0]
        r = requests.post(f"{BASE}/businesses/{biz['id']}/reviews", headers=h(customer["token"]),
                          json={"rating": 9, "comment": "x"}, timeout=30)
        assert r.status_code == 422

    def test_review_missing_business(self, customer):
        r = requests.post(f"{BASE}/businesses/{uuid.uuid4()}/reviews", headers=h(customer["token"]),
                          json={"rating": 3, "comment": "x"}, timeout=30)
        assert r.status_code == 404


# --- Enquiries + notifications ---
class TestEnquiries:
    def test_enquiry_and_notification(self, customer, owner):
        tok = customer["token"]
        owner_biz = requests.get(f"{BASE}/businesses/owner/me", headers=h(owner["token"]), timeout=30).json()[0]
        bid = owner_biz["id"]
        payload = {"name": "TEST Lead", "email": "test_lead@example.com",
                   "phone": "+91 90000 00001", "message": "TEST enquiry message"}
        r = requests.post(f"{BASE}/businesses/{bid}/enquiries", headers=h(tok), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        eid = r.json()["id"]
        assert r.json()["status"] == "new"
        assert r.json()["business_name"] == owner_biz["name"]

        mine = requests.get(f"{BASE}/enquiries/me", headers=h(tok), timeout=30)
        assert mine.status_code == 200
        assert eid in [x["id"] for x in mine.json()]

        biz_side = requests.get(f"{BASE}/enquiries/business", headers=h(owner["token"]), timeout=30)
        assert biz_side.status_code == 200
        assert eid in [x["id"] for x in biz_side.json()]

        notes = requests.get(f"{BASE}/notifications/me", headers=h(owner["token"]), timeout=30)
        assert notes.status_code == 200
        assert any(x["type"] == "enquiry" and "TEST Lead" in x["body"] for x in notes.json())

    def test_enquiry_unauth_business_role(self, customer):
        r = requests.get(f"{BASE}/enquiries/business", headers=h(customer["token"]), timeout=30)
        assert r.status_code == 403

    def test_enquiries_me_unauthenticated(self):
        assert requests.get(f"{BASE}/enquiries/me", timeout=30).status_code in (401, 403)

    def test_notifications_mark_read(self, owner):
        tok = owner["token"]
        notes = requests.get(f"{BASE}/notifications/me", headers=h(tok), timeout=30).json()
        if notes:
            nid = notes[0]["id"]
            assert requests.patch(f"{BASE}/notifications/{nid}/read", headers=h(tok), timeout=30).status_code == 200
            fresh = requests.get(f"{BASE}/notifications/me", headers=h(tok), timeout=30).json()
            assert next(x for x in fresh if x["id"] == nid)["read"] is True
        assert requests.post(f"{BASE}/notifications/read-all", headers=h(tok), timeout=30).status_code == 200
        fresh = requests.get(f"{BASE}/notifications/me", headers=h(tok), timeout=30).json()
        assert all(x["read"] is True for x in fresh)


# --- Subscriptions ---
class TestSubscriptions:
    def test_plans(self):
        r = requests.get(f"{BASE}/subscriptions/plans", timeout=30)
        assert r.status_code == 200
        plans = r.json()
        assert [p["id"] for p in plans] == ["free", "starter", "pro", "enterprise"]

    def test_subscribe_flow(self, owner):
        tok = owner["token"]
        r = requests.post(f"{BASE}/subscriptions/subscribe", headers=h(tok), json={"plan_id": "pro"}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["plan_name"] == "Pro"
        me = requests.get(f"{BASE}/subscriptions/me", headers=h(tok), timeout=30)
        assert me.status_code == 200
        assert me.json()["plan_id"] == "pro" and me.json()["status"] == "active"
        # revert
        requests.post(f"{BASE}/subscriptions/subscribe", headers=h(tok), json={"plan_id": "free"}, timeout=30)

    def test_invalid_plan(self, customer):
        r = requests.post(f"{BASE}/subscriptions/subscribe", headers=h(customer["token"]),
                          json={"plan_id": "nope"}, timeout=30)
        assert r.status_code == 400


# --- Claims ---
class TestClaims:
    def test_claim_flow_approve(self, admin):
        # dedicated claimer user + dedicated business so we don't disturb seed data
        email = f"TEST_claim_{uuid.uuid4().hex[:8]}@example.com"
        reg = requests.post(f"{BASE}/auth/register", json={
            "name": "TEST Claimer", "email": email, "password": "Passw0rd!"}, timeout=30).json()
        tok = reg["token"]
        cat = requests.get(f"{BASE}/categories", timeout=30).json()[0]
        biz = requests.post(f"{BASE}/businesses", headers=h(admin["token"]), json={
            "name": f"TEST Claim Biz {uuid.uuid4().hex[:5]}", "description": "d",
            "category_id": cat["id"], "address": "a", "city": "c", "phone": "1"}, timeout=30).json()

        c = requests.post(f"{BASE}/businesses/{biz['id']}/claim", headers=h(tok),
                          json={"reason": "TEST owner of this"}, timeout=30)
        assert c.status_code == 200, c.text
        cid = c.json()["id"]
        assert c.json()["status"] == "pending"

        dup = requests.post(f"{BASE}/businesses/{biz['id']}/claim", headers=h(tok),
                            json={"reason": "again"}, timeout=30)
        assert dup.status_code == 400

        mine = requests.get(f"{BASE}/claims/me", headers=h(tok), timeout=30)
        assert mine.status_code == 200 and cid in [x["id"] for x in mine.json()]

        all_c = requests.get(f"{BASE}/claims", headers=h(admin["token"]), timeout=30)
        assert all_c.status_code == 200 and cid in [x["id"] for x in all_c.json()]

        ap = requests.post(f"{BASE}/claims/{cid}/approve", headers=h(admin["token"]), timeout=30)
        assert ap.status_code == 200
        after = requests.get(f"{BASE}/businesses/{biz['id']}", timeout=30).json()
        assert after["owner_id"] == reg["user"]["id"]
        assert requests.get(f"{BASE}/auth/me", headers=h(tok), timeout=30).json()["role"] == "business_owner"
        notes = requests.get(f"{BASE}/notifications/me", headers=h(tok), timeout=30).json()
        assert any(x["type"] == "claim" and "approved" in x["body"].lower() for x in notes)

        requests.delete(f"{BASE}/businesses/{biz['id']}", headers=h(admin["token"]), timeout=30)
        requests.delete(f"{BASE}/admin/users/{reg['user']['id']}", headers=h(admin["token"]), timeout=30)

    def test_claim_reject(self, admin, customer):
        biz = requests.get(f"{BASE}/businesses", timeout=30).json()["items"][-1]
        c = requests.post(f"{BASE}/businesses/{biz['id']}/claim", headers=h(customer["token"]),
                          json={"reason": "TEST reject path"}, timeout=30)
        assert c.status_code in (200, 400)
        if c.status_code == 400:
            pytest.skip("pending claim already exists")
        cid = c.json()["id"]
        r = requests.post(f"{BASE}/claims/{cid}/reject", headers=h(admin["token"]), timeout=30)
        assert r.status_code == 200
        mine = requests.get(f"{BASE}/claims/me", headers=h(customer["token"]), timeout=30).json()
        assert next(x for x in mine if x["id"] == cid)["status"] == "rejected"

    def test_claims_list_non_admin(self, customer):
        assert requests.get(f"{BASE}/claims", headers=h(customer["token"]), timeout=30).status_code == 403

    def test_claim_missing_business(self, customer):
        r = requests.post(f"{BASE}/businesses/{uuid.uuid4()}/claim", headers=h(customer["token"]),
                          json={"reason": "x"}, timeout=30)
        assert r.status_code == 404


# --- Admin ---
class TestAdmin:
    def test_stats(self, admin):
        r = requests.get(f"{BASE}/admin/stats", headers=h(admin["token"]), timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("users", "businesses", "verified_businesses", "reviews", "enquiries", "pending_claims"):
            assert isinstance(d[k], int)
        assert d["businesses"] >= 12 and d["users"] >= 3

    def test_users_list_and_role_change(self, admin):
        r = requests.get(f"{BASE}/admin/users", headers=h(admin["token"]), timeout=30)
        assert r.status_code == 200
        users = r.json()
        assert all("password" not in u and "_id" not in u for u in users)

        email = f"TEST_role_{uuid.uuid4().hex[:8]}@example.com"
        reg = requests.post(f"{BASE}/auth/register", json={
            "name": "TEST Role", "email": email, "password": "Passw0rd!"}, timeout=30).json()
        uid = reg["user"]["id"]
        up = requests.patch(f"{BASE}/admin/users/{uid}/role", params={"role": "business_owner"},
                            headers=h(admin["token"]), timeout=30)
        assert up.status_code == 200
        users = requests.get(f"{BASE}/admin/users", headers=h(admin["token"]), timeout=30).json()
        assert next(u for u in users if u["id"] == uid)["role"] == "business_owner"

        bad = requests.patch(f"{BASE}/admin/users/{uid}/role", params={"role": "superuser"},
                             headers=h(admin["token"]), timeout=30)
        assert bad.status_code == 400

        d = requests.delete(f"{BASE}/admin/users/{uid}", headers=h(admin["token"]), timeout=30)
        assert d.status_code == 200
        users = requests.get(f"{BASE}/admin/users", headers=h(admin["token"]), timeout=30).json()
        assert uid not in [u["id"] for u in users]

    def test_admin_cannot_delete_self(self, admin):
        r = requests.delete(f"{BASE}/admin/users/{admin['user']['id']}", headers=h(admin["token"]), timeout=30)
        assert r.status_code == 400

    def test_admin_routes_protected(self, customer):
        for path in ("/admin/stats", "/admin/users"):
            assert requests.get(f"{BASE}{path}", headers=h(customer["token"]), timeout=30).status_code == 403
            assert requests.get(f"{BASE}{path}", timeout=30).status_code in (401, 403)

    def test_invalid_token(self):
        r = requests.get(f"{BASE}/auth/me", headers=h("garbage.token.value"), timeout=30)
        assert r.status_code == 401
