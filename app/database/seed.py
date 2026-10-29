"""Database seeder for Infoez: pre-populates categories, demo users, and sample businesses."""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import hash_password
from app.utils.datetime import now_iso, new_id
from app.utils.slug import slugify

logger = logging.getLogger("infoez.seed")

DEFAULT_CATEGORIES = [
    {"name": "Restaurants", "icon": "UtensilsCrossed", "color": "#EF4444"},
    {"name": "Cafes & Bakeries", "icon": "Coffee", "color": "#D97706"},
    {"name": "Beauty & Spa", "icon": "Sparkles", "color": "#EC4899"},
    {"name": "Fitness & Wellness", "icon": "Dumbbell", "color": "#10B981"},
    {"name": "Home Services", "icon": "Wrench", "color": "#6366F1"},
    {"name": "Auto & Repair", "icon": "Car", "color": "#0EA5E9"},
    {"name": "Health & Medical", "icon": "Stethoscope", "color": "#14B8A6"},
    {"name": "Retail & Shopping", "icon": "ShoppingBag", "color": "#8B5CF6"},
    {"name": "Education", "icon": "GraduationCap", "color": "#F59E0B"},
    {"name": "Professional", "icon": "Briefcase", "color": "#64748B"},
]

SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1571942948809-74637bfc59b9?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    "https://images.unsplash.com/photo-1511018556340-d16986a1c194?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    "https://images.pexels.com/photos/33870288/pexels-photo-33870288.jpeg?auto=compress&cs=tinysrgb&w=1200",
    "https://images.pexels.com/photos/5865683/pexels-photo-5865683.jpeg?auto=compress&cs=tinysrgb&w=1200",
    "https://images.pexels.com/photos/19571937/pexels-photo-19571937.jpeg?auto=compress&cs=tinysrgb&w=1200",
    "https://images.unsplash.com/photo-1584696049838-8e692282a2e6?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
]

SAMPLE_BUSINESSES = [
    ("Sundara Coffee Roasters", "Cafes & Bakeries", "Small-batch specialty coffee roasted in-house. Warm neighbourhood cafe with pour-overs, pastries and a quiet loft.", "Bengaluru", "12 Church Street", ["Espresso", "Pour Over", "Cold Brew", "Pastries"], 4.7, 12.9749, 77.6069),
    ("Amma's South Kitchen", "Restaurants", "Authentic South Indian cuisine, hand-ground masalas and heirloom recipes served on banana leaves.", "Chennai", "88 Mylapore Road", ["Dine-in", "Takeaway", "Catering", "Thali"], 4.8, 13.0356, 80.2680),
    ("Bloom Beauty Studio", "Beauty & Spa", "Full-service salon offering hair, skin, nails and bridal packages by senior stylists.", "Mumbai", "45 Bandra West", ["Haircut", "Facial", "Bridal", "Nails"], 4.6, 19.0596, 72.8295),
    ("Iron Peak Gym", "Fitness & Wellness", "Modern strength & conditioning gym with certified coaches, group HIIT and personal training.", "Bengaluru", "22 Indiranagar", ["Personal Training", "HIIT", "CrossFit", "Nutrition"], 4.5, 12.9784, 77.6408),
    ("HomeFix Pro", "Home Services", "Trusted electricians, plumbers and handymen. Same-day service, background verified professionals.", "Hyderabad", "Gachibowli Main Rd", ["Electrical", "Plumbing", "Painting", "AC Repair"], 4.4, 17.4400, 78.3489),
    ("QuickShift Auto", "Auto & Repair", "Multi-brand car service centre with genuine parts, insurance claims and doorstep pickup.", "Pune", "FC Road 34", ["Servicing", "Denting", "Insurance", "Pickup"], 4.3, 18.5204, 73.8567),
    ("Aarogya Clinic", "Health & Medical", "General physicians, paediatrics and lab tests under one roof. Walk-ins welcome.", "Chennai", "Anna Nagar East", ["Consultation", "Lab Tests", "Vaccination"], 4.6, 13.0850, 80.2101),
    ("The Curated Closet", "Retail & Shopping", "Independent boutique for slow fashion, handloom sarees and local designer wear.", "Bengaluru", "MG Road", ["Sarees", "Kurtis", "Accessories"], 4.5, 12.9752, 77.6098),
    ("Bright Minds Academy", "Education", "K-12 tutoring, olympiad prep and STEM workshops with small batch sizes.", "Mumbai", "Andheri West", ["Tutoring", "Olympiad", "STEM"], 4.7, 19.1197, 72.8464),
    ("Ledger & Co.", "Professional", "Chartered accountants for SMEs. GST, tax filing, audits and financial advisory.", "Delhi", "Connaught Place", ["GST", "Tax Filing", "Audit"], 4.4, 28.6328, 77.2197),
    ("Petal & Loom Bakery", "Cafes & Bakeries", "Artisan sourdough, cakes and celebration desserts baked fresh daily.", "Hyderabad", "Jubilee Hills", ["Sourdough", "Cakes", "Croissants"], 4.6, 17.4239, 78.4738),
    ("Naga Biryani House", "Restaurants", "Legendary dum biryani with slow-cooked flavour. Family recipes since 1978.", "Hyderabad", "Charminar Lane", ["Biryani", "Kebabs", "Desserts"], 4.9, 17.3616, 78.4747),
]

