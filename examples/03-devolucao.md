# Devolução: dado do pedido cruzado com a política

Caso não trivial. Exige o pedido (data de recebimento) e o manual (prazo de 7 dias) na mesma resposta.

> Data de referência da conversa: 2026-03-25. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.


**Cliente:** me arrependi da compra, quero devolver o pedido 4

**Téo:** Oi! Entendo, vamos cuidar disso. 😊

Para eu localizar seu pedido 4, pode me passar o e‑mail ou o telefone cadastrado na compra? Assim o time responsável já registra a solicitação e retorna em até 24 horas úteis.

**Cliente:** lucas.mendes@jmail.com

<sub>consultou `get_order`</sub>

**Téo:** Lucas, vi que o pedido 4 já foi entregue há mais de 90 dias (recebido em 22/12/2025). Nesse prazo o direito de arrependimento já expirou e a troca por preferência também não está mais disponível.

Se houver algum defeito de fabricação, ainda dá pra acionar a garantia do fabricante (a loja pode intermediar). Caso contrário, infelizmente não conseguimos aceitar a devolução.

Posso te ajudar a abrir a solicitação de garantia ou a encontrar outro instrumento? É só falar!

**Cliente:** e se tiver defeito de fábrica, muda alguma coisa?

<sub>consultou `search_policies`</sub>

**Téo:** Boa, então se o seu instrumento tiver defeito de fábrica a gente tem duas opções:

1. **Até 30 dias da compra** – a Empório troca o produto sem custo.  
2. **Depois de 30 dias** – você aciona a garantia legal de 90 dias (ou a garantia do fabricante, que pode ser maior). A loja pode intermediar o processo, mas a solicitação tem que ser feita ao fabricante.

Se precisar abrir a solicitação de garantia, me avisa que eu te passo o passo a passo. Mais alguma coisa?
