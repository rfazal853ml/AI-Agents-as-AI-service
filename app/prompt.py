def build_prompt(user_message, products, history=None):
    if products:
        product_text = "\n".join([
            f"- **{p.name}** (${p.price}): {p.description}"
            for p in products
        ])
    else:
        product_text = "No products found matching your query."

    messages = [
        {
            "role": "system",
            "content": f"""
You are a friendly WhatsApp sales assistant.
Use only the provided products to answer clearly and in a friendly way.
Respond using bullet points and emojis
where appropriate. Keep it concise and helpful.
keep in mind whatsapp formatting and character limits.
Ensure WhatsApp text formatting rules while responding:
- Use single asterisks * for bold like *bold*.
- Use underscores _ for italics like _italics_.
- Use tildes ~ for strikethrough like ~strikethrough~.
- Use triple backticks ``` for monospace like ```code```.


Available Products:
{product_text}

Be concise, persuasive, and helpful.
"""
        }
    ]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    return messages