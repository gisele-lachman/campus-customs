"""Read-only access to the Campus Customs SQLite database."""

import json
import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
# CC_DB_PATH lets tests point a separate server at a scratch copy of the database.
DB_PATH = Path(os.getenv("CC_DB_PATH", DATA_DIR / "campus_customs.db"))
IMAGES_DIR = DATA_DIR / "products"

# Order sizes the way a shopper expects, not alphabetically.
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def connect() -> sqlite3.Connection:
    """Open the database in read-only mode so the app can never change it."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _product_from_row(row: sqlite3.Row) -> dict:
    product = dict(row)
    product["colors"] = json.loads(product["colors"])
    product["search_tags"] = json.loads(product["search_tags"])
    return product


def list_products() -> list[dict]:
    """All catalogue rows plus total units in stock and the sizes that are in stock."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
            FROM catalogue c
            LEFT JOIN inventory i ON i.product_id = c.product_id
            GROUP BY c.product_id
            ORDER BY c.name
            """
        ).fetchall()
        stocked = conn.execute("SELECT product_id, size FROM inventory WHERE quantity > 0").fetchall()
    in_stock: dict[str, set[str]] = {}
    for r in stocked:
        in_stock.setdefault(r["product_id"], set()).add(r["size"])
    products = [_product_from_row(r) for r in rows]
    for p in products:
        p["in_stock_sizes"] = [s for s in SIZE_ORDER if s in in_stock.get(p["product_id"], set())]
    return products


def get_product(product_id: str) -> dict | None:
    """One catalogue row plus its stock for every size, or None if not found."""
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    product = _product_from_row(row)
    by_size = {s["size"]: s["quantity"] for s in stock}
    product["inventory"] = [
        {"size": size, "quantity": by_size[size]} for size in SIZE_ORDER if size in by_size
    ]
    product["total_stock"] = sum(by_size.values())
    return product
