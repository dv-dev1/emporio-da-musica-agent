"""Runs the example conversations against the real agent and writes them down.

The transcripts in examples/ are generated, never handwritten, so what the repo
shows is what the agent actually answers.

    EMPORIO_TODAY=2026-03-25 python scripts/record_examples.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from emporio import config  # noqa: E402
from emporio.agent import Agent  # noqa: E402

CONVERSATIONS = [
    {
        "file": "01-catalogo-e-preco.md",
        "title": "Catálogo, faixa de preço e preço promocional",
        "about": "Consulta de catálogo com filtro de valor, seguida de uma pergunta "
                 "de preço em um produto que está em promoção.",
        "turns": [
            "oi! quais violões vocês têm até 1000 reais?",
            "e o yamaha c40, dá pra parcelar? quanto fica cada parcela?",
        ],
    },
    {
        "file": "02-pedido-e-rastreio.md",
        "title": "Status de pedido com verificação de identidade",
        "about": "O agente se recusa a falar do pedido antes de confirmar quem está "
                 "perguntando, e só então entrega status e rastreio.",
        "turns": [
            "quero saber do meu pedido 8",
            "é a ana carolina, meu email é anacarol.ferreira@coldmail.com",
        ],
    },
    {
        "file": "03-devolucao.md",
        "title": "Devolução: dado do pedido cruzado com a política",
        "about": "Caso não trivial. Exige o pedido (data de recebimento) e o manual "
                 "(prazo de 7 dias) na mesma resposta.",
        "turns": [
            "me arrependi da compra, quero devolver o pedido 4",
            "lucas.mendes@jmail.com",
            "e se tiver defeito de fábrica, muda alguma coisa?",
        ],
    },
    {
        "file": "04-informacoes-e-escopo.md",
        "title": "Informações da loja, acessório e pergunta fora do escopo",
        "about": "O que a loja é, o que ela não vende e o que não é assunto dela. "
                 "Abre com endereço e horário, que saem de `store_info` e não do "
                 "prompt, e fecha recusando um assunto que o modelo sabe responder.",
        "turns": [
            "qual o endereço de vocês? e que horas abre no sábado?",
            "vocês têm jogo de cordas e uma palheta pra guitarra?",
            "beleza. e qual a capital da Mongólia?",
        ],
    },
    {
        "file": "05-produto-indisponivel.md",
        "title": "Produto sem estoque e promoção vencida",
        "about": "O agente não confirma disponibilidade do que acabou, oferece "
                 "alternativa do catálogo e não promete um desconto que expirou. "
                 "Fecha com um ukulele que está de fato em promoção, para mostrar "
                 "o desconto aparecendo junto do preço de tabela.",
        "turns": [
            "queria o Giannini GF-3D Dreadnought Sunburst, tem?",
            "vi que teve black friday nele, ainda vale aquele desconto?",
            "e o ohana ck-20, tá com algum desconto?",
        ],
    },
]

HEADER = """# {title}

{about}

> Data de referência da conversa: {today}. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.

"""


def main() -> None:
    output = ROOT / "examples"
    output.mkdir(exist_ok=True)
    for index, conversation in enumerate(CONVERSATIONS, start=1):
        agent = Agent(session_id=f"exemplo-{index}")
        agent.history.clear()
        lines = [HEADER.format(today=config.today().isoformat(), **conversation)]
        for turn in conversation["turns"]:
            reply = agent.reply(turn)
            lines.append(f"**Cliente:** {turn}\n")
            if reply.tool_calls:
                consulted = ", ".join(
                    f"`{call.name}`" for call in reply.tool_calls
                )
                lines.append(f"<sub>consultou {consulted}</sub>\n")
            lines.append(f"**Téo:** {reply.text}\n")
        path = output / conversation["file"]
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"escrito {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
