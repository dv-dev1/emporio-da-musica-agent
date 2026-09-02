"""Checks the whole dataset against the rules, without a model and without a key.

The test suite pins the rules with chosen examples. This sweeps the actual data:
every catalogue row through the pricing rules, every order through the identity
gate and the return windows, every manual section through the index, and a list
of malformed arguments through the tool boundary. A chosen example proves a rule
is implemented; a sweep proves no row in the shipped data escapes it.

    python scripts/validate.py

Exits non-zero on the first failing check, so it can gate a release.
"""

import os
import sqlite3
import sys
from pathlib import Path

os.environ.setdefault("EMPORIO_TODAY", "2026-03-25")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from emporio import config, etl, policies, rules, tools  # noqa: E402

PIX_RATE = 0.05
BANDS = {3: 0.0, 6: 80.0, 12: 100.0}


def band_floor(installments: int) -> float:
    """The minimum installment the manual allows for that many installments (3.1)."""
    for ceiling, floor in sorted(BANDS.items()):
        if installments <= ceiling:
            return floor
    return BANDS[12]


def check_pricing(rows: list[sqlite3.Row]) -> list[str]:
    """Policy 3, 3.1 and 6.2 against every row the store would ever quote."""
    failures = []
    for row in rows:
        money = rules.payment_options(row["price_brl"], row["effective_price"],
                                      row["discount_percent"])
        listed, now = row["price_brl"], row["effective_price"]
        on_promotion = row["discount_percent"] is not None and now < listed

        if on_promotion:
            if money["pix"]["total"] != round(now, 2):
                failures.append(f"§6.2 produto {row['product_id']}: PIX acumulou sobre promoção")
            expected = round(listed * (1 - row["discount_percent"] / 100), 2)
            if abs(round(now, 2) - expected) > 0.02:
                failures.append(f"§6.1 produto {row['product_id']}: preço promocional "
                                f"{now} não bate com {row['discount_percent']}% de {listed}")
        elif abs(money["pix"]["total"] - round(listed * (1 - PIX_RATE), 2)) > 0.01:
            failures.append(f"§3 produto {row['product_id']}: PIX não deu 5%")

        count = money["credit"]["max_installments"]
        value = money["credit"]["installment_value"]
        if not 1 <= count <= 12:
            failures.append(f"§3.1 produto {row['product_id']}: {count} parcelas")
        if count > 1 and value < band_floor(count) - 0.01:
            failures.append(f"§3.1 produto {row['product_id']}: {count}x de {value} "
                            f"abaixo do piso {band_floor(count)}")
        if abs(value * count - now) > count * 0.01:
            failures.append(f"produto {row['product_id']}: parcela × {count} não fecha o total")
    return failures


def check_catalogue_tool(rows: list[sqlite3.Row]) -> list[str]:
    """The rules again, but read back through the door the model actually uses."""
    failures = []
    for row in rows:
        product = tools.get_product(row["product_id"])
        if "error" in product:
            failures.append(f"get_product({row['product_id']}): {product['error']}")
            continue
        if product["pix_price_brl"] != product["payment"]["pix"]["total"]:
            failures.append(f"produto {row['product_id']}: resumo e detalhe discordam no PIX")
        if product["in_stock"] != (row["stock_quantity"] > 0):
            failures.append(f"produto {row['product_id']}: in_stock não bate com o estoque")
        note, status = product["availability_note"], row["status"]
        if status == "discontinued" and "descontinuado" not in note:
            failures.append(f"§7.3 produto {row['product_id']}: descontinuado sem aviso")
        if status == "coming_soon" and "lançado" not in note:
            failures.append(f"§7.3 produto {row['product_id']}: pré-lançamento sem aviso")
        if status == "active" and row["stock_quantity"] == 0 and "sem estoque" not in note:
            failures.append(f"§7.3 produto {row['product_id']}: esgotado sem aviso")

        found = tools.search_products(query=row["name"], only_in_stock=False, limit=8)
        seen = {item["product_id"] for item in
                found.get("products", []) + found.get("unavailable", [])}
        if row["product_id"] not in seen:
            failures.append(f"produto {row['product_id']} não é achado pelo próprio nome")

    categories = {row["category"] for row in rows if row["category"]}
    for category in sorted(categories):
        found = tools.search_products(category=category, limit=8, only_in_stock=False)
        for product in found.get("products", []):
            if product["category"] != category:
                failures.append(f"categoria {category}: veio {product['name']} "
                                f"({product['category']})")
    return failures


