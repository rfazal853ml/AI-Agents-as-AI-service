from app.database import get_system_prompt


def build_prompt(user_message, products, history=None):
    if products:
        product_text = "\n".join([
            f"- **{p.name}** (${p.price}): {p.description}"
            for p in products
        ])
    else:
        product_text = "No products found matching your query."

    # Always fetch the latest prompt from DB so changes take effect immediately
    system_content = get_system_prompt()

    # Inject the available products into the prompt
    system_content += f"\n\nAvailable Products:\n{product_text}"

    messages = [
        {
            "role": "system",
            "content": system_content,
        }
    ]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    return messages