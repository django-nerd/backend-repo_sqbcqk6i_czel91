import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from database import db, create_document, get_documents
from schemas import Contactmessage, Blogpost, Userauth, Pricingplan

app = FastAPI(title="Oil SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Oil SaaS API running"}

# ----------------------
# Auth (simple demo only)
# ----------------------
class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    company: Optional[str] = None

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    company: Optional[str] = None
    token: str

from hashlib import sha256

def hash_password(pw: str) -> str:
    return sha256(pw.encode()).hexdigest()

@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(payload: SignUpRequest):
    existing = get_documents("userauth", {"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = Userauth(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        company=payload.company or None,
    )
    new_id = create_document("userauth", user)

    return AuthResponse(
        user_id=new_id,
        name=user.name,
        email=user.email,
        company=user.company,
        token=hash_password(user.email + new_id)[:32]
    )

@app.post("/api/auth/signin", response_model=AuthResponse)
def signin(payload: SignInRequest):
    users = get_documents("userauth", {"email": payload.email})
    if not users:
        raise HTTPException(status_code=404, detail="User not found")
    user = users[0]
    if user.get("password_hash") != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = hash_password(user["email"] + str(user["_id"]))[:32]
    return AuthResponse(
        user_id=str(user["_id"]),
        name=user.get("name"),
        email=user.get("email"),
        company=user.get("company"),
        token=token
    )

# --------------
# Blog endpoints
# --------------
class BlogCreate(BaseModel):
    title: str
    excerpt: Optional[str] = None
    content: str
    author: str
    tags: List[str] = []
    cover_image: Optional[str] = None

@app.post("/api/blog", response_model=dict)
def create_blog(post: BlogCreate):
    slug = post.title.lower().replace(" ", "-")
    blog = Blogpost(
        title=post.title,
        slug=slug,
        excerpt=post.excerpt,
        content=post.content,
        author=post.author,
        tags=post.tags,
        cover_image=post.cover_image,
        published=True,
        published_at=datetime.utcnow()
    )
    new_id = create_document("blogpost", blog)
    return {"id": new_id, "slug": slug}

@app.get("/api/blog", response_model=List[dict])
def list_blogs(limit: int = 10):
    posts = get_documents("blogpost", {"published": True}, limit)
    # Serialize ObjectId
    for p in posts:
        p["id"] = str(p.pop("_id", ""))
    return posts

# -----------------
# Contact endpoint
# -----------------
class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    subject: Optional[str] = None
    message: str

@app.post("/api/contact", response_model=dict)
def submit_contact(payload: ContactRequest):
    doc = Contactmessage(
        name=payload.name,
        email=payload.email,
        company=payload.company,
        subject=payload.subject,
        message=payload.message,
        status="new"
    )
    doc_id = create_document("contactmessage", doc)
    return {"status": "ok", "id": doc_id}

# -----------------
# Pricing endpoint
# -----------------
@app.get("/api/pricing", response_model=List[dict])
def get_pricing():
    # seed default plans if empty
    count = db.pricingplan.count_documents({}) if db else 0
    if count == 0 and db:
        plans = [
            Pricingplan(name="Starter", price_monthly=49, price_yearly=490, features=[
                "Up to 1,000 barrels tracked",
                "Basic analytics",
                "Email support"
            ], most_popular=False),
            Pricingplan(name="Pro", price_monthly=199, price_yearly=1990, features=[
                "Up to 25,000 barrels tracked",
                "Advanced analytics",
                "API access",
                "Priority support"
            ], most_popular=True),
            Pricingplan(name="Enterprise", price_monthly=0, price_yearly=0, features=[
                "Unlimited scale",
                "Custom SLAs",
                "Dedicated onboarding",
                "SAML SSO"
            ], most_popular=False),
        ]
        for pl in plans:
            create_document("pricingplan", pl)
    docs = get_documents("pricingplan", {})
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return docs

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
