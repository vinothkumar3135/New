"""Iteration-3 cleanup: purge TEST_* enquiries/reviews/businesses, restore customer phone
and restore the seeded review for any business left with 0 reviews."""
import asyncio, os, uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]


async def main():
    r = await db.enquiries.delete_many({"$or": [
        {"message": {"$regex": "TEST", "$options": "i"}},
        {"name": {"$regex": "^TEST", "$options": "i"}},
        {"email": {"$regex": "test_qa", "$options": "i"}},
    ]})
    print("enquiries removed:", r.deleted_count)

    r = await db.reviews.delete_many({"comment": {"$regex": "TEST_", "$options": "i"}})
    print("test reviews removed:", r.deleted_count)

    r = await db.businesses.delete_many({"name": {"$regex": "^TEST", "$options": "i"}})
    print("test businesses removed:", r.deleted_count)

    r = await db.categories.delete_many({"name": {"$regex": "^TEST", "$options": "i"}})
    print("test categories removed:", r.deleted_count)

    r = await db.users.delete_many({"email": {"$regex": "^test_", "$options": "i"}})
    print("test users removed:", r.deleted_count)

    r = await db.claims.delete_many({"reason": {"$regex": "TEST", "$options": "i"}})
    print("test claims removed:", r.deleted_count)

    # restore customer phone (cleared during UI blank-phone test)
    await db.users.update_one({"email": "customer@infoez.com"}, {"$set": {"phone": "+91 99999 00000"}})
    print("customer phone restored")

    # restore a seeded review for businesses that ended up with 0 reviews
    customer = await db.users.find_one({"email": "customer@infoez.com"})
    async for b in db.businesses.find({}, {"_id": 0}):
        cnt = await db.reviews.count_documents({"business_id": b["id"]})
        if cnt == 0:
            rating = 4.5
            await db.reviews.insert_one({
                "id": str(uuid.uuid4()), "business_id": b["id"], "user_id": customer["id"],
                "rating": round(rating), "comment": "Great experience, would definitely come back.",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            await db.businesses.update_one({"id": b["id"]},
                                           {"$set": {"rating": rating, "review_count": 1}})
            print("restored review for", b["name"])
        else:
            await db.businesses.update_one({"id": b["id"]}, {"$set": {"review_count": cnt}})

    print("final: businesses=%d reviews=%d enquiries=%d users=%d" % (
        await db.businesses.count_documents({}), await db.reviews.count_documents({}),
        await db.enquiries.count_documents({}), await db.users.count_documents({})))


asyncio.run(main())
