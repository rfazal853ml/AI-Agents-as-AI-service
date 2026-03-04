from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from app.database import init_db
from app.vector_store import search
from app.prompt import build_prompt
from app.llm import generate_response
from pydantic import BaseModel
from app.session import get_session, cart_add, cart_clear, history_append
from app import responses as R
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal, Product

app = FastAPI()

init_db()

conversation_memory = {}

class ChatRequest(BaseModel):
    user_id: str
    message: str



@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    session = get_session(req.user_id)
    cmd     = req.message.strip().lower()

    # ── 1. First-time greeting ────────────────────────────────
    if not session["greeted"]:
        session["greeted"] = True
        return R.greeting()

    # ── 2. Command routing ────────────────────────────────────

    # Show product catalog
    if cmd == "menu":
        return R.product_catalog()

    # Add product to cart  →  "buy 1", "buy 2", ...
    if cmd.startswith("buy "):
        parts = cmd.split()
        if len(parts) == 2 and parts[1].isdigit():
            product = cart_add(session, int(parts[1]))
            if product:
                return R.added_to_cart(product, session)
        return R.product_not_found()

    # View cart
    if cmd == "cart":
        return R.cart_view(session)

    # Checkout — show order summary
    if cmd == "checkout":
        return R.checkout_summary(session)

    # Confirm mock payment
    if cmd == "pay":
        if session["stage"] == "checkout":
            return R.payment_confirmed(session)
        return R.not_in_checkout()

    # Clear cart
    if cmd == "clear":
        cart_clear(session)
        return R.cart_cleared()

    # ── 3. AI fallback for natural language ───────────────────
    products   = search(req.message)
    messages   = build_prompt(req.message, products, session["history"])
    ai_reply   = generate_response(messages)
    history_append(session, req.message, ai_reply)

    return {"text": ai_reply}


@app.get("/")
def root():
    return {"message": "AI Store is running!"}


@app.post("/webhook")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...)
):
    user_message = Body
    user_id = From

    # Get similar products from FAISS
    products = search(user_message)

    history = conversation_memory.get(user_id, [])

    messages = build_prompt(user_message, products, history)

    ai_response = generate_response(messages)

    # Store last interaction
    conversation_memory[user_id] = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": ai_response}
    ]

    print(conversation_memory)

    resp = MessagingResponse()
    resp.message(ai_response)
    print("AI response for user:", ai_response)

    # return PlainTextResponse(str(resp))
    return PlainTextResponse(str(resp), media_type="application/xml")

# ── Add these routes to your app/main.py ──
# Paste into main.py (after existing imports/routes)
# Also add: from fastapi.middleware.cors import CORSMiddleware
# and add CORS middleware so the admin panel can reach the API.

# ── CORS (allow admin panel running from file:// or localhost) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory prompt store (replace with DB/file for persistence) ──
_system_prompt = {"prompt": None}   # None = use default in prompt.py


# ── GET all products ──────────────────────────────────────────
@app.get("/admin/products")
def admin_get_products():
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return [
        {
            "id":          p.id,
            "name":        p.name,
            "description": p.description,
            "price":       p.price,
            "image_url":   p.image_url,
        }
        for p in products
    ]


# ── POST create product ───────────────────────────────────────
from pydantic import BaseModel
from typing import Optional

class ProductIn(BaseModel):
    name:        str
    description: Optional[str] = ""
    price:       float
    image_url:   Optional[str] = None

@app.post("/admin/products", status_code=201)
def admin_create_product(data: ProductIn):
    db = SessionLocal()
    p  = Product(
        name        = data.name,
        description = data.description,
        price       = data.price,
        image_url   = data.image_url,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    db.close()
    return {"id": p.id, "name": p.name}


# ── PUT update product ────────────────────────────────────────
@app.put("/admin/products/{product_id}")
def admin_update_product(product_id: int, data: ProductIn):
    db = SessionLocal()
    p  = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        db.close()
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    p.name        = data.name
    p.description = data.description
    p.price       = data.price
    p.image_url   = data.image_url
    db.commit()
    db.close()
    return {"ok": True}


# ── DELETE product ────────────────────────────────────────────
@app.delete("/admin/products/{product_id}")
def admin_delete_product(product_id: int):
    db = SessionLocal()
    p  = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        db.close()
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()
    db.close()
    return {"ok": True}


# ── GET system prompt ─────────────────────────────────────────
@app.get("/admin/prompt")
def admin_get_prompt():
    return {"prompt": _system_prompt["prompt"]}


# ── POST save system prompt ───────────────────────────────────
class PromptIn(BaseModel):
    prompt: str

@app.post("/admin/prompt")
def admin_save_prompt(data: PromptIn):
    _system_prompt["prompt"] = data.prompt
    # Update prompt.py at runtime so new chats use the new prompt.
    # For full persistence, write to a file or DB here.
    return {"ok": True}