import faiss
import numpy as np
from app.database import SessionLocal, Product
from app.llm import get_embedding

# ── In-memory state ───────────────────────────────────────────
_index = None   # faiss.IndexFlatL2
_meta  = []     # list of product_ids, parallel to index vectors

# ── Distance threshold ────────────────────────────────────────
# IndexFlatL2 uses squared Euclidean distance.
# Lower = more similar. Tune this value:
#   < 0.3  → very strict (only near-exact matches)
#   < 0.5  → balanced (recommended)
#   < 0.8  → loose (more results, less relevant)
DISTANCE_THRESHOLD = 0.5


def _build_text(product) -> str:
    return f"{product.name} {product.description or ''}"


# ── Boot: build index from DB on startup ──────────────────────

def boot_index():
    global _index, _meta

    db       = SessionLocal()
    products = db.query(Product).all()
    db.close()

    if not products:
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

    dim   = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors, dtype="float32"))

    _index = index
    _meta  = meta
    print(f"✅ FAISS index ready — {len(meta)} product(s) loaded.")


# ── Add a single product ──────────────────────────────────────

def index_add(product):
    global _index, _meta

    emb = np.array([get_embedding(_build_text(product))], dtype="float32")

    if _index is None:
        _index = faiss.IndexFlatL2(emb.shape[1])

    _index.add(emb)
    _meta.append(product.id)


# ── Remove a single product (rebuild without it) ──────────────

def index_remove(product_id: int):
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


# ── Update = remove + re-add ──────────────────────────────────

def index_update(product):
    index_remove(product.id)
    index_add(product)


# ── Semantic search with distance filtering ───────────────────

def search(query: str, k: int = 3):
    """
    Return only products whose distance is below DISTANCE_THRESHOLD.
    This prevents unrelated products from showing up just because
    they are the 'closest available' vectors.
    """
    if _index is None or len(_meta) == 0:
        return []

    k  = min(k, len(_meta))
    qv = np.array([get_embedding(query)], dtype="float32")

    distances, indices = _index.search(qv, k)

    matched_ids = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        if dist <= DISTANCE_THRESHOLD:
            matched_ids.append(_meta[idx])

    if not matched_ids:
        return []

    db       = SessionLocal()
    products = db.query(Product).filter(Product.id.in_(matched_ids)).all()
    db.close()
    return products