def check_orders(connection: sqlite3.Connection) -> list[str]:
    """Policy 9 (identity before data) and 4.x (which window is still open)."""
    from datetime import date

    failures = []
    today = config.today()
    orders = connection.execute(
        "SELECT o.*, c.email, c.phone FROM orders o "
        "JOIN customers c ON c.customer_id = o.customer_id"
    ).fetchall()

    for order in orders:
        order_id = order["order_id"]
        wrong = ["", "   ", "ninguem@exemplo.com", "0000000000", "a", "67999999999"]
        for contact in wrong:
            if "error" not in tools.get_order(order_id, contact):
                failures.append(f"§9 pedido {order_id}: vazou com o contato {contact!r}")

        answer = tools.get_order(order_id, order["email"])
        if "error" in answer:
            failures.append(f"§9 pedido {order_id}: recusou o e-mail cadastrado")
            continue
        digits = "".join(ch for ch in (order["phone"] or "") if ch.isdigit())
        if digits:
            formatted = f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
            if "error" in tools.get_order(order_id, formatted):
                failures.append(f"§9 pedido {order_id}: recusou o telefone formatado")

        options = answer["return_options"]
        if not options.get("summary"):
            failures.append(f"pedido {order_id}: avaliação de devolução sem veredito")
        if order["status"].lower() != "delivered":
            continue

        placed = date.fromisoformat(order["order_date"])
        receipt = (date.fromisoformat(order["estimated_delivery"])
                   if order["estimated_delivery"] else placed)
        since_receipt = (today - receipt).days
        since_purchase = (today - placed).days
        open_paths = options.get("available_paths", [])
        for window, days, limit, clause in [
            ("arrependimento", since_receipt, rules.REGRET_DAYS, "§4.1"),
            ("defeito", since_purchase, rules.DEFECT_EXCHANGE_DAYS, "§4.2"),
            ("garantia legal", since_receipt, rules.LEGAL_WARRANTY_DAYS, "§8.1"),
        ]:
            offered = any(window in path for path in open_paths)
            if offered != (days <= limit):
                failures.append(f"{clause} pedido {order_id}: {days} dias, "
                                f"{'oferece' if offered else 'nega'} {window}")
    return failures


def check_manual() -> list[str]:
    """Every numbered section reaches the index, and answers to its own name."""
    failures = []
    index = policies.load()
    numbers = {section.number.rstrip(".") for section in index.sections}
    for required in ["1", "2", "3", "3.1", "4.1", "4.2", "4.3", "4.4", "5.1", "5.2",
                     "5.3", "6.1", "6.2", "7.1", "7.2", "7.3", "8.1", "8.2", "8.3", "9", "10"]:
        if required not in numbers:
            failures.append(f"§{required} não foi extraído do manual")
    for section in index.sections:
        hits = index.search(section.title, limit=3)
        if not any(hit["section"].startswith(section.number) for hit in hits):
            failures.append(f"§{section.number} não é recuperável pelo próprio título")
    for question, expected in [("posso devolver se me arrependi", "4.1"),
                               ("produto veio com defeito", "4.2"),
                               ("quanto tempo de garantia", "8"),
                               ("qual o frete para campo grande", "5.1"),
                               ("posso parcelar", "3"),
                               ("horário de funcionamento", "2"),
                               ("vocês guardam meus dados", "9")]:
        found = [hit["section"].split()[0] for hit in index.search(question, limit=3)]
        if not any(section.startswith(expected) for section in found):
            failures.append(f"'{question}' devia trazer §{expected}, trouxe {found}")
    return failures


