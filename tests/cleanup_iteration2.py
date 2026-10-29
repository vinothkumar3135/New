"""Cleanup of iteration-2 QA artifacts + restore seeded review/rating state."""
import uuid
from datetime import datetime, timezone

import requests
from dotenv import dotenv_values
from pymongo import MongoClient

env = dotenv_values("/app/backend/.env")
fe = dotenv_values("/app/frontend/.env")
BASE = fe["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
db = MongoClient(env["MONGO_URL"])[env["DB_NAME"]]

tok = requests.post(f"{BASE}/auth/login", json={"email": "admin@infoez.com", "password": "Admin@123"}).json()["token"]
H = {"Authorization": f"Bearer {tok}"}

# businesses / categories created during UI testing
for b in requests.get(f"{BASE}/businesses", params={"limit": 200}).json()["items"]:
    if "TEST" in b["name"].upper():
        print("delete biz", b["name"], requests.delete(f"{BASE}/businesses/{b['id']}", headers=H).status_code)
for c in requests.get(f"{BASE}/categories").json():
    if c["name"].upper().startswith("TEST"):
        print("delete cat", c["name"], requests.delete(f"{BASE}/categories/{c['id']}", headers=H).status_code)

print("enquiries", db.enquiries.delete_many({"$or": [{"name": {"$regex": "^TEST"}}, {"message": {"$regex": "^TEST"}}]}).deleted_count)
print("reviews", db.reviews.delete_many({"comment": {"$regex": "^TEST"}}).deleted_count)
print("claims", db.claims.delete_many({"reason": {"$regex": "^TEST"}}).deleted_count)
print("favorites", db.favorites.delete_many({"business_id": {"$nin": [b["id"] for b in db.businesses.find({}, {"id": 1})]}}).deleted_count)
print("users", db.users.delete_many({"email": {"$regex": "^TEST", "$options": "i"}}).deleted_count)
print("notifications", db.notifications.delete_many({"title": {"$regex": "TEST"}}).deleted_count)

# restore seeded single review + rating for businesses whose review was removed by QA
SEED_RATINGS = {"Petal & Loom Bakery": 4.6, "Naga Biryani House": 4.9}
customer = db.users.find_one({"email": "customer@infoez.com"})
for name, rating in SEED_RATINGS.items():
    biz = db.businesses.find_one({"name": name})
    if not biz:
        continue
    db.reviews.delete_many({"business_id": biz["id"]})
    db.reviews.insert_one({
        "id": str(uuid.uuid4()), "business_id": biz["id"], "user_id": customer["id"],
        "rating": min(5, round(rating)), "comment": "Great experience, would definitely come back.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    db.businesses.update_one({"id": biz["id"]}, {"$set": {"rating": rating, "review_count": 3}})
    print("restored", name)

print("final counts biz/rev/enq/claims/users:", db.businesses.count_documents({}), db.reviews.count_documents({}),
      db.enquiries.count_documents({}), db.claims.count_documents({}), db.users.count_documents({}))
