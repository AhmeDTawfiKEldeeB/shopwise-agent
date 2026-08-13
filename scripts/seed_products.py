import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.models import ProductDetails
from db.session import SessionLocal

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "shopwise_data.csv"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


def parse_row(row: dict) -> dict:
    return {
        "product_id": row["product_id"],
        "sku": row["sku"],
        "name": row["name"],
        "description": row["description"] or None,
        "category": row["category"] or None,
        "subcategory": row["subcategory"] or None,
        "brand": row["brand"] or None,
        "price": Decimal(row["price"]),
        "currency": row["currency"],
        "discount_percent": int(row["discount_percent"]),
        "stock_quantity": int(row["stock_quantity"]),
        "rating": float(row["rating"]) if row["rating"] else None,
        "review_count": int(row["review_count"]),
        "attributes": json.loads(row["attributes"]) if row["attributes"] else None,
        "image_url": row["image_url"] or None,
        "product_url": row["product_url"] or None,
        "is_active": parse_bool(row["is_active"]),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def seed() -> None:
    with open(DATA_FILE, encoding="utf-8") as f:
        rows = [parse_row(r) for r in csv.DictReader(f)]

    with SessionLocal() as session:
        stmt = pg_insert(ProductDetails).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ProductDetails.product_id],
            set_={
                "sku": stmt.excluded.sku,
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "category": stmt.excluded.category,
                "subcategory": stmt.excluded.subcategory,
                "brand": stmt.excluded.brand,
                "price": stmt.excluded.price,
                "currency": stmt.excluded.currency,
                "discount_percent": stmt.excluded.discount_percent,
                "stock_quantity": stmt.excluded.stock_quantity,
                "rating": stmt.excluded.rating,
                "review_count": stmt.excluded.review_count,
                "attributes": stmt.excluded.attributes,
                "image_url": stmt.excluded.image_url,
                "product_url": stmt.excluded.product_url,
                "is_active": stmt.excluded.is_active,
                "updated_at": func.now(),
            },
        )
        session.execute(stmt)
        session.commit()

    print(f"Seeded {len(rows)} products into product_details.")


if __name__ == "__main__":
    seed()