def check_boundary() -> list[str]:
    """What a language model sends when it gets the schema wrong.

    None of these may raise: the loop hands the model an error dict and moves on,
    and an exception here would end the conversation instead.
    """
    attempts = [
        ("busca com injection", lambda: tools.search_products(query="'; DROP TABLE products; --")),
        ("categoria com injection", lambda: tools.search_products(category="x' OR '1'='1")),
        ("busca gigante", lambda: tools.search_products(query="a" * 5000)),
        ("busca com emoji", lambda: tools.search_products(query="🎸 violão ñ")),
        ("limite negativo", lambda: tools.search_products(query="violão", limit=-5)),
        ("limite absurdo", lambda: tools.search_products(query="violão", limit=999999)),
        ("limite em texto", lambda: tools.search_products(query="violão", limit="cinco")),
        ("faixa invertida", lambda: tools.search_products(min_price=5000, max_price=100)),
        ("preço negativo", lambda: tools.search_products(min_price=-100)),
        ("preço em texto", lambda: tools.search_products(max_price="mil reais")),
        ("booleano 'false'", lambda: tools.search_products(query="violão", only_in_stock="false")),
        ("booleano 'False'", lambda: tools.search_products(query="violão", only_in_stock="False")),
        ("booleano nulo", lambda: tools.search_products(query="violão", only_in_stock=None)),
        ("id em texto", lambda: tools.get_product("81")),
        ("id inválido", lambda: tools.get_product("abc")),
        ("id nulo", lambda: tools.get_product(None)),
        ("id negativo", lambda: tools.get_product(-1)),
        ("pedido decimal", lambda: tools.get_order(3.0, "x@x.com")),
        ("pedido em texto", lambda: tools.get_order("pedido três", "x@x.com")),
        ("contato nulo", lambda: tools.get_order(3, None)),
        ("contato vazio", lambda: tools.get_order(3, "")),
        ("política vazia", lambda: tools.search_policies("")),
        ("política nula", lambda: tools.search_policies(None)),
        ("política gigante", lambda: tools.search_policies("z" * 5000)),
        ("ferramenta inexistente", lambda: tools.call("drop_database", {})),
        ("argumento errado", lambda: tools.call("get_product", {"foo": 1})),
        ("argumento sobrando", lambda: tools.call("store_info", {"lixo": 1})),
        ("sem argumento nenhum", lambda: tools.call("search_products", {})),
    ]
    failures = []
    for name, attempt in attempts:
        try:
            answer = attempt()
        except Exception as error:  # noqa: BLE001 — that is the point of the check
            failures.append(f"{name}: levantou {type(error).__name__}: {error}")
            continue
        if not isinstance(answer, dict):
            failures.append(f"{name}: devolveu {type(answer).__name__}, não um dict")

    unavailable = tools.search_products(query="Giannini GF-3D Dreadnought Sunburst")
    if not unavailable.get("unavailable"):
        failures.append("§7.3: item sem estoque não veio marcado como indisponível")
    missing = tools.search_products(query="Fender Stratocaster Signature Zakk Wylde")
    if "não existe" not in missing.get("note", ""):
        failures.append("§7.3: item inexistente não foi declarado inexistente")
    return failures, len(attempts)


def check_sources() -> list[str]:
    """The CSVs and the manual are the store's, and must arrive unedited."""
    failures = []
    for name in ["products", "customers", "orders", "order_items", "promotions", "categories"]:
        path = config.DATA_DIR / f"{name}.csv"
        if not path.exists():
            failures.append(f"{name}.csv está faltando")
    if not config.POLICY_PDF.exists():
        failures.append("o manual de políticas está faltando")
    return failures


def main() -> int:
    print(f"data de referência: {config.today()}  (EMPORIO_TODAY)\n")
    with etl.session() as connection:
        catalogue = connection.execute("SELECT * FROM catalog").fetchall()
        order_count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        order_failures = check_orders(connection)

    boundary_failures, attempts = check_boundary()
    sections = len(policies.load().sections)

    checks = [
        (f"{len(catalogue)} produtos contra as regras de preço", check_pricing(catalogue)),
        (f"{len(catalogue)} produtos pela porta das ferramentas", check_catalogue_tool(catalogue)),
        (f"{order_count} pedidos: identidade e prazos", order_failures),
        (f"{sections} seções do manual: extração e busca", check_manual()),
        (f"{attempts} argumentos malformados no boundary", boundary_failures),
        ("arquivos de origem presentes", check_sources()),
    ]

    total = 0
    for label, failures in checks:
        print(f"  {'FALHOU' if failures else '  ok  '}  {label}")
        for failure in failures:
            print(f"            - {failure}")
        total += len(failures)

    print(f"\n{'FALHAS: ' + str(total) if total else 'nenhuma falha'}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
