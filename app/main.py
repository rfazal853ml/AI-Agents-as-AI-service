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