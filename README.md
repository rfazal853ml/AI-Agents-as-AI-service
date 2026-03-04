# AI Agents as AI Service (Proof of Concept)

This repository contains a proof-of-concept implementation for running AI agents as a service. The project includes a Python-based backend with vector store capabilities, OpenAI integrations, and a WhatsApp bridge for messaging.

## 📁 Project Structure

```
ai-store/
│
├── app/
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy models (Product)
│   ├── llm.py               # Mistral client (chat + embeddings)
│   ├── main.py              # FastAPI app + all routes (chat, webhook, admin)
│   ├── prompt.py            # build_prompt() for LLM messages
│   ├── responses.py         # Structured response builders
│   ├── session.py           # In-memory session + cart helpers
│   └── vector_store.py      # FAISS index build + search
│
├── whatsapp-bridge/
│   ├── bridge.js            # WhatsApp Web.js client → calls /chat
│   ├── package.json
│   └── package-lock.json
│
├── admin/                   # ← NEW (the panel we just built)
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── seed.py                  # Seeds DB + rebuilds FAISS index
├── requirements.txt
├── .env                     # MISTRAL_API_KEY (gitignored)
├── .gitignore
├── products.db              # SQLite DB (auto-created)
├── faiss.index              # FAISS vector index (auto-created by seed.py)
└── faiss_meta.pkl           # FAISS metadata (auto-created by seed.py)
```

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd AI-Agents-as-AI-service
   ```

2. **Create Python environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate    # Windows
   pip install -r requirements.txt
   ```

3. **Seed the vector store**
   ```bash
   python seed.py
   ```

4. **Run the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Start WhatsApp bridge**
   ```bash
   cd whatsapp-bridge
   npm install
   node bridge.js
   ```

## 🧠 Core Components

- `app/vector_store.py` - Handles vector storage operations using FAISS.
- `app/llm.py` - Wrapper for language model interactions.
- `app/prompt.py` - Prompt templates and management.
- `app/database.py` - Database connectivity and session handling.
- `app/main.py` - FastAPI application entry point.
- `app/responses.py` - Response generation logic.
- `app/session.py` - Session management for agents.

## 💬 WhatsApp Integration
The `whatsapp-bridge` folder contains a simple Node.js service to relay messages between WhatsApp and the Python backend.

## 📄 Workflow & Cost Estimation
Detailed workflows and cost estimation documents are located in the `Workfow & Cost Estimation/` directory.

## ⚙️ Requirements
- Python 3.11+
- Node.js 18+
- FAISS
- OpenAI API key

## 📝 License
This project is provided as a proof of concept