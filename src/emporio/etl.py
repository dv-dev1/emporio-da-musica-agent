"""Loads the CSV snapshot into a local SQLite database."""

import csv
import sqlite3
from pathlib import Path

from . import config

SCHEMA = """
DROP VIEW IF EXISTS catalog;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS promotions;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT
);

CREATE TABLE products (
    product_id     INTEGER PRIMARY KEY,
    name           TEXT NOT NULL,
    category_id    INTEGER REFERENCES categories(category_id),
    price_brl      REAL NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    status         TEXT NOT NULL,
    description    TEXT,
    specs          TEXT,
    created_at     TEXT
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    phone       TEXT,
    email       TEXT,
    city        TEXT
);

CREATE TABLE orders (
    order_id           INTEGER PRIMARY KEY,
    customer_id        INTEGER REFERENCES customers(customer_id),
    order_date         TEXT NOT NULL,
    status             TEXT NOT NULL,
    total_brl          REAL NOT NULL,
    payment_method     TEXT,
    tracking_code      TEXT,
    estimated_delivery TEXT,
    notes              TEXT
);

CREATE TABLE order_items (
    order_id   INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity   INTEGER NOT NULL
);

CREATE TABLE promotions (
    promotion_id     INTEGER PRIMARY KEY,
    product_id       INTEGER REFERENCES products(product_id),
    discount_percent REAL NOT NULL,
    description      TEXT,
    is_active        INTEGER NOT NULL
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_promo_product ON promotions(product_id, is_active);
"""

# A product may in theory carry more than one live promotion. Policy 6.2 forbids
# stacking, so the best single discount wins.
CATALOG_VIEW = """
CREATE VIEW catalog AS
SELECT
    p.product_id,
    p.name,
    p.price_brl,
    p.stock_quantity,
    p.status,
    p.description,
    p.specs,
    c.name AS category,
    live.discount_percent,
    live.description AS promotion,
    ROUND(p.price_brl * (1 - COALESCE(live.discount_percent, 0) / 100.0), 2) AS effective_price
FROM products p
LEFT JOIN categories c ON c.category_id = p.category_id
LEFT JOIN (
    SELECT product_id, MAX(discount_percent) AS discount_percent, description
    FROM promotions
    WHERE is_active = 1
    GROUP BY product_id
) live ON live.product_id = p.product_id;
"""

TABLES = {
    "categories": ("categories.csv", ["category_id", "name", "description"]),
    "products": (
        "products.csv",
        ["product_id", "name", "category_id", "price_brl", "stock_quantity",
         "status", "description", "specs", "created_at"],
    ),
    "customers": ("customers.csv", ["customer_id", "name", "phone", "email", "city"]),
    "orders": (
        "orders.csv",
        ["order_id", "customer_id", "order_date", "status", "total_brl",
         "payment_method", "tracking_code", "estimated_delivery", "notes"],
    ),
    "order_items": ("order_items.csv", ["order_id", "product_id", "quantity"]),
    "promotions": (
        "promotions.csv",
        ["promotion_id", "product_id", "discount_percent", "description", "is_active"],
    ),
}

NUMERIC = {"price_brl", "total_brl", "discount_percent"}
INTEGER = {
    "category_id", "product_id", "customer_id", "order_id", "promotion_id",
    "stock_quantity", "quantity", "is_active",
}


def _coerce(column: str, raw: str):
    value = (raw or "").strip()
    if value == "":
        return None
    if column in INTEGER:
        return int(float(value))
    if column in NUMERIC:
        return float(value)
    return value


def _read(path: Path, columns: list[str]) -> list[tuple]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            tuple(_coerce(column, row.get(column, "")) for column in columns)
            for row in csv.DictReader(handle)
        ]


def build(db_path: Path | None = None, data_dir: Path | None = None) -> Path:
    db_path = db_path or config.DB_PATH
    data_dir = data_dir or config.DATA_DIR
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA)
        for table, (filename, columns) in TABLES.items():
            rows = _read(data_dir / filename, columns)
            placeholders = ", ".join("?" * len(columns))
            connection.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                rows,
            )
        connection.executescript(CATALOG_VIEW)
        connection.commit()
    finally:
        connection.close()
    return db_path


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or config.DB_PATH
    if not db_path.exists():
        build(db_path)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


if __name__ == "__main__":
    print(f"database written to {build()}")
