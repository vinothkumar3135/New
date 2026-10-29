"""Restore the seeded 'Sundara Coffee Roasters' business that cleanup removed by mistake."""
from dotenv import dotenv_values
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid

env = dotenv_values("/app/backend/.env")
mc = MongoClient(env["MONGO_URL"])
db = mc[env["DB_NAME"]]

SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1571942948809-74637bfc59b9?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    "https://images.unsplash.com/photo-1511018556340-d16986a1c194?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
]
owner = db.users.find_one({"email": "owner@infoez.com"})
cat = db.categories.find_one({"name": "Cafes & Bakeries"})
if db.businesses.find_one({"slug": "sundara-coffee-roasters-1"}):
    print("already present")
else:
    doc = {
        "id": str(uuid.uuid4()),
        "owner_id": owner["id"],
        "slug": "sundara-coffee-roasters-1",
        "name": "Sundara Coffee Roasters",
        "description": "Small-batch specialty coffee roasted in-house. Warm neighbourhood cafe with pour-overs, pastries and a quiet loft.",
        "category_id": cat["id"],
        "address": "12 Church Street",
        "city": "Bengaluru",
        "phone": "+91 980000000",
        "email": "hello@sundara-coffee-roasters.in",
        "website": "https://sundara-coffee-roasters.in",
        "services": ["Espresso", "Pour Over", "Cold Brew", "Pastries"],
        "images": [SAMPLE_IMAGES[0], SAMPLE_IMAGES[1]],
        "price_range": "$",
        "hours": "Mon-Sun 9:00 AM - 10:00 PM",
        "rating": 4.7,
        "review_count": 0,
        "view_count": 100,
        "verified": False,
        "featured": True,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.businesses.insert_one(doc)
    print("restored", doc["slug"])
print("businesses:", db.businesses.count_documents({}))
