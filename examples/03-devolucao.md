# Devolução: dado do pedido cruzado com a política

Caso não trivial. Exige o pedido (data de recebimento) e o manual (prazo de 7 dias) na mesma resposta.

> Data de referência da conversa: 2026-03-25. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.


**Cliente:** me arrependi da compra, quero devolver o pedido 4

**Téo:** Oi! Para a gente abrir a solicitação de devolução do pedido 4, preciso confirmar seu cadastro. Pode me passar o e‑mail ou o telefone que está associado ao pedido? 😊

**Cliente:** lucas.mendes@jmail.com

<sub>consultou `get_order`</sub>

**Téo:** Oi Lucas, tudo bem? 

Vi aqui que o pedido 4 já foi entregue há **93 dias** (recebido em 22/12/2025). Nesse prazo já passou o direito de arrependimento de 7 dias e também o período de troca por preferência. 

Como ainda está dentro da garantia legal de 90 dias do fabricante, a gente pode intermediar a garantia, mas a devolução por arrependimento não está mais disponível.

Se quiser, posso abrir um contato com a equipe de suporte para você analisar a garantia do violão Giannini GF‑3D. Eles retornam em até 24 horas úteis.

Precisa de mais alguma coisa?

**Cliente:** e se tiver defeito de fábrica, muda alguma coisa?

<sub>consultou `search_policies`</sub>

**Téo:** Exato, Lucas. Se o violão tiver defeito de fábrica, a gente tem duas opções:

1. **Até 30 dias da compra** – a Empório pode trocar o produto direto, sem burocracia.  
2. **Depois de 30 dias** – você aciona a garantia legal de 90 dias (ou a garantia do fabricante, se houver). A gente pode intermediar o contato com a Giannini e o time volta em até 24 h úteis.

Então, se o defeito for de fabricação, ainda dá pra resolver. Quer que eu abra o chamado de garantia pra você?
