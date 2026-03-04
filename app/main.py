from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.messaging_response import MessagingResponse
from pydantic import BaseModel
from typing import Optional

from app.database import init_db, SessionLocal, Product, get_system_prompt, set_system_prompt
from app.vector_store import search, boot_index, index_add, index_remove, index_update
from app.prompt import build_prompt, build_intro_prompt
from app.llm import generate_response
from app.session import get_session, cart_add, cart_clear, history_append
from app import responses as R

app = FastAPI()

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────
init_db()
boot_index()

conversation_memory = {}


# ══════════════════════════════════════════════════════════════
# CHAT
# ══════════════════════════════════════════════════════════════

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
    if cmd == "menu":
        return R.product_catalog()

    if cmd.startswith("buy "):
        parts = cmd.split()
        if len(parts) == 2 and parts[1].isdigit():
            product = cart_add(session, int(parts[1]))
            if product:
                return R.added_to_cart(product, session)
        return R.product_not_found()

    if cmd == "cart":
        return R.cart_view(session)

    if cmd == "checkout":
        return R.checkout_summary(session)

    if cmd == "pay":
        if session["stage"] == "checkout":
            return R.payment_confirmed(session)
        return R.not_in_checkout()

    if cmd == "clear":
        cart_clear(session)
        return R.cart_cleared()

    # ── 3. Semantic search ────────────────────────────────────
    products = search(req.message)

    if products:
        # Products found → generate a short AI intro + rich product cards
        intro_messages = build_intro_prompt(req.message, products)
        ai_intro       = generate_response(intro_messages)
        history_append(session, req.message, ai_intro)
        return R.search_results(products, ai_intro)
    else:
        # No products found → pure conversational AI reply
        messages = build_prompt(req.message, [], session["history"])
        ai_reply = generate_response(messages)
        history_append(session, req.message, ai_reply)
        return {"text": ai_reply}


# ── WhatsApp webhook (Twilio) ─────────────────────────────────
@app.post("/webhook")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...)
):
    user_message = Body
    user_id      = From

    products = search(user_message)
    history  = conversation_memory.get(user_id, [])

    if products:
        intro_messages = build_intro_prompt(user_message, products)
        ai_intro       = generate_response(intro_messages)
        conversation_memory[user_id] = history + [
            {"role": "user",      "content": user_message},
            {"role": "assistant", "content": ai_intro},
        ]
        # Webhook is Twilio — can only send one message, so flatten to text
        lines = [ai_intro]
        for p in products:
            lines.append(f"\n*{p.name}* — ${p.price:.2f}\n{p.description}\nReply *buy {p.id}* to add to cart")
        lines.append("\nType *cart* to view your basket 🛒")
        resp = MessagingResponse()
        resp.message("\n".join(lines))
    else:
        messages    = build_prompt(user_message, [], history)
        ai_response = generate_response(messages)
        conversation_memory[user_id] = history + [
            {"role": "user",      "content": user_message},
            {"role": "assistant", "content": ai_response},
        ]
        resp = MessagingResponse()
        resp.message(ai_response)

    return PlainTextResponse(str(resp), media_type="application/xml")


@app.get("/")
def root():
    return {"message": "AI Store is running!"}


# ══════════════════════════════════════════════════════════════
# ADMIN — PRODUCTS
# ══════════════════════════════════════════════════════════════

class ProductIn(BaseModel):
    name:        str
    description: Optional[str] = ""
    price:       float
    image_url:   Optional[str] = None


@app.get("/admin/products")
def admin_get_products():
    db       = SessionLocal()
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
    index_add(p)
    return {"id": p.id, "name": p.name}


@app.put("/admin/products/{product_id}")
def admin_update_product(product_id: int, data: ProductIn):
    db = SessionLocal()
    p  = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        db.close()
        raise HTTPException(status_code=404, detail="Product not found")
    p.name        = data.name
    p.description = data.description
    p.price       = data.price
    p.image_url   = data.image_url
    db.commit()
    db.refresh(p)
    db.close()
    index_update(p)
    return {"ok": True}


@app.delete("/admin/products/{product_id}")
def admin_delete_product(product_id: int):
    db = SessionLocal()
    p  = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        db.close()
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()
    db.close()
    index_remove(product_id)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# ADMIN — SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════

class PromptIn(BaseModel):
    prompt: str


@app.get("/admin/prompt")
def admin_get_prompt():
    return {"prompt": get_system_prompt()}


@app.post("/admin/prompt")
def admin_save_prompt(data: PromptIn):
    if not data.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    set_system_prompt(data.prompt.strip())
    return {"ok": True}