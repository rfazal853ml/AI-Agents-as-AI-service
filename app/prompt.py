from app.database import get_system_prompt


def build_intro_prompt(user_message: str, products) -> list:
    """
    Used when FAISS found matching products.
    Mistral only writes a short friendly 1-line intro.
    The actual product cards are rendered by responses.search_results().
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
    Used when FAISS found NO products — pure conversational fallback.
    Mistral answers freely using the system prompt from DB.
    """
    system_content = get_system_prompt()
    system_content += "\n\nNo matching products were found for this query."

    messages = [{"role": "system", "content": system_content}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})
    return messages