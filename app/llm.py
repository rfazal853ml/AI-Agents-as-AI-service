import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def generate_response(messages):
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages
    )
    return response.choices[0].message.content


def get_embedding(text):
    response = client.embeddings.create(
        model="mistral-embed",
        inputs=[text]
    )
    return response.data[0].embedding