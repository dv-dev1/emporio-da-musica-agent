"""The only doors the model has to the store's data.

Every one of them returns plain data. The model decides which to call and how to
word the answer; it never gets to invent a price, a stock level or a deadline.
"""

import json
import re
import sqlite3
from datetime import date, datetime

from . import config, etl, policies, rules

MAX_RESULTS = 8


def _connection() -> sqlite3.Connection:
    connection = etl.connect()
    connection.create_function("searchable", 1, _searchable)
    return connection


def _searchable(text: str) -> str:
    from .text import searchable

    return searchable(text or "")


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _product_row(row: sqlite3.Row, with_payment: bool = False) -> dict:
    # A listing carries the short version of the payment terms and the details
    # carry the full breakdown. Leaving the terms out of the listing entirely
    # invites the model to recite the policy text and work the installments out
    # itself, which is how a R$599 guitar gets advertised at twelve payments.
    money = rules.payment_options(row["price_brl"], row["effective_price"],
                                  row["discount_percent"])
    product = {
        "product_id": row["product_id"],
        "name": row["name"],
        "category": row["category"],
        "list_price_brl": round(row["price_brl"], 2),
        "price_now_brl": round(row["effective_price"], 2),
        "in_stock": row["stock_quantity"] > 0,
        "stock_quantity": row["stock_quantity"],
        "status": row["status"],
        "pix_price_brl": money["pix"]["total"],
        "max_installments": money["credit"]["max_installments"],
        "installment_brl": money["credit"]["installment_value"],
    }
    if row["discount_percent"]:
        product["promotion"] = {
            "description": row["promotion"],
            "discount_percent": row["discount_percent"],
        }
    if with_payment:
        product["payment"] = money
    return product


def search_products(query: str = "", category: str = "", min_price: float | None = None,
                    max_price: float | None = None, only_in_stock: bool = True,
                    limit: int = 5) -> dict:
    from .text import search_terms

    clauses, params = [], []
    for term in search_terms(f"{query} {category}"):
        clauses.append("searchable(name || ' ' || COALESCE(description,'') || ' ' || "
                       "COALESCE(category,'')) LIKE ?")
        params.append(f"%{term}%")
    if min_price is not None:
        clauses.append("effective_price >= ?")
        params.append(min_price)
    if max_price is not None:
        clauses.append("effective_price <= ?")
        params.append(max_price)
    if only_in_stock:
        clauses.append("stock_quantity > 0 AND status = 'active'")

    where = " AND ".join(clauses) or "1 = 1"
    limit = max(1, min(int(limit or 5), MAX_RESULTS))

    with _connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM catalog WHERE {where} ORDER BY effective_price LIMIT ?",
            [*params, limit],
        ).fetchall()

    results = [_product_row(row) for row in rows]
    payload = {"count": len(results), "products": results}
    if not results:
        payload["note"] = (
            "nenhum produto do catálogo atende a esses filtros; não sugira itens "
            "que não apareçam aqui"
        )
    return payload


def get_product(product_id: int) -> dict:
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM catalog WHERE product_id = ?", [product_id]
        ).fetchone()
    if row is None:
        return {"error": "produto não encontrado no catálogo"}

    product = _product_row(row, with_payment=True)
    product["description"] = row["description"]
    try:
        product["specs"] = json.loads(row["specs"]) if row["specs"] else {}
    except json.JSONDecodeError:
        product["specs"] = {}
    if row["status"] == "discontinued":
        product["availability_note"] = "produto descontinuado, ofereça um sucessor equivalente"
    elif row["status"] == "coming_soon":
        product["availability_note"] = "produto ainda não lançado, sem previsão de venda"
    elif row["stock_quantity"] == 0:
        product["availability_note"] = (
            "sem estoque no momento, ofereça alternativas semelhantes"
        )
    return product


