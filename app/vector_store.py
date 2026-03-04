import faiss
import numpy as np
import os
from app.database import SessionLocal, Product
from app.llm import get_embedding

# ── In-memory state ───────────────────────────────────────────
_index    = None   # faiss.IndexFlatL2
_meta     = []     # list of product_ids, parallel to index vectors


# ── Boot: build index from DB if not already loaded ───────────

def _build_text(product) -> str:
    return f"{product.name} {product.description or ''}"


def boot_index():
    """Called once on startup. Loads all products from DB into FAISS."""
    global _index, _meta

    db       = SessionLocal()
    products = db.query(Product).all()
    db.close()

    if not products:
        # Empty store — create a blank index (dimension fixed at first embed)
        _index = None
        _meta  = []
        print("⚠️  No products in DB — FAISS index is empty.")
        return

    vectors = []
    meta    = []
    for p in products:
        emb = get_embedding(_build_text(p))
        vectors.append(emb)
        meta.append(p.id)

    dim    = len(vectors[0])
    index  = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors, dtype="float32"))

    _index = index
    _meta  = meta
    print(f"✅ FAISS index ready — {len(meta)} product(s) loaded.")


# ── Add a single product to the live index ────────────────────

def index_add(product):
    """Insert one product into the in-memory FAISS index."""
    global _index, _meta

    emb = np.array([get_embedding(_build_text(product))], dtype="float32")

    if _index is None:
        dim    = emb.shape[1]
        _index = faiss.IndexFlatL2(dim)

    _index.add(emb)
    _meta.append(product.id)


# ── Remove a product from the live index ─────────────────────
# FAISS IndexFlatL2 doesn't support deletion, so we rebuild
# only the affected rows (fast for small catalogs).

def index_remove(product_id: int):
    """Remove one product and rebuild the index without it."""
    global _index, _meta

    if product_id not in _meta:
        return

    db       = SessionLocal()
    products = db.query(Product).filter(Product.id != product_id).all()
    db.close()

    if not products:
        _index = None
        _meta  = []
        return

    vectors = []
    meta    = []
    for p in products:
        emb = get_embedding(_build_text(p))
        vectors.append(emb)
        meta.append(p.id)

    dim   = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors, dtype="float32"))

    _index = index
    _meta  = meta


# ── Update = remove old vector + add new one ─────────────────

def index_update(product):
    """Re-embed a product after an edit."""
    index_remove(product.id)
    index_add(product)


# ── Semantic search ───────────────────────────────────────────

def search(query: str, k: int = 3):
    """Return up to k most relevant Product objects for a query."""
    if _index is None or len(_meta) == 0:
        return []

    k   = min(k, len(_meta))   # can't return more than we have
    qv  = np.array([get_embedding(query)], dtype="float32")
    _, indices = _index.search(qv, k)

    product_ids = [_meta[i] for i in indices[0] if i < len(_meta)]

    db       = SessionLocal()
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    db.close()
    return products