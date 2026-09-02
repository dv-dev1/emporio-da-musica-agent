import pytest

from emporio import tools


@pytest.mark.spec("6.2")
def test_price_filter_respects_the_promotional_price():
    """The Ohana lists at 549.00 and sells at 439.20, so a 450 ceiling keeps it."""
    found = tools.search_products(query="ukulele", max_price=450, limit=8)
    names = [product["name"] for product in found["products"]]
    assert "Ohana CK-20 Concert Natural" in names


@pytest.mark.spec("3.1")
def test_a_listing_already_answers_how_many_installments():
    """Without this the model recites the 12x ceiling at a guitar that supports six."""
    guitar = next(
        product
        for product in tools.search_products(query="violão", max_price=1000, limit=8)["products"]
        if product["name"].startswith("Yamaha C40")
    )
    assert guitar["max_installments"] == 6
    assert guitar["installment_brl"] == 99.98


def test_details_add_the_full_payment_breakdown():
    listing = tools.search_products(query="violão")["products"][0]
    assert "payment" not in listing
    assert "payment" in tools.get_product(listing["product_id"])


@pytest.mark.spec("7.3")
def test_search_never_returns_anything_out_of_stock_by_default():
    found = tools.search_products(query="", limit=8)
    assert all(product["in_stock"] for product in found["products"])


def test_a_product_the_store_never_had_is_reported_as_such():
    found = tools.search_products(query="saxofone")
    assert found["count"] == 0
    assert "unavailable" not in found
    assert "não existe no catálogo" in found["note"]


@pytest.mark.spec("7.3")
def test_a_product_that_only_ran_out_is_not_denied():
    """Policy 7.3: sold out is announced with an alternative, never denied."""
    found = tools.search_products(query="Giannini GF-3D Dreadnought")
    assert found["count"] == 0
    assert [p["name"] for p in found["unavailable"]] == ["Giannini GF-3D Dreadnought Sunburst"]
    assert found["unavailable"][0]["availability_note"].startswith("sem estoque")


def test_a_model_code_survives_the_query_parser():
    found = tools.search_products(query="ohana ck-20")
    assert found["products"][0]["name"] == "Ohana CK-20 Concert Natural"


def test_unknown_product_is_an_error_not_an_empty_shell():
    assert "error" in tools.get_product(9999)


@pytest.mark.spec("7.3")
def test_products_the_store_cannot_sell_carry_a_warning():
    """96 ran out of stock, 113 was discontinued, 130 has not launched yet."""
    for product_id in (96, 113, 130):
        assert tools.get_product(product_id)["availability_note"] != "disponível"


@pytest.mark.spec("7.3")
def test_those_products_never_show_up_in_a_normal_search():
    listing = tools.search_products(query="", only_in_stock=True, limit=8)
    assert all(product["status"] == "active" for product in listing["products"])
    assert all(product["stock_quantity"] > 0 for product in listing["products"])


@pytest.mark.spec("9")
def test_order_requires_a_matching_contact():
    assert tools.get_order(4, "quemquerseja@gmail.com")["error"] == "não confere"
    assert "status" in tools.get_order(4, "lucas.mendes@jmail.com")


@pytest.mark.spec("9")
def test_phone_matching_ignores_formatting():
    assert "status" in tools.get_order(4, "67998123456")


def test_order_answer_carries_the_return_assessment():
    order = tools.get_order(4, "lucas.mendes@jmail.com")
    assert order["return_options"]["available_paths"] == []


def test_missing_order_is_reported():
    assert "error" in tools.get_order(9999, "lucas.mendes@jmail.com")


@pytest.mark.spec("7.1")
def test_policy_search_returns_sections():
    matches = tools.search_policies("posso trocar se não gostei?")["matches"]
    assert matches and matches[0]["section"].startswith("4")


@pytest.mark.spec("1")
def test_store_info_lists_what_the_store_does_not_sell():
    assert "pedais" in tools.store_info()["does_not_sell"]


@pytest.mark.spec("2")
def test_open_right_now_follows_the_pinned_date(monkeypatch):
    """EMPORIO_TODAY has to reach store_info, or "open now" answers a different day.

    Order deadlines read the pinned date and this one used to read the wall
    clock, so a run pinned to a Sunday still reported the store open.
    """
    monkeypatch.setenv("EMPORIO_TODAY", "2026-03-22")
    assert tools.store_info()["right_now"]["reason"] == "domingo"
    monkeypatch.setenv("EMPORIO_TODAY", "2026-03-25")
    assert tools.store_info()["right_now"]["open"] in {True, False}


def test_a_category_never_returns_another_category():
    """A category filters its column, it is not one more word to search for.

    The Kala KA-B is a barítono ukulele whose description calls it "uma ponte
    entre o ukulele e o violão". While the category was folded into the free
    text, asking for violões offered it as one.
    """
    for category in ["Violões", "Ukuleles", "Guitarras", "Baixos",
                     "Teclados e Pianos", "Baterias e Percussão"]:
        found = tools.search_products(category=category, limit=8, only_in_stock=False)
        strays = [product["name"] for product in found["products"]
                  if product["category"] != category]
        assert not strays, f"{category} trouxe {strays}"


def test_a_category_is_read_however_the_model_spells_it():
    counts = {tools.search_products(category=spelling, limit=8)["count"]
              for spelling in ["Violões", "violões", "violao", "Violão", "VIOLAO"]}
    assert len(counts) == 1, f"grafias divergiram: {counts}"


def test_unknown_tool_does_not_raise():
    assert "error" in tools.call("consultar_horoscopo", {})


def test_bad_arguments_do_not_raise():
    assert "error" in tools.call("get_product", {"nome": "violão"})
