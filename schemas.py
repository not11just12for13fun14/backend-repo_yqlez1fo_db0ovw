"""
Database Schemas for Amberarctic

Each Pydantic model below maps to a MongoDB collection where the collection
name is the lowercase of the class name. For example:
- Product -> "product"
- Review -> "review"
- Order -> "order"

These schemas are used for validation when creating documents.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class Product(BaseModel):
    title: str = Field(..., description="Product model name")
    slug: str = Field(..., description="URL-safe identifier")
    gender: str = Field(..., description="Men | Women | Unisex")
    activity: List[str] = Field(default_factory=list, description="Activities: city, hiking, biking, travel")
    description: Optional[str] = Field(None, description="Marketing description")
    price: float = Field(..., ge=0, description="Price in USD")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    colors: List[str] = Field(default_factory=list, description="Available color names")
    sizes: List[str] = Field(default_factory=lambda: ["XS","S","M","L","XL","XXL"])
    temperature_min_c: int = Field(..., description="Minimum comfortable temperature in Celsius")
    battery_life_hours: int = Field(..., description="Battery life on standard mode")
    warmth_level: int = Field(..., ge=1, le=10, description="1-10 warmth scale")
    features: List[str] = Field(default_factory=list, description="Feature badges e.g., waterproof")

class Review(BaseModel):
    product_slug: str = Field(..., description="Associated product slug")
    name: str = Field(..., description="Reviewer name")
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(...)
    city: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    email: str
    message: str

class SizeProfile(BaseModel):
    height_cm: int = Field(..., ge=120, le=230)
    weight_kg: int = Field(..., ge=35, le=180)
    build: str = Field(..., description="slim | average | athletic | broad")
    gender: Optional[str] = Field(None, description="Men | Women | Unisex")

class OrderItem(BaseModel):
    product_slug: str
    size: str
    color: str
    quantity: int = Field(..., ge=1)

class Order(BaseModel):
    items: List[OrderItem]
    email: str
    shipping_name: str
    shipping_address: str
    city: str
    country: str
    postal_code: str
    total: float = Field(..., ge=0)
