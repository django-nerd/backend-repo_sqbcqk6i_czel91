"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# Example schemas (kept for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# --------------------------------------------------
# SaaS Oil Company App Schemas
# --------------------------------------------------

class Userauth(BaseModel):
    """
    Auth users collection
    Collection: "userauth"
    """
    name: str
    email: EmailStr
    password_hash: str
    company: Optional[str] = None
    role: str = "user"

class Blogpost(BaseModel):
    """
    Blog posts collection
    Collection: "blogpost"
    """
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author: str
    tags: List[str] = []
    published: bool = True
    published_at: Optional[datetime] = None
    cover_image: Optional[str] = None

class Contactmessage(BaseModel):
    """
    Contact form submissions
    Collection: "contactmessage"
    """
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: str
    subject: Optional[str] = None
    status: str = "new"  # new, read, responded

class Pricingplan(BaseModel):
    """
    Pricing plans
    Collection: "pricingplan"
    """
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str]
    most_popular: bool = False
