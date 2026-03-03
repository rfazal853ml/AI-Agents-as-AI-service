from app.database import SessionLocal, Product, init_db
from app.vector_store import build_index


def seed_products():
    init_db()

    db = SessionLocal()
    db.query(Product).delete()
    db.commit()

    products = [
        Product(
            name="Running Shoes",
            description="Lightweight sports shoes for daily running and gym workouts",
            price=80,
            image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"
        ),
        Product(
            name="Smart Watch",
            description="Fitness tracking smartwatch with heart monitor and sleep tracking",
            price=120,
            image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"
        ),
        Product(
            name="Wireless Earbuds",
            description="Noise cancelling Bluetooth earbuds with long battery life",
            price=60,
            image_url="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"
        ),
    ]

    db.add_all(products)
    db.commit()
    db.close()
    print("✅ Products seeded")


if __name__ == "__main__":
    seed_products()
    build_index()
    print("✅ FAISS index built")