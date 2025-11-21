import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Product, Review, ContactMessage, SizeProfile, Order

app = FastAPI(title="Amberarctic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"brand": "Amberarctic", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:60]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:60]}"
    return response

# Seed sample products if none exist (idempotent)
@app.post("/seed")
def seed():
    try:
        existing = list(db["product"].find({})) if db else []
        if existing:
            return {"seeded": False, "count": len(existing)}
        sample_products = [
            {
                "title": "Arctic Edge Pro",
                "slug": "arctic-edge-pro",
                "gender": "Unisex",
                "activity": ["city", "hiking", "travel"],
                "description": "Premium heated jacket engineered for -30°C with sleek urban design.",
                "price": 399.0,
                "images": ["/images/arctic-edge-pro-1.jpg", "/images/arctic-edge-pro-2.jpg"],
                "colors": ["Glacier Blue", "Charcoal Black", "Frost White"],
                "sizes": ["XS","S","M","L","XL","XXL"],
                "temperature_min_c": -30,
                "battery_life_hours": 10,
                "warmth_level": 9,
                "features": ["waterproof", "windproof", "rechargeable", "lightweight"]
            },
            {
                "title": "Polar Stealth Lite",
                "slug": "polar-stealth-lite",
                "gender": "Men",
                "activity": ["city", "biking"],
                "description": "Minimal techwear silhouette with targeted heating zones.",
                "price": 329.0,
                "images": ["/images/polar-stealth-lite-1.jpg"],
                "colors": ["Charcoal Black", "Icy Silver"],
                "sizes": ["S","M","L","XL"],
                "temperature_min_c": -20,
                "battery_life_hours": 8,
                "warmth_level": 7,
                "features": ["waterproof", "windproof", "rechargeable"]
            },
            {
                "title": "Glacier Flow Aero",
                "slug": "glacier-flow-aero",
                "gender": "Women",
                "activity": ["travel", "hiking"],
                "description": "Featherlight performance for fast movement in cold climates.",
                "price": 349.0,
                "images": ["/images/glacier-flow-aero-1.jpg"],
                "colors": ["Aurora Blue", "Frost White"],
                "sizes": ["XS","S","M","L"],
                "temperature_min_c": -18,
                "battery_life_hours": 9,
                "warmth_level": 8,
                "features": ["waterproof", "rechargeable", "lightweight"]
            }
        ]
        for p in sample_products:
            create_document("product", p)
        return {"seeded": True, "count": len(sample_products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Products API
@app.get("/products")
def list_products(gender: Optional[str] = None, activity: Optional[str] = None, min_temp: Optional[int] = None):
    query = {}
    if gender:
        query["gender"] = gender
    if activity:
        query["activity"] = {"$in": [activity]}
    if min_temp is not None:
        query["temperature_min_c"] = {"$lte": int(min_temp)}
    try:
        items = list(db["product"].find(query))
        for it in items:
            it["_id"] = str(it["_id"])  # serialize
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{slug}")
def get_product(slug: str):
    try:
        doc = db["product"].find_one({"slug": slug})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        doc["_id"] = str(doc["_id"])
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reviews
@app.get("/reviews/{product_slug}")
def get_reviews(product_slug: str):
    try:
        items = list(db["review"].find({"product_slug": product_slug}))
        for it in items:
            it["_id"] = str(it["_id"])
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reviews")
def add_review(review: Review):
    try:
        create_document("review", review)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Contact
@app.post("/contact")
def send_contact(msg: ContactMessage):
    try:
        create_document("contactmessage", msg)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Size recommendation (very simple heuristic)
@app.post("/size/recommend")
def recommend_size(profile: SizeProfile):
    h = profile.height_cm
    w = profile.weight_kg
    build = profile.build
    score = (h - 160) + (w - 60)
    if build in ["athletic", "broad"]:
        score += 10
    if score < 0:
        size = "XS"
    elif score < 10:
        size = "S"
    elif score < 20:
        size = "M"
    elif score < 30:
        size = "L"
    elif score < 40:
        size = "XL"
    else:
        size = "XXL"
    return {"recommended_size": size}

# Checkout (store order)
@app.post("/checkout")
def checkout(order: Order):
    try:
        create_document("order", order)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
