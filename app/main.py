from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from app.database import init_db
from app.vector_store import search
from app.prompt import build_prompt
from app.llm import generate_response

app = FastAPI()

init_db()

conversation_memory = {}

@app.get("/")
async def root():
    return {"message": "AI Agents As A Service is running!"}

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