"""One-off cleanup of QA test artifacts created during UI testing."""
import os
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

BASE = (dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"]).rstrip("/") + "/api"
tok = requests.post(f"{BASE}/auth/login", json={"email": "admin@infoez.com", "password": "Admin@123"}).json()["token"]
H = {"Authorization": f"Bearer {tok}"}

# delete QA-created businesses
biz = requests.get(f"{BASE}/businesses", params={"q": "TEST QA", "limit": 50}).json()["items"]
for b in [x for x in biz if x["name"].startswith("TEST")]:
    print("deleting business", b["name"], requests.delete(f"{BASE}/businesses/{b['id']}", headers=H).status_code)

# delete QA users
users = requests.get(f"{BASE}/admin/users", headers=H).json()
for u in users:
    if u["email"].startswith(("test_", "TEST_")):
        print("deleting user", u["email"], requests.delete(f"{BASE}/admin/users/{u['id']}", headers=H).status_code)

# restore seeded business fields mutated by tests
env = dotenv_values("/app/backend/.env")
mc = MongoClient(env["MONGO_URL"])
db = mc[env["DB_NAME"]]
db.reviews.delete_many({"comment": {"$regex": "^TEST"}})
db.enquiries.delete_many({"message": {"$regex": "^TEST"}})
db.claims.delete_many({"reason": {"$regex": "^TEST"}})
db.notifications.delete_many({"body": {"$regex": "TEST"}})
restore = {
    "Sundara Coffee Roasters": ("Small-batch specialty coffee roasted in-house. Warm neighbourhood cafe with pour-overs, pastries and a quiet loft.", 4.7),
    "Naga Biryani House": (None, 4.9),
}
for name, (desc, rating) in restore.items():
    upd = {"rating": rating, "review_count": 0}
    if desc:
        upd["description"] = desc
    print(name, db.businesses.update_one({"name": name}, {"$set": upd}).modified_count)
print("categories:", db.categories.count_documents({}), "businesses:", db.businesses.count_documents({}), "users:", db.users.count_documents({}))
