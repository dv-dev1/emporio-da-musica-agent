"""The clauses of the store policy manual this agent implements.

The manual is the specification. Every clause listed here is expected to be
enforced somewhere in the code and pinned by at least one test marked with the
same number, which `tests/test_spec_coverage.py` checks and
`scripts/spec_matrix.py` turns into SPEC.md.

A clause that stops being covered fails the suite. A clause the agent does not
implement is absent from this list on purpose, not by accident.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Clause:
    section: str
    title: str
    requirement: str
    implemented_in: str


CLAUSES: tuple[Clause, ...] = (
    Clause(
        "1", "Sobre a Empório da Música",
        "A loja vende apenas instrumentos musicais e não comercializa acessórios "
        "como cordas, palhetas, cabos, cases, pedais ou amplificadores.",
        "tools.store_info, prompts.SYSTEM_PROMPT",
    ),
    Clause(
        "2", "Horário de Funcionamento",
        "Segunda a sexta das 09:00 às 18:00, sábado das 09:00 às 13:00, "
        "domingo e feriados fechado.",
        "rules.store_status",
    ),
    Clause(
        "3", "Formas de Pagamento",
        "PIX à vista com 5% de desconto sobre o preço de tabela; débito e boleto "
        "à vista; boleto compensa em até 3 dias úteis.",
        "rules.payment_options",
    ),
    Clause(
        "3.1", "Regras de Parcelamento",
        "Até 3x sem parcela mínima acima de R$50; de 4x a 6x parcela mínima de "
        "R$80; de 7x a 12x parcela mínima de R$100; combinação de formas de "
        "pagamento acima de R$2.000.",
        "rules.max_installments, rules.payment_options",
    ),
    Clause(
        "4.1", "Direito de Arrependimento",
        "Devolução em até 7 dias corridos após o recebimento, sem justificativa, "
        "com frete de devolução por conta da loja.",
        "rules.assess_return",
    ),
    Clause(
        "4.2", "Trocas por Defeito",
        "Troca por defeito de fabricação em até 30 dias corridos após a compra; "
        "depois disso, garantia do fabricante com intermediação da loja.",
        "rules.assess_return",
    ),
    Clause(
        "4.3", "Trocas por Preferência",
        "Troca por preferência em até 7 dias, sujeita a disponibilidade.",
        "rules.assess_return",
    ),
    Clause(
        "4.4", "Itens Não Elegíveis para Troca",
        "Itens com setup sob encomenda, liquidação com aviso de venda final e "
        "boquilhas de sopro não são elegíveis.",
        "rules.assess_return",
    ),
    Clause(
        "5.1", "Entregas na Região Metropolitana",
        "Frete grátis acima de R$500; abaixo disso taxa fixa de R$35; prazo de "
        "1 a 3 dias úteis.",
        "rules.shipping_quote",
    ),
    Clause(
        "5.2", "Entregas para Outras Cidades",
        "Fora da região metropolitana o frete depende de CEP, peso e dimensões e "
        "não é cotável pelo agente; informar transportadora e prazo estimado.",
        "rules.shipping_quote",
    ),
    Clause(
        "6.2", "Regras de Promoções",
        "Promoções não são cumulativas e o desconto PIX de 5% não se aplica "
        "sobre preços já promocionais; o preço promocional é sempre apresentado "
        "junto do preço original e do percentual.",
        "etl.CATALOG_VIEW, rules.payment_options",
    ),
    Clause(
        "7.1", "Diretrizes de Atendimento",
        "Nunca fornecer preço, estoque ou prazo sem consultar o sistema; "
        "redirecionar pedidos de acessórios.",
        "tools.SCHEMAS, prompts.SYSTEM_PROMPT",
    ),
    Clause(
        "7.3", "Situações Especiais",
        "Produto sem estoque, descontinuado ou não lançado nunca é confirmado "
        "como disponível; promoção vencida é informada com o preço atual.",
        "tools.search_products, tools.get_product",
    ),
    Clause(
        "8.1", "Garantia Legal",
        "Garantia legal de 90 dias contra defeitos de fabricação, contados do "
        "recebimento.",
        "rules.assess_return",
    ),
    Clause(
        "9", "Privacidade e Proteção de Dados",
        "Dados do cliente só são revelados a quem comprova ser o titular do "
        "pedido.",
        "tools.get_order",
    ),
)

BY_SECTION = {clause.section: clause for clause in CLAUSES}
