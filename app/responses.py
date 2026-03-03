# app/responses.py
# Every function returns a dict that main.py sends back to bridge.js
# Shape:
#   { "text": str }                        — plain text reply
#   { "text": str, "image_url": str }      — single image + caption
#   { "messages": [ {text, image_url?} ] } — multiple messages (one per product)

import random, string
from datetime import datetime
from app.database import SessionLocal, Product
from app.session   import cart_summary_text, cart_total, cart_clear


# ── Greeting ─────────────────────────────────────────────────

def greeting() -> dict:
    return {"text": (
        "👋 *Welcome to AI Store!*\n\n"
        "I'm your personal shopping assistant 🤖\n\n"
        "Here's what you can do:\n"
        "🛍️ *menu*      — browse all products\n"
        "🛒 *cart*      — view your cart\n"
        "💳 *checkout*  — place your order\n"
        "🗑️ *clear*     — empty your cart\n\n"
        "Or just *ask me anything* about our products! 💬"
    )}


# ── Product catalog ───────────────────────────────────────────

def product_catalog() -> dict:
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()

    if not products:
        return {"text": "😔 No products available right now. Check back soon!"}

    msgs = []

    # Header message
    msgs.append({"text": "🛍️ *Our Products*\nHere's what we have for you today:\n"})

    # One message per product (image + caption)
    for p in products:
        caption = (
            f"*{p.name}*\n"
            f"💰 *${p.price:.2f}*\n\n"
            f"{p.description}\n\n"
            f"➡️ Reply *buy {p.id}* to add to cart"
        )
        msgs.append({"text": caption, "image_url": p.image_url})

    # Footer
    msgs.append({"text": "Type *cart* to view your basket 🛒"})

    return {"messages": msgs}


# ── Add to cart ───────────────────────────────────────────────

def added_to_cart(product, session: dict) -> dict:
    total_items = sum(i["qty"] for i in session["cart"])
    return {"text": (
        f"✅ *{product.name}* added to your cart!\n\n"
        f"🛒 Cart: {total_items} item(s)  |  💰 Total: ${cart_total(session):.2f}\n\n"
        f"Type *menu* to keep shopping or *cart* to review."
    )}


def product_not_found() -> dict:
    return {"text": "❌ Product not found. Type *menu* to see available products."}


# ── Cart view ─────────────────────────────────────────────────

def cart_view(session: dict) -> dict:
    if not session["cart"]:
        return {"text": (
            "🛒 Your cart is empty!\n\n"
            "Type *menu* to browse products."
        )}
    return {"text": (
        f"🛒 *Your Cart*\n\n"
        f"{cart_summary_text(session)}\n\n"
        f"Type *checkout* to proceed 💳\n"
        f"Type *clear* to empty your cart 🗑️"
    )}


# ── Checkout ──────────────────────────────────────────────────

def checkout_summary(session: dict) -> dict:
    if not session["cart"]:
        return {"text": "🛒 Your cart is empty! Type *menu* to add products first."}

    session["stage"] = "checkout"
    return {"text": (
        f"📦 *Order Summary*\n\n"
        f"{cart_summary_text(session)}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"To confirm, type *pay* ✅\n"
        f"To go back, type *cart* 🛒\n\n"
        f"_(This is a demo — no real charge will occur)_ 🔒"
    )}


# ── Mock payment ──────────────────────────────────────────────

def _order_id() -> str:
    date  = datetime.now().strftime("%Y%m%d")
    rand  = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"ORD-{date}-{rand}"


def payment_confirmed(session: dict) -> dict:
    order_id = _order_id()
    total    = cart_total(session)
    items    = session["cart"].copy()

    cart_clear(session)
    session["stage"] = "paid"

    item_lines = "\n".join(f"  • {i['product'].name} × {i['qty']}" for i in items)

    return {"text": (
        f"🎉 *Payment Successful!*\n\n"
        f"✅ *Order ID:* `{order_id}`\n"
        f"💰 *Amount paid:* ${total:.2f}\n\n"
        f"*Items ordered:*\n{item_lines}\n\n"
        f"📦 Estimated delivery: 3–5 business days\n\n"
        f"Thank you for shopping with us! 🙏\n"
        f"Type *menu* to continue shopping."
    )}


def not_in_checkout() -> dict:
    return {"text": "⚠️ Please type *checkout* first to review your order before paying."}


# ── Cart cleared ──────────────────────────────────────────────

def cart_cleared() -> dict:
    return {"text": "🗑️ Your cart has been cleared.\nType *menu* to start shopping again!"}


# ── Unknown command hint ──────────────────────────────────────

def unknown_command_hint() -> dict:
    return {"text": (
        "🤔 I didn't quite get that.\n\n"
        "Try one of these:\n"
        "• *menu* — browse products\n"
        "• *cart* — view cart\n"
        "• *checkout* — place order\n"
        "• *clear* — empty cart\n\n"
        "Or just ask me a question! 💬"
    )}