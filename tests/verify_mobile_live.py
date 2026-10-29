"""Live integration script simulating Mobile-App/src/api.ts against http://192.168.1.11:8000."""

import urllib.request
import json
import sys

BASE_URL = "http://192.168.1.11:8000/api"

def request(path, method="GET", body=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def run():
    print(f"Connecting to {BASE_URL}...")

    # 1. Locations
    locations = request("/locations")
    print(f"  [OK] GET /locations -> {len(locations)} cities found: {[loc['city'] for loc in locations[:3]]}...")

    # 2. Categories
    categories = request("/categories")
    print(f"  ✓ GET /categories -> {len(categories)} categories")

    # 3. Businesses list
    biz_list = request("/businesses?limit=3")
    print(f"  ✓ GET /businesses -> {len(biz_list['items'])} items, total: {biz_list['total']}, pages: {biz_list['pages']}")
    first_biz = biz_list["items"][0]

    # 4. Business detail dual compatibility
    detail = request(f"/businesses/{first_biz['slug']}")
    assert "business" in detail, "Missing nested business"
    assert "reviews" in detail, "Missing reviews"
    assert "similar" in detail, "Missing similar"
    assert "name" in detail, "Missing root business fields"
    print(f"  ✓ GET /businesses/{first_biz['slug']} -> Dual compatible (root name: '{detail['name']}', reviews: {len(detail['reviews'])}, similar: {len(detail['similar'])})")

    # 5. Plans
    plans = request("/plans")
    print(f"  ✓ GET /plans -> {len(plans)} plans available: {[p['name'] for p in plans]}")

    # 6. Event tracking
    event_res = request(f"/businesses/{first_biz['id']}/events?kind=call", method="POST")
    print(f"  ✓ POST /businesses/{first_biz['id']}/events -> {event_res}")

    # 7. Login as owner
    login = request("/auth/login", method="POST", body={"email": "owner@infoez.com", "password": "Owner@123"})
    token = login["token"]
    user = login["user"]
    print(f"  ✓ POST /auth/login -> Logged in as {user['name']} (role: {user['role']})")

    # 8. Owner endpoints
    owner_biz = request("/owner/businesses", token=token)
    print(f"  ✓ GET /owner/businesses -> {len(owner_biz)} listings")

    owner_an = request("/owner/analytics", token=token)
    print(f"  ✓ GET /owner/analytics -> Views: {owner_an['views']}, Calls: {owner_an['calls']}, Leads: {owner_an['leads']}")

    owner_tr = request("/owner/analytics/trends", token=token)
    print(f"  ✓ GET /owner/analytics/trends -> {len(owner_tr['days'])} days of trends")

    leads = request("/leads", token=token)
    print(f"  ✓ GET /leads -> {len(leads)} leads")

    # 9. Favorites flow
    fav_add = request(f"/favorites/{first_biz['id']}", method="POST", token=token)
    print(f"  ✓ POST /favorites/{first_biz['id']} -> {fav_add}")

    fav_list = request("/favorites", token=token)
    print(f"  ✓ GET /favorites -> {len(fav_list)} bookmarked businesses")

    fav_del = request(f"/favorites/{first_biz['id']}", method="DELETE", token=token)
    print(f"  ✓ DELETE /favorites/{first_biz['id']} -> {fav_del}")

    # 10. Admin endpoints
    admin_login = request("/auth/login", method="POST", body={"email": "admin@infoez.com", "password": "Admin@123"})
    admin_token = admin_login["token"]

    overview = request("/admin/overview", token=admin_token)
    print(f"  ✓ GET /admin/overview -> Users: {overview['users']}, Listings: {overview['businesses']}, Categories: {overview['categories']}")

    print("\nALL MOBILE ENDPOINTS VERIFIED SUCCESSFULLY OVER LAN IP 192.168.1.11:8000! 🎉")

if __name__ == "__main__":
    run()
