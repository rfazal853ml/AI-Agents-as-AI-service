from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./products.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String,  nullable=False)
    description = Column(Text)
    price       = Column(Float)
    image_url   = Column(String,  nullable=True)


class SystemPrompt(Base):
    __tablename__ = "system_prompt"

    id      = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)


DEFAULT_PROMPT = """You are a friendly WhatsApp sales assistant.
Use only the provided products to answer clearly and in a friendly way.
Respond using bullet points and emojis where appropriate.
Keep it concise and helpful.
Keep in mind WhatsApp formatting and character limits.

Ensure WhatsApp text formatting rules while responding:
- Use single asterisks * for bold like *bold*.
- Use underscores _ for italics like _italics_.
- Use tildes ~ for strikethrough like ~strikethrough~.
- Use triple backticks ``` for monospace like ```code```.

Be concise, persuasive, and helpful."""


def get_system_prompt() -> str:
    """Return the active system prompt from DB, seeding default if missing."""
    db = SessionLocal()
    row = db.query(SystemPrompt).first()
    if not row:
        row = SystemPrompt(content=DEFAULT_PROMPT)
        db.add(row)
        db.commit()
        db.refresh(row)
    content = row.content
    db.close()
    return content


def set_system_prompt(content: str):
    """Upsert the system prompt in DB."""
    db = SessionLocal()
    row = db.query(SystemPrompt).first()
    if row:
        row.content = content
    else:
        row = SystemPrompt(content=content)
        db.add(row)
    db.commit()
    db.close()


def init_db():
    Base.metadata.create_all(bind=engine)