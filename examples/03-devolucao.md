# Devolução: dado do pedido cruzado com a política

Caso não trivial. Exige o pedido (data de recebimento) e o manual (prazo de 7 dias) na mesma resposta.

> Data de referência da conversa: 2026-03-25. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.


**Cliente:** me arrependi da compra, quero devolver o pedido 4

**Téo:** Oi! Para a gente verificar a situação do seu pedido 4 e iniciar a devolução, preciso do e‑mail ou do telefone cadastrado. Pode me passar, por favor?

**Cliente:** lucas.mendes@jmail.com

<sub>consultou `get_order`</sub>

**Téo:** Entendi, Lucas. Seu pedido 4 já foi entregue há mais de 90 dias, então o direito de arrependimento (7 dias) e a troca por preferência não estão mais disponíveis. Ainda resta a garantia do fabricante, que varia de 6 meses a 2 anos conforme a marca e está no certificado que acompanha o violão.

Se quiser acionar a garantia, a loja pode intermediar o processo. O time responsável vai entrar em contato com você em até 24 horas úteis para alinhar os próximos passos.

Posso ajudar em mais alguma coisa?

**Cliente:** e se tiver defeito de fábrica, muda alguma coisa?

<sub>consultou `search_policies`</sub>

**Téo:** Boa pergunta! Se o seu violão apresentar defeito de fábrica, a gente tem duas opções:

1. **Até 30 dias corridos da compra** – você pode solicitar a troca direto com a Empório da Música, sem custo.  
2. **Depois de 30 dias** – o defeito ainda é coberto pela garantia legal de 90 dias (Código de Defesa do Consumidor) e, se houver garantia do fabricante (geralmente de 6 meses a 2 anos), a loja pode intermediar o processo para você.

O time responsável vai analisar o caso e entra em contato em até 24 horas úteis para alinhar o próximo passo.

Precisa de mais alguma coisa?
