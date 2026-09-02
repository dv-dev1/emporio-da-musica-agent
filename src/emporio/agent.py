"""The conversation loop: model decides, tools answer, model writes."""

import json
from dataclasses import dataclass, field

from groq import Groq

from . import config, prompts, tools
from .memory import History


class MissingApiKey(RuntimeError):
    pass


@dataclass
class ToolCall:
    name: str
    arguments: dict
    result: dict


@dataclass
class Reply:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class Agent:
    def __init__(self, session_id: str = "cli", client: Groq | None = None,
                 model: str | None = None):
        self.model = model or config.GROQ_MODEL
        self.history = History(session_id)
        if client is not None:
            self.client = client
        elif config.GROQ_API_KEY:
            self.client = Groq(api_key=config.GROQ_API_KEY)
        else:
            raise MissingApiKey(
                "GROQ_API_KEY não configurada. Copie .env.example para .env e "
                "preencha a chave criada em https://console.groq.com/keys"
            )

    def reply(self, message: str) -> Reply:
        conversation = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            *self.history.messages(),
            {"role": "system", "content": prompts.TURN_REMINDER},
            {"role": "user", "content": message},
        ]
        used: list[ToolCall] = []

        for _ in range(config.MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation,
                tools=tools.SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
            )
            choice = response.choices[0].message
            if not choice.tool_calls:
                answer = (choice.content or "").strip()
                self.history.append("user", message)
                self.history.append("assistant", answer)
                return Reply(answer, used)

            conversation.append(choice.model_dump(exclude_none=True))
            for call in choice.tool_calls:
                arguments = _decode(call.function.arguments)
                result = tools.call(call.function.name, arguments)
                used.append(ToolCall(call.function.name, arguments, result))
                conversation.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        # Six rounds without an answer means the model is looping on tools.
        fallback = (
            "Desculpa, me embananei aqui na consulta. Pode repetir a pergunta de "
            "outro jeito? Se preferir, fala com a gente no (67) 3321-4500."
        )
        self.history.append("user", message)
        self.history.append("assistant", fallback)
        return Reply(fallback, used)


def _decode(raw: str) -> dict:
    """Tool arguments, with the junk keys dropped.

    For a tool that takes no arguments the model tends to emit {"": {}} rather
    than {}. Passing that through costs a failed call and a wasted round trip.
    """
    try:
        arguments = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    if not isinstance(arguments, dict):
        return {}
    return {key: value for key, value in arguments.items() if key.isidentifier()}
