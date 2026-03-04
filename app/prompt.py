from app.database import get_system_prompt, SessionLocal, Product


def _get_all_product_names() -> str:
    """Fetch current product names from DB to ground the AI."""
    db       = SessionLocal()
    products = db.query(Product).all()
    db.close()
    if not products:
        return "No products currently available."
    return "\n".join(f"- {p.name} (${p.price:.2f}): {p.description}" for p in products)


def build_intro_prompt(user_message: str, products) -> list:
    """
    Used when FAISS found matching products.
    Mistral only writes a short friendly 1-line intro.
    """
    product_names = ", ".join(p.name for p in products)

    return [
        {
            "role": "system",
            "content": (
                "You are a friendly WhatsApp sales assistant. "
                "Write ONE short, friendly, enthusiastic intro sentence (max 15 words) "
                "to introduce the products the user asked about. "
                "No bullet points. No product details. Just a warm opener. "
                "Use 1 relevant emoji at the start."
            ),
        },
        {
            "role": "user",
            "content": (
                f"The user asked: \"{user_message}\"\n"
                f"Matching products found: {product_names}\n"
                f"Write the intro line only."
            ),
        },
    ]


def build_prompt(user_message: str, products, history=None) -> list:
    """
    Used when FAISS found NO matching products.
    Mistral must ONLY reference real products from DB — never invent any.
    """
    system_content = get_system_prompt()
    all_products   = _get_all_product_names()

    system_content += f"""

IMPORTANT RULES — follow strictly:
1. You can ONLY mention products from the list below. Never invent, suggest, or describe any product not in this list.
2. If the user asks for something we don't carry, politely say we don't have it and suggest the closest real product from the list if one exists.
3. Never make up prices, names, descriptions, or product categories.
4. If nothing in the list is relevant, say we don't currently carry that item and invite them to type *menu* to see what's available.

Our current products:
{all_products}"""

    messages = [{"role": "system", "content": system_content}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})
    return messages