def get_order(order_id: int, customer_contact: str) -> dict:
    """Order lookup behind an identity check.

    The manual treats customer data as protected (9), and an order id alone is
    guessable, so the caller has to bring the phone or the e-mail on the order.
    """
    with _connection() as connection:
        row = connection.execute(
            """
            SELECT o.*, c.name AS customer_name, c.email, c.phone, c.city
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            WHERE o.order_id = ?
            """,
            [order_id],
        ).fetchone()
        if row is None:
            return {"error": "pedido não encontrado"}

        contact = (customer_contact or "").strip()
        matches_email = contact.lower() == (row["email"] or "").lower()
        matches_phone = bool(_digits(contact)) and _digits(contact) == _digits(row["phone"])
        if not (matches_email or matches_phone):
            return {
                "error": "não confere",
                "detail": "o contato informado não bate com o cadastro do pedido; "
                          "peça o e-mail ou o telefone do pedido antes de seguir",
            }

        items = connection.execute(
            """
            SELECT i.quantity, p.name, p.product_id
            FROM order_items i
            JOIN products p ON p.product_id = i.product_id
            WHERE i.order_id = ?
            """,
            [order_id],
        ).fetchall()

    today = config.today()
    order = {
        "order_id": row["order_id"],
        "customer_name": row["customer_name"],
        "order_date": row["order_date"],
        "status": row["status"],
        "total_brl": round(row["total_brl"], 2),
        "payment_method": row["payment_method"],
        "tracking_code": row["tracking_code"],
        "estimated_delivery": row["estimated_delivery"],
        "city": row["city"],
        "items": [dict(item) for item in items],
        "today": today.isoformat(),
    }
    if row["notes"]:
        order["notes"] = row["notes"]
    order["return_options"] = rules.assess_return(
        row["status"],
        _parse_date(row["order_date"]),
        today,
        _parse_date(row["estimated_delivery"]),
    )
    return order


def search_policies(question: str) -> dict:
    hits = policies.load().search(question, limit=3)
    if not hits:
        return {
            "matches": [],
            "note": "nada no manual cobre essa pergunta; não improvise uma política",
        }
    return {"matches": hits}


def store_info() -> dict:
    now = datetime.now()
    return {
        "name": config.STORE_NAME,
        "address": config.STORE_ADDRESS,
        "whatsapp": config.STORE_WHATSAPP,
        "phone": config.STORE_PHONE,
        "email": config.STORE_EMAIL,
        "opening_hours": {
            "segunda a sexta": "09:00 às 18:00",
            "sábado": "09:00 às 13:00",
            "domingo e feriados": "fechado",
        },
        "right_now": rules.store_status(now),
        "sells": "apenas instrumentos musicais",
        "does_not_sell": ["cordas", "palhetas", "cabos", "cases", "pedais", "amplificadores"],
    }


REGISTRY = {
    "search_products": search_products,
    "get_product": get_product,
    "get_order": get_order,
    "search_policies": search_policies,
    "store_info": store_info,
}

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Busca no catálogo da loja. Use sempre que o cliente perguntar o que "
                "existe, quanto custa ou se tem disponível. Preços de tabela e "
                "promocionais e condições de pagamento vêm prontos daqui."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termos do produto: tipo, marca ou modelo. "
                                       "Não coloque valores em reais aqui. Monte a "
                                       "busca só com o que o cliente pediu agora; "
                                       "não repita filtros de perguntas anteriores.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Guitarras, Baixos, Baterias e Percussão, "
                                       "Teclados e Pianos, Violões ou Ukuleles.",
                    },
                    "min_price": {"type": "number"},
                    "max_price": {"type": "number"},
                    "only_in_stock": {
                        "type": "boolean",
                        "description": "Padrão true. Só use false se o cliente quiser "
                                       "saber de itens indisponíveis.",
                    },
                    "limit": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Ficha completa de um produto: especificações, descrição, "
                           "estoque e situação no catálogo.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": (
                "Situação de um pedido, rastreio e quais prazos de troca ou devolução "
                "ainda estão abertos. Exige o e-mail ou o telefone do cliente para "
                "confirmar a identidade; peça ao cliente se ainda não tiver."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"},
                    "customer_contact": {
                        "type": "string",
                        "description": "E-mail ou telefone informado pelo cliente.",
                    },
                },
                "required": ["order_id", "customer_contact"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": (
                "Consulta o manual de políticas: trocas, devoluções, garantia, frete, "
                "formas de pagamento, promoções e privacidade. Pergunte com as palavras "
                "do cliente."
            ),
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_info",
            "description": "Endereço, contatos, horário de funcionamento e se a loja "
                           "está aberta agora.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def call(name: str, arguments: dict) -> dict:
    function = REGISTRY.get(name)
    if function is None:
        return {"error": f"ferramenta desconhecida: {name}"}
    try:
        return function(**arguments)
    except TypeError as error:
        return {"error": f"argumentos inválidos para {name}: {error}"}
    except Exception as error:  # a broken tool should not kill the conversation
        return {"error": f"falha ao executar {name}: {error}"}
