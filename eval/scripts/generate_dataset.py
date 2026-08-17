"""Generate the retrieval ground-truth dataset from the actual product catalog.

Usage:
    python -m eval.scripts.generate_dataset [output_path]
"""

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SRC = _REPO / "src"
for _p in (str(_SRC), str(_REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db.models import ProductDetails  # noqa: E402
from db.session import SessionLocal  # noqa: E402

DEFAULT_OUTPUT = _REPO / "eval" / "data" / "eval_queries.jsonl"


def _name_contains(row, token):
    return token.lower() in (row["name"] or "").lower()


def _attr(row, key, value):
    return (row.get("attributes") or {}).get(key) == value


def _price_at_most(row, value):
    return (row["price"] or float("inf")) <= value


QUERIES = [
    ("shampoo",                lambda r: _name_contains(r, "shampoo")),
    ("facial cleanser",        lambda r: r["subcategory"] == "Skincare" and _name_contains(r, "cleanser")),
    ("laptop",                 lambda r: r["subcategory"] == "Laptops"),
    ("smart tv",               lambda r: r["subcategory"] == "TVs"),
    ("sneakers",               lambda r: r["subcategory"] == "Shoes"),
    ("jeans",                  lambda r: r["subcategory"] == "Jeans"),
    ("cotton t-shirt",         lambda r: r["subcategory"] == "T-Shirts"),
    ("jacket",                 lambda r: r["subcategory"] == "Jackets"),
    ("blender",                lambda r: _name_contains(r, "blender")),
    ("kitchen appliances",     lambda r: r["subcategory"] == "Kitchen"),
    ("vacuum cleaner",         lambda r: _name_contains(r, "vacuum")),
    ("hair dryer",             lambda r: _name_contains(r, "hair dryer")),
    ("air fryer",              lambda r: _name_contains(r, "air fryer")),
    ("smartphone",             lambda r: r["subcategory"] == "Smartphones"),
    ("makeup",                 lambda r: r["subcategory"] == "Makeup"),
    ("dove products",          lambda r: r["brand"] == "Dove"),
    ("cerave skincare",        lambda r: r["brand"] == "CeraVe"),
    ("philips home appliances",lambda r: r["brand"] == "Philips" and r["category"] == "Home"),
    ("adidas",                 lambda r: r["brand"] == "Adidas"),
    ("baseus accessories",     lambda r: r["brand"] == "Baseus"),
    ("asus laptop",            lambda r: r["brand"] == "Asus" and r["subcategory"] == "Laptops"),
    ("apple laptop",           lambda r: r["brand"] == "Apple" and r["subcategory"] == "Laptops"),
    ("samsung smartphone",     lambda r: r["brand"] == "Samsung" and r["subcategory"] == "Smartphones"),
    ("wireless headphones",    lambda r: r["subcategory"] == "Headphones" and _attr(r, "wireless", "Bluetooth")),
    ("noise cancelling headphones", lambda r: r["subcategory"] == "Headphones" and _attr(r, "noise_cancelling", True)),
    ("wireless charger",       lambda r: r["subcategory"] == "Accessories" and (_name_contains(r, "wireless charger") or _attr(r, "type", "Wireless Charger"))),
    ("usb-c hub and cables",   lambda r: r["brand"] == "Baseus" and (_name_contains(r, "cable") or _name_contains(r, "hub"))),
    ("matte makeup",           lambda r: r["subcategory"] == "Makeup" and (_name_contains(r, "matte") or _attr(r, "finish", "Matte"))),
    ("75 inch tv",             lambda r: r["subcategory"] == "TVs" and _attr(r, "screen", "75 inch")),
    ("pantene shampoo for damaged hair", lambda r: r["brand"] == "Pantene" and _name_contains(r, "shampoo")),
    ("shampoo for dry hair",   lambda r: _name_contains(r, "shampoo") and _attr(r, "hair_type", "dry")),
    ("shampoo for oily hair",  lambda r: _name_contains(r, "shampoo") and _attr(r, "hair_type", "oily")),
    ("large shampoo bottle",   lambda r: _name_contains(r, "shampoo") and _attr(r, "volume", "500ml")),
    ("fragrance free facial cleanser", lambda r: r["subcategory"] == "Skincare" and _attr(r, "fragrance_free", True)),
    ("16gb ram laptop",        lambda r: r["subcategory"] == "Laptops" and _attr(r, "ram", "16GB")),
    ("cheap shampoo",          lambda r: _name_contains(r, "shampoo") and _price_at_most(r, 500)),
]


def load_catalog() -> dict[str, dict]:
    with SessionLocal() as session:
        products = session.query(ProductDetails).all()
    return {
        p.product_id: {
            "name": p.name,
            "category": p.category,
            "subcategory": p.subcategory,
            "brand": p.brand,
            "price": float(p.price) if p.price else None,
            "attributes": p.attributes or {},
        }
        for p in products
    }


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    catalog = load_catalog()
    print(f"Loaded {len(catalog)} products.")
    records = []
    for query, pred in QUERIES:
        ids = sorted(pid for pid, row in catalog.items() if pred(row))
        if not ids:
            print(f"WARNING: {query!r} matched nothing; skipping.")
            continue
        records.append({"query": query, "expected_ids": ids})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