async def ensure_demo_users(db: AsyncIOMotorDatabase) -> dict:
    """Idempotently create or repair core demo users with expected roles and credentials."""
    demo_users = [
        {
            "name": "Infoez Admin",
            "email": "admin@infoez.com",
            "password": hash_password("Admin@123"),
            "role": "admin",
            "phone": None,
            "status": "active",
        },
        {
            "name": "Ravi Kumar",
            "email": "owner@infoez.com",
            "password": hash_password("Owner@123"),
            "role": "business_owner",
            "phone": "+91 90000 00000",
            "status": "active",
        },
        {
            "name": "Priya Sharma",
            "email": "customer@infoez.com",
            "password": hash_password("Customer@123"),
            "role": "customer",
            "phone": "+91 91111 11111",
            "status": "active",
        },
    ]

    reconciled = {}
    for user_info in demo_users:
        existing = await db.users.find_one({"email": user_info["email"]})
        if existing:
            # Reconcile role and password if conflicted or demoted
            await db.users.update_one(
                {"email": user_info["email"]},
                {
                    "$set": {
                        "role": user_info["role"],
                        "password": user_info["password"],
                        "status": "active",
                    }
                },
            )
            reconciled[user_info["email"]] = user_info["role"]
        else:
            doc = {
                "id": new_id(),
                "name": user_info["name"],
                "email": user_info["email"],
                "password": user_info["password"],
                "role": user_info["role"],
                "phone": user_info["phone"],
                "avatar": None,
                "status": "active",
                "created_at": now_iso(),
            }
            await db.users.insert_one(doc)
            reconciled[user_info["email"]] = user_info["role"]

    return reconciled


async def seed_database(db: AsyncIOMotorDatabase) -> dict:
    """Idempotently seed categories, users, sample businesses, and reviews, while self-healing demo accounts."""
    # Always ensure core demo users have correct roles (self-heals any demoted admin/customer accounts)
    reconciled = await ensure_demo_users(db)

    if await db.categories.count_documents({}) > 0:
        logger.info("Database already seeded. Demo user roles reconciled successfully.")
        return {
            "ok": True,
            "already_seeded": True,
            "demo_users_reconciled": reconciled,
            "users": await db.users.count_documents({}),
            "businesses": await db.businesses.count_documents({}),
            "categories": await db.categories.count_documents({}),
            "admin_email": "admin@infoez.com",
            "admin_role": "admin",
            "owner_email": "owner@infoez.com",
            "owner_role": "business_owner",
            "customer_email": "customer@infoez.com",
            "customer_role": "customer",
        }

    logger.info("Seeding database with default dataset...")

    # 1. Categories
    cats = []
    for c in DEFAULT_CATEGORIES:
        doc = {
            "id": new_id(),
            "name": c["name"],
            "slug": slugify(c["name"]),
            "icon": c["icon"],
            "color": c["color"],
            "created_at": now_iso(),
        }
        cats.append(doc)
    await db.categories.insert_many(cats)
    cat_by_name = {c["name"]: c for c in cats}

    # Fetch reconciled users for business and review references
    owner = await db.users.find_one({"email": "owner@infoez.com"})
    customer = await db.users.find_one({"email": "customer@infoez.com"})

    # 2. Sample Businesses & Reviews (All businesses belong to the business owner, not admin)
    biz_docs = []
    review_docs = []
    for i, (name, cat_name, desc, city, addr, services, rating, lat, lng) in enumerate(SAMPLE_BUSINESSES):
        cat = cat_by_name.get(cat_name)
        bid = new_id()
        review_rating = int(round(rating))
        if customer:
            review_docs.append({
                "id": new_id(),
                "business_id": bid,
                "user_id": customer["id"],
                "rating": review_rating,
                "comment": "Great experience — friendly staff, quality service, would recommend.",
                "created_at": now_iso(),
            })
        biz_docs.append({
            "id": bid,
            "owner_id": owner["id"] if owner else new_id(),
            "slug": f"{slugify(name)}-{i + 1}",
            "name": name,
            "description": desc,
            "category_id": cat["id"] if cat else None,
            "address": addr,
            "city": city,
            "lat": lat,
            "lng": lng,
            "phone": f"+91 9{80000000 + i * 1234}",
            "email": f"hello@{slugify(name)}.in",
            "website": f"https://{slugify(name)}.in",
            "services": services,
            "images": [
                SAMPLE_IMAGES[i % len(SAMPLE_IMAGES)],
                SAMPLE_IMAGES[(i + 1) % len(SAMPLE_IMAGES)],
            ],
            "price_range": ["$", "$$", "$$$"][i % 3],
            "hours": "Mon-Sun 9:00 AM - 10:00 PM",
            "rating": float(review_rating),
            "review_count": 1,
            "view_count": 100 + i * 15,
            "verified": i % 3 != 0,
            "featured": i < 4,
            "status": "active",
            "created_at": now_iso(),
        })

    await db.businesses.insert_many(biz_docs)
    await db.reviews.insert_many(review_docs)

    logger.info("Database seeding completed successfully.")
    return {
        "ok": True,
        "seeded": True,
        "admin_email": "admin@infoez.com",
        "admin_password": "Admin@123",
        "owner_email": "owner@infoez.com",
        "owner_password": "Owner@123",
        "customer_email": "customer@infoez.com",
        "customer_password": "Customer@123",
    }
