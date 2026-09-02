# Devolução: dado do pedido cruzado com a política

Caso não trivial. Exige o pedido (data de recebimento) e o manual (prazo de 7 dias) na mesma resposta.

> Data de referência da conversa: 2026-03-25. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.


**Cliente:** me arrependi da compra, quero devolver o pedido 4

**Téo:** Oi! Para eu checar o seu pedido e te orientar sobre a devolução, preciso do e‑mail ou telefone cadastrado. Você pode me passar, por favor?

**Cliente:** lucas.mendes@jmail.com

<sub>consultou `get_order`</sub>

**Téo:** Oi Lucas, tudo bem? Pelo que eu vi, seu pedido #4 já foi entregue há mais de 90 dias. Nesse caso o direito de arrependimento (7 dias) e a troca por preferência não estão mais disponíveis. Você ainda pode acionar a garantia do fabricante (geralmente de 6 meses a 2 anos, conforme o certificado que vem com o violão), e a loja pode intermediar esse processo.

Se quiser seguir por esse caminho ou precisar de mais alguma coisa, me avisa!

**Cliente:** e se tiver defeito de fábrica, muda alguma coisa?

<sub>consultou `search_policies`</sub>

**Téo:** Exato, Lucas. Se o produto apresentar defeito de fabricação, a gente tem duas opções:

1. **Até 30 dias** da compra: a Empório troca o item sem custo pra você.  
2. **Depois de 30 dias**: você aciona a garantia do fabricante (geralmente de 6 meses a 2 anos). A loja pode intermediar o processo, mas a solicitação tem que ser feita ao fabricante.

Lembre‑se que a garantia não cobre danos por mau uso, quedas ou umidade. Precisa de mais alguma coisa?
