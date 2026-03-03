# app/session.py
# In-memory store — good enough for POC.
# Replace with Redis for production.

from app.database import SessionLocal, Product

_sessions: dict = {}


def get_session(user_id: str) -> dict:
    if user_id not in _sessions:
        _sessions[user_id] = {
            "greeted": False,
            "stage":   "browsing",   # browsing | checkout | paid
            "cart":    [],           # [{"product": Product, "qty": int}]
            "history": [],           # LLM conversation history
        }
    return _sessions[user_id]


# ── Cart helpers ──────────────────────────────────────────────

def cart_add(session: dict, product_id: int) -> dict | None:
    """Add a product to cart. Returns the product or None if not found."""
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == product_id).first()
    db.close()
    if not product:
        return None

    for item in session["cart"]:
        if item["product"].id == product_id:
            item["qty"] += 1
            return product

    session["cart"].append({"product": product, "qty": 1})
    return product


def cart_remove(session: dict, product_id: int) -> bool:
    before = len(session["cart"])
    session["cart"] = [i for i in session["cart"] if i["product"].id != product_id]
    return len(session["cart"]) < before


def cart_clear(session: dict):
    session["cart"] = []
    session["stage"] = "browsing"


def cart_total(session: dict) -> float:
    return sum(i["product"].price * i["qty"] for i in session["cart"])


def cart_summary_text(session: dict) -> str:
    if not session["cart"]:
        return "Your cart is empty."
    lines = []
    for idx, item in enumerate(session["cart"], 1):
        p = item["product"]
        lines.append(f"{idx}. *{p.name}* × {item['qty']}  —  ${p.price * item['qty']:.2f}")
    lines.append(f"\n💰 *Total: ${cart_total(session):.2f}*")
    return "\n".join(lines)


# ── History helpers ───────────────────────────────────────────

def history_append(session: dict, user_msg: str, ai_msg: str):
    session["history"] += [
        {"role": "user",      "content": user_msg},
        {"role": "assistant", "content": ai_msg},
    ]
    # Keep last 10 turns to avoid token bloat
    session["history"] = session["history"][-20:]