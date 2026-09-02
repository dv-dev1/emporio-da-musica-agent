"""Business rules taken from the store policy manual.

They live in code, not in the prompt, because a wrong price or a wrong deadline
is the one mistake the manual explicitly calls out as legally risky (7.1).
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time

PIX_DISCOUNT = 0.05
FREE_SHIPPING_FROM = 500.0
METRO_SHIPPING_FEE = 35.0
COMBINED_PAYMENT_FROM = 2000.0

REGRET_DAYS = 7
DEFECT_EXCHANGE_DAYS = 30
LEGAL_WARRANTY_DAYS = 90

# Manual 3.1. The 3.0 table also states a flat R$100 minimum for credit, which
# contradicts these bands; the more specific rule wins. Read "sem valor mínimo
# de parcela (exceto abaixo de R$ 50,00)" as a R$50 floor on the installment.
INSTALLMENT_FLOORS = [(3, 50.0), (6, 80.0), (12, 100.0)]

OPENING_HOURS = {
    0: (time(9), time(18)),
    1: (time(9), time(18)),
    2: (time(9), time(18)),
    3: (time(9), time(18)),
    4: (time(9), time(18)),
    5: (time(9), time(13)),
}

SHIPPING_OUTSIDE_METRO = [
    {"carrier": "PAC (Correios)", "estimate_business_days": "5 a 12"},
    {"carrier": "SEDEX (Correios)", "estimate_business_days": "2 a 5"},
    {"carrier": "Jadlog (.package)", "estimate_business_days": "3 a 8"},
]


@dataclass
class Money:
    list_price: float
    effective_price: float
    discount_percent: float | None = None

    @property
    def on_promotion(self) -> bool:
        return self.discount_percent is not None and self.effective_price < self.list_price


def max_installments(amount: float) -> int:
    best = 1
    for ceiling, floor in INSTALLMENT_FLOORS:
        for count in range(best + 1, ceiling + 1):
            if amount / count >= floor:
                best = count
    return best


def payment_options(list_price: float, effective_price: float | None = None,
                    discount_percent: float | None = None) -> dict:
    money = Money(list_price, effective_price if effective_price is not None else list_price,
                  discount_percent)

    if money.on_promotion:
        pix_total = money.effective_price
        pix_note = "desconto PIX de 5% não acumula com preço promocional"
    else:
        pix_total = round(money.list_price * (1 - PIX_DISCOUNT), 2)
        pix_note = "5% de desconto à vista"

    installments = max_installments(money.effective_price)
    return {
        "list_price": round(money.list_price, 2),
        "price_now": round(money.effective_price, 2),
        "discount_percent": money.discount_percent,
        "pix": {"total": round(pix_total, 2), "note": pix_note},
        "debit": {"total": round(money.effective_price, 2)},
        "boleto": {"total": round(money.effective_price, 2),
                   "note": "compensação em até 3 dias úteis"},
        "credit": {
            "max_installments": installments,
            "installment_value": round(money.effective_price / installments, 2),
            "note": "sem juros",
        },
        "combined_payment_allowed": money.effective_price > COMBINED_PAYMENT_FROM,
    }


def shipping_quote(order_total: float, metro_campo_grande: bool = True) -> dict:
    if not metro_campo_grande:
        return {
            "area": "fora da região metropolitana de Campo Grande",
            "fee_brl": None,
            "note": "frete calculado pelo CEP, peso e dimensões; não estimável aqui",
            "carriers": SHIPPING_OUTSIDE_METRO,
        }
    free = order_total > FREE_SHIPPING_FROM
    return {
        "area": "região metropolitana de Campo Grande",
        "fee_brl": 0.0 if free else METRO_SHIPPING_FEE,
        "free_shipping": free,
        "estimate_business_days": "1 a 3",
        "note": "entrega por motoboy próprio, com contato telefônico antes",
    }


def store_status(now: datetime) -> dict:
    window = OPENING_HOURS.get(now.weekday())
    if window is None:
        return {"open": False, "reason": "domingo", "next_opening": "segunda-feira às 09:00"}
    opens, closes = window
    if opens <= now.time() < closes:
        return {"open": True, "closes_at": closes.strftime("%H:%M")}
    reason = "antes da abertura" if now.time() < opens else "após o fechamento"
    return {"open": False, "reason": reason, "opens_at": opens.strftime("%H:%M")}


@dataclass
class ReturnAssessment:
    order_status: str
    available_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    days_since_purchase: int | None = None
    days_since_receipt: int | None = None
    receipt_date: str | None = None
    receipt_date_is_estimated: bool = False
    conditions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {key: value for key, value in self.__dict__.items() if value not in (None, [])}


def assess_return(order_status: str, order_date: date, today: date,
                  estimated_delivery: date | None = None) -> dict:
    """Which return or exchange route is still open for an order.

    The dataset has no delivery confirmation date, so for delivered orders the
    estimated delivery is used as the receipt date and flagged as such.
    """
    status = (order_status or "").lower()
    assessment = ReturnAssessment(order_status=status)
    assessment.days_since_purchase = (today - order_date).days

    if status in {"pending", "confirmed"}:
        assessment.available_paths.append("cancelamento antes do envio")
        assessment.conditions.append("pedido ainda não despachado, cancelamento direto com a loja")
        return assessment.as_dict()

    if status == "cancelled":
        assessment.conditions.append("pedido já cancelado")
        return assessment.as_dict()

    if status == "shipped":
        assessment.available_paths.append("recusar o recebimento em caso de avaria")
        assessment.conditions.append(
            "prazos de troca e devolução só começam a contar depois do recebimento"
        )
        return assessment.as_dict()

    if status != "delivered":
        assessment.conditions.append("status do pedido não permite avaliar prazos")
        return assessment.as_dict()

    receipt = estimated_delivery or order_date
    assessment.receipt_date = receipt.isoformat()
    assessment.receipt_date_is_estimated = estimated_delivery is not None
    assessment.days_since_receipt = (today - receipt).days

    if assessment.days_since_receipt <= REGRET_DAYS:
        assessment.available_paths.append("direito de arrependimento (7 dias)")
        assessment.available_paths.append("troca por preferência (7 dias)")
        assessment.conditions.append("embalagem original, sem uso, com acessórios e manuais")
        assessment.conditions.append("frete de devolução por conta da loja no arrependimento")
        assessment.conditions.append("reembolso na forma original em até 10 dias úteis")
    else:
        assessment.blocked_paths.append("direito de arrependimento (7 dias)")
        assessment.blocked_paths.append("troca por preferência (7 dias)")

    if assessment.days_since_purchase <= DEFECT_EXCHANGE_DAYS:
        assessment.available_paths.append("troca por defeito de fabricação (30 dias)")
    else:
        assessment.blocked_paths.append("troca por defeito de fabricação (30 dias)")

    if assessment.days_since_receipt <= LEGAL_WARRANTY_DAYS:
        assessment.available_paths.append("garantia legal de 90 dias")
    else:
        assessment.blocked_paths.append("garantia legal de 90 dias")
        assessment.conditions.append(
            "fora da garantia legal, acionar a garantia do fabricante; a loja pode intermediar"
        )

    assessment.conditions.append(
        "não elegíveis: itens com setup sob encomenda, liquidação com aviso de venda final "
        "e boquilhas de sopro"
    )
    return assessment.as_dict()
