from datetime import date, datetime

import pytest

from emporio import rules


@pytest.mark.spec("3")
def test_pix_discount_applies_to_a_product_without_promotion():
    options = rules.payment_options(1000.0)
    assert options["pix"]["total"] == 950.0


@pytest.mark.spec("6.2")
def test_pix_discount_does_not_stack_on_a_promotional_price():
    options = rules.payment_options(549.0, effective_price=439.2, discount_percent=20.0)
    assert options["pix"]["total"] == 439.2
    assert options["price_now"] == 439.2


@pytest.mark.parametrize(
    "amount, expected",
    [
        (40.0, 1),
        (150.0, 3),
        (480.0, 6),
        (1200.0, 12),
        (599.9, 6),
    ],
)
@pytest.mark.spec("3.1")
def test_installment_bands(amount, expected):
    assert rules.max_installments(amount) == expected


@pytest.mark.spec("3.1")
def test_combined_payment_only_above_two_thousand():
    assert rules.payment_options(2500.0)["combined_payment_allowed"]
    assert not rules.payment_options(1999.0)["combined_payment_allowed"]


@pytest.mark.spec("5.1")
def test_free_shipping_threshold_in_the_metro_area():
    assert rules.shipping_quote(600.0)["fee_brl"] == 0.0
    assert rules.shipping_quote(499.0)["fee_brl"] == 35.0


@pytest.mark.spec("5.2")
def test_shipping_outside_the_metro_area_is_not_quotable():
    quote = rules.shipping_quote(600.0, metro_campo_grande=False)
    assert quote["fee_brl"] is None
    assert len(quote["carriers"]) == 3


@pytest.mark.spec("2")
def test_store_is_closed_on_sunday():
    assert rules.store_status(datetime(2026, 3, 22, 10, 0))["open"] is False


@pytest.mark.spec("2")
def test_store_closes_early_on_saturday():
    assert rules.store_status(datetime(2026, 3, 21, 11, 0))["open"] is True
    assert rules.store_status(datetime(2026, 3, 21, 14, 0))["open"] is False


@pytest.mark.spec("4.1")
def test_regret_window_open_right_after_delivery():
    assessment = rules.assess_return(
        "delivered", date(2026, 2, 3), date(2026, 2, 20), date(2026, 2, 17)
    )
    assert "direito de arrependimento (7 dias)" in assessment["available_paths"]
    assert assessment["receipt_date_is_estimated"] is True


@pytest.mark.spec("8.1")
def test_old_delivered_order_falls_back_to_the_manufacturer():
    assessment = rules.assess_return(
        "delivered", date(2025, 10, 15), date(2026, 3, 25), date(2025, 10, 25)
    )
    assert assessment["available_paths"] == []
    assert "garantia legal de 90 dias" in assessment["blocked_paths"]


@pytest.mark.spec("4.2")
def test_defect_exchange_counts_from_the_purchase_date():
    assessment = rules.assess_return(
        "delivered", date(2026, 3, 1), date(2026, 3, 25), date(2026, 3, 10)
    )
    assert "troca por defeito de fabricação (30 dias)" in assessment["available_paths"]
    assert "direito de arrependimento (7 dias)" in assessment["blocked_paths"]


@pytest.mark.spec("4.1")
def test_pending_order_can_still_be_cancelled():
    assessment = rules.assess_return("pending", date(2026, 3, 22), date(2026, 3, 25))
    assert assessment["available_paths"] == ["cancelamento antes do envio"]


@pytest.mark.spec("4.2")
def test_the_verdict_is_also_written_out_in_words():
    expired = rules.assess_return(
        "delivered", date(2025, 10, 15), date(2026, 3, 25), date(2025, 10, 25)
    )
    assert expired["summary"].startswith("nenhum prazo")

    open_window = rules.assess_return(
        "delivered", date(2026, 3, 20), date(2026, 3, 25), date(2026, 3, 22)
    )
    assert "ainda aberto: direito de arrependimento" in open_window["summary"]


@pytest.mark.spec("4.3")
def test_preference_exchange_shares_the_seven_day_window():
    inside = rules.assess_return(
        "delivered", date(2026, 3, 20), date(2026, 3, 25), date(2026, 3, 22)
    )
    assert "troca por preferência (7 dias)" in inside["available_paths"]

    outside = rules.assess_return(
        "delivered", date(2026, 2, 1), date(2026, 3, 25), date(2026, 2, 10)
    )
    assert "troca por preferência (7 dias)" in outside["blocked_paths"]


@pytest.mark.spec("4.4")
def test_the_items_that_cannot_be_exchanged_are_always_stated():
    assessment = rules.assess_return(
        "delivered", date(2026, 3, 20), date(2026, 3, 25), date(2026, 3, 22)
    )
    conditions = " ".join(assessment["conditions"])
    assert "venda final" in conditions
    assert "boquilhas" in conditions
