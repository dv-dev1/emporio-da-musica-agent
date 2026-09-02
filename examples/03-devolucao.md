# Devolução: dado do pedido cruzado com a política

Caso não trivial. Exige o pedido (data de recebimento) e o manual (prazo de 7 dias) na mesma resposta.

> Data de referência da conversa: 2026-03-25. O conjunto de dados é um retrato que
> termina em março de 2026, então `EMPORIO_TODAY` fixa o relógio para os prazos
> fazerem sentido.


**Cliente:** me arrependi da compra, quero devolver o pedido 4

**Téo:** Oi! Tudo bem? Para eu te ajudar com a devolução do pedido 4, preciso confirmar seu cadastro. Me passa o e‑mail ou o telefone que está registrado na compra?

**Cliente:** lucas.mendes@jmail.com

<sub>consultou `get_order`</sub>

**Téo:** Oi Lucas, tudo certo. Seu pedido 4 já foi entregue há mais de 90 dias (recebido em 22/12/2025). Nesse período o direito de arrependimento já expirou e não temos mais a opção de troca por preferência.

Se o violão estiver com algum defeito de fabricação, ainda dá pra acionar a garantia do fabricante – a gente pode intermediar, mas a garantia da loja não cobre mais.

Quer que eu abra um chamado pra você falar com o suporte do fabricante ou tem outra coisa que eu possa ajudar?

**Cliente:** e se tiver defeito de fábrica, muda alguma coisa?

<sub>consultou `search_policies`</sub>

**Téo:** Exato, Lucas. Se o violão apresentar defeito de fabricação, a garantia legal de 90 dias ainda vale. Como o seu pedido já passou desse prazo, a gente pode intermediar a garantia do fabricante (que costuma ser de 6 meses a 2 anos, dependendo da marca). 

Vou abrir um chamado pra você falar com o suporte do fabricante e encaminhar as informações do seu pedido. Preciso só confirmar o número do modelo do violão (ou o nome que consta na nota) para anexar tudo certinho. Você tem esse dado?
