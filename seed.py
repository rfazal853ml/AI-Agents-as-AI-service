from app.database import SessionLocal, Product, init_db
from app.vector_store import build_index

def seed_products():
    init_db()  # Ensure tables exist

    db = SessionLocal()

    # Optional: Clear existing data (safe for POC)
    db.query(Product).delete()
    db.commit()

    products = [
        Product(
            name="Running Shoes",
            description="Lightweight sports shoes for daily running and gym workouts",
            price=80
        ),
        Product(
            name="Smart Watch",
            description="Fitness tracking smartwatch with heart monitor and sleep tracking",
            price=120
        ),
        Product(
            name="Wireless Earbuds",
            description="Noise cancelling Bluetooth earbuds with long battery life",
            price=60
        )
    ]

    db.add_all(products)
    db.commit()
    db.close()

    print("✅ Products inserted successfully")


if __name__ == "__main__":
    seed_products()
    build_index()
    print("✅ FAISS index built successfully")