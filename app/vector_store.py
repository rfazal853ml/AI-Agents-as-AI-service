import faiss
import numpy as np
import pickle
from app.database import SessionLocal, Product
from app.llm import get_embedding

INDEX_FILE = "faiss.index"
META_FILE = "faiss_meta.pkl"


def build_index():
    db = SessionLocal()
    products = db.query(Product).all()

    vectors = []
    metadata = []

    for product in products:
        text = f"{product.name} {product.description}"
        embedding = get_embedding(text)
        vectors.append(embedding)
        metadata.append(product.id)

    dimension = len(vectors[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(vectors).astype("float32"))

    faiss.write_index(index, INDEX_FILE)

    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)


def search(query, k=3):
    index = faiss.read_index(INDEX_FILE)

    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)

    query_vector = np.array([get_embedding(query)]).astype("float32")
    distances, indices = index.search(query_vector, k)

    product_ids = [metadata[i] for i in indices[0]]

    db = SessionLocal()
    return db.query(Product).filter(Product.id.in_(product_ids)).all()