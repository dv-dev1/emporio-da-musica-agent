# Devolução: dado do pedido cruzado com a política

Caso não trivial. Exige o pedido (data de recebimento) e o manual (prazo de 7 dias) na mesma resposta.

> Data de referência da conversa: 2026-03-25. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.


**Cliente:** me arrependi da compra, quero devolver o pedido 4

**Téo:** Oi! Para a gente abrir a solicitação de devolução do pedido 4, preciso confirmar seu cadastro. Pode me passar o e‑mail ou o telefone que usou na compra? 😊

**Cliente:** lucas.mendes@jmail.com

<sub>consultou `get_order`</sub>

**Téo:** Oi Lucas, tudo bem?  

Olha, o pedido 4 já foi entregue há mais de 90 dias (recebido em 22/12/2025). Nesse prazo o direito de arrependimento já expirou e a troca por preferência também não está mais disponível.  

Se ainda houver algum defeito de fabricação, a garantia legal de 90 dias já acabou, mas você pode acionar a garantia do fabricante; a gente pode intermediar, se precisar.

Quer que eu te passe o contato do fabricante ou tem outra coisa que eu possa ajudar?

**Cliente:** e se tiver defeito de fábrica, muda alguma coisa?

<sub>consultou `search_policies`</sub>

**Téo:** Se o produto tiver defeito de fabricação, a garantia legal de 90 dias cobre a troca. Como o seu pedido já foi entregue há mais de 90 dias, a garantia legal expirou, mas ainda dá pra acionar a garantia do fabricante (geralmente de 6 meses a 2 anos, dependendo da marca).  

A Empório da Música pode intermediar esse contato para você, caso precise. Quer que eu abra a solicitação de intermediação ou prefere falar direto com o fabricante?
