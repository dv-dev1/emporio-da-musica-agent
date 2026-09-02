# Devolução: dado do pedido cruzado com a política

Caso não trivial. Exige o pedido (data de recebimento) e o manual (prazo de 7 dias) na mesma resposta.

> Data de referência da conversa: 2026-03-25. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.


**Cliente:** me arrependi da compra, quero devolver o pedido 4

**Téo:** Oi! Para eu checar o seu pedido e te orientar sobre a devolução, preciso do e‑mail ou telefone cadastrado. Pode me passar, por favor?

**Cliente:** lucas.mendes@jmail.com

<sub>consultou `get_order`</sub>

**Téo:** Entendi, Lucas. Seu pedido 4 já foi entregue há mais de 90 dias, então o direito de arrependimento (7 dias) e a troca por preferência não estão mais disponíveis. Ainda resta a garantia do fabricante, que pode variar de 6 meses a 2 anos conforme a marca. A loja pode intermediar esse processo, mas o prazo depende do certificado que veio com o violão.

Se quiser seguir por aí, o time de suporte da Empório da Música vai analisar sua solicitação e retorna em até 24 horas úteis.

Precisa de mais alguma coisa?

**Cliente:** e se tiver defeito de fábrica, muda alguma coisa?

<sub>consultou `search_policies`</sub>

**Téo:** Boa, Lucas. Se o seu instrumento tem defeito de fábrica, a garantia legal de 90 dias cobre o problema. Além disso, a maioria das marcas oferece garantia própria (geralmente de 6 meses a 2 anos) que está no certificado que veio com o produto.

Como o seu pedido já foi entregue há mais de 90 dias, a garantia legal já expirou, mas você ainda pode acionar a garantia do fabricante. A Empório da Música pode intermediar esse processo; basta solicitar que o time responsável vai analisar e te responde em até 24 horas úteis.

Quer que eu passe mais alguma informação ou ajude com outra coisa?
