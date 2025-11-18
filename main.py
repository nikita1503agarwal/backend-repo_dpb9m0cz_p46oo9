import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document
from schemas import Product as ProductSchema, Order as OrderSchema

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    price: float
    category: str
    image: Optional[str]
    in_stock: bool


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
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
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


# -------------------------
# E-commerce API Endpoints
# -------------------------

@app.get("/api/products", response_model=List[ProductResponse])
def list_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Seed a few products if empty
    if db["product"].count_documents({}) == 0:
        sample_products = [
            {
                "title": "Minimalist Chair",
                "description": "A modern, comfortable chair with a minimalist design.",
                "price": 89.99,
                "category": "Furniture",
                "image": "https://images.unsplash.com/photo-1549187774-b4e9b0445b41?q=80&w=1200&auto=format&fit=crop",
                "in_stock": True,
            },
            {
                "title": "Wireless Headphones",
                "description": "Noise-cancelling over-ear headphones with 30h battery.",
                "price": 129.0,
                "category": "Electronics",
                "image": "https://images.unsplash.com/photo-1518449037270-3c0758cd7ed0?q=80&w=1200&auto=format&fit=crop",
                "in_stock": True,
            },
            {
                "title": "Ceramic Mug",
                "description": "Handmade ceramic mug for coffee or tea (350ml).",
                "price": 16.5,
                "category": "Kitchen",
                "image": "https://images.unsplash.com/photo-1509463531436-7b8b53f6d4ba?q=80&w=1200&auto=format&fit=crop",
                "in_stock": True,
            },
        ]
        db["product"].insert_many(sample_products)

    products = list(db["product"].find())

    def to_response(doc) -> ProductResponse:
        return ProductResponse(
            id=str(doc.get("_id")),
            title=doc.get("title"),
            description=doc.get("description"),
            price=float(doc.get("price", 0)),
            category=doc.get("category", "General"),
            image=doc.get("image"),
            in_stock=bool(doc.get("in_stock", True)),
        )

    return [to_response(p) for p in products]


@app.post("/api/products", response_model=dict)
def create_product(product: ProductSchema):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    new_id = create_document("product", product)
    return {"id": new_id}


@app.post("/api/orders", response_model=dict)
def create_order(order: OrderSchema):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    order_id = create_document("order", order)
    return {"id": order_id, "status": "received"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
