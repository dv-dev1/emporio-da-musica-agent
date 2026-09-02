import sqlite3
from contextlib import closing

import pytest

from emporio import config, etl


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    path = etl.build(tmp_path_factory.mktemp("etl") / "emporio.db", config.DATA_DIR)
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        yield connection


def test_every_csv_becomes_a_table(db):
    for table in etl.TABLES:
        assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] > 0


def test_numbers_are_stored_as_numbers_not_text(db):
    row = db.execute("SELECT price_brl, stock_quantity FROM products LIMIT 1").fetchone()
    assert isinstance(row["price_brl"], float)
    assert isinstance(row["stock_quantity"], int)


def test_blank_csv_cells_become_null(db):
    assert db.execute(
        "SELECT COUNT(*) FROM orders WHERE tracking_code IS NULL"
    ).fetchone()[0] > 0


def test_the_catalog_view_covers_every_product(db):
    products = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert db.execute("SELECT COUNT(*) FROM catalog").fetchone()[0] == products


def test_a_product_without_a_promotion_sells_at_list_price(db):
    row = db.execute(
        "SELECT price_brl, effective_price FROM catalog WHERE discount_percent IS NULL LIMIT 1"
    ).fetchone()
    assert row["effective_price"] == row["price_brl"]


def test_only_live_promotions_reach_the_catalog(db):
    live = {row["product_id"] for row in db.execute(
        "SELECT product_id FROM catalog WHERE discount_percent IS NOT NULL")}
    expected = {row["product_id"] for row in db.execute(
        "SELECT product_id FROM promotions WHERE is_active = 1")}
    assert live == expected


def test_a_discounted_price_is_never_above_the_list_price(db):
    assert db.execute(
        "SELECT COUNT(*) FROM catalog WHERE effective_price > price_brl"
    ).fetchone()[0] == 0


def test_rebuilding_is_idempotent(tmp_path):
    path = tmp_path / "emporio.db"
    etl.build(path, config.DATA_DIR)
    first = _count(path)
    etl.build(path, config.DATA_DIR)
    second = _count(path)
    assert first == second


def _count(path):
    with closing(sqlite3.connect(path)) as connection:
        return connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
