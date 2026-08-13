import json
import uuid

from infrastructure.embeddings import get_embedding_model
from infrastructure.vector_db import get_vector_store
from infrastructure.vector_db.interface import Distance, VectorRecord
from src.config.settings import get_vector_db_settings
from db.models import ProductDetails
from db.session import SessionLocal

PRODUCT_COLUMNS = [
    "name",
    "description",
    "category",
    "subcategory",
    "brand",
    "attributes",
]

BATCH_SIZE = 32


def build_document(product: ProductDetails) -> str:
    attributes = (
        json.dumps(product.attributes, ensure_ascii=False)
        if product.attributes
        else ""
    )
    parts = [
        product.name or "",
        product.description or "",
        product.category or "",
        product.subcategory or "",
        product.brand or "",
        attributes,
    ]
    return "\n".join(part for part in parts if part)


def to_payload(product: ProductDetails) -> dict:
    return {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "subcategory": product.subcategory,
        "brand": product.brand,
        "attributes": product.attributes,
        "price": float(product.price) if product.price else None,
        "currency": product.currency,
        "discount_percent": product.discount_percent,
        "stock_quantity": product.stock_quantity,
        "rating": product.rating,
        "review_count": product.review_count,
    }


def index_products() -> None:
    with SessionLocal() as session:
        products = session.query(ProductDetails).all()

    if not products:
        print("No products found in product_details. Run scripts/seed_products.py first.")
        return

    model = get_embedding_model()
    store = get_vector_store()

    collection = get_vector_db_settings().collection
    dimension = model.get_dimension()
    store.ensure_collection(collection, vector_size=dimension, distance=Distance.COSINE)

    docs = [build_document(product) for product in products]

    total = 0
    for start in range(0, len(products), BATCH_SIZE):
        chunk = products[start : start + BATCH_SIZE]
        vectors = model.embed_documents(docs[start : start + BATCH_SIZE])
        records = [
            VectorRecord(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, product.product_id),
                vector=vector,
                payload=to_payload(product),
            )
            for product, vector in zip(chunk, vectors)
        ]
        store.upsert_many(collection, records)
        total += len(records)
        print(f"  indexed {total}/{len(products)}")

    print(
        f"Done. {total} products indexed into qdrant collection "
        f"'{collection}' (dim={dimension})."
    )


if __name__ == "__main__":
    index_products()
