"""The conversation loop: model decides, tools answer, model writes."""

import json
import time
from dataclasses import dataclass, field

from groq import APIStatusError, Groq

from . import config, prompts, tools
from .memory import History


RETRIES = 3
TRANSIENT_STATUS = {429, 500, 502, 503}
# A 400 is normally the caller's fault, except this one: it means the model
# emitted something that is not a valid tool call, which the next sample fixes.
TRANSIENT_CODE = "tool_use_failed"


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
            choice = self._complete(conversation)
            if choice is None:
                break
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

        # Either six rounds without an answer, or the API kept refusing. Both end
        # the same way: say so and hand the customer a phone number.
        fallback = (
            "Desculpa, me embananei aqui na consulta. Pode repetir a pergunta de "
            "outro jeito? Se preferir, fala com a gente no (67) 3321-4500."
        )
        self.history.append("user", message)
        self.history.append("assistant", fallback)
        return Reply(fallback, used)

    def _complete(self, conversation: list[dict]):
        """One completion, retried on a transient API failure.

        gpt-oss sometimes emits its internal reasoning channel as a tool call
        named "commentary", which Groq rejects outright. It is sampling
        dependent, so the same request usually succeeds on the next attempt —
        and dropping the customer over it would be the worse outcome.

        Returns None once the retries are spent, so the caller can apologise.
        A bad key or a missing model is not transient and is raised as is,
        because hiding it behind a friendly message only wastes someone's
        afternoon.
        """
        for attempt in range(RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=conversation,
                    tools=tools.SCHEMAS,
                    tool_choice="auto",
                    temperature=0.3,
                )
                return response.choices[0].message
            except APIStatusError as error:
                if not _is_transient(error):
                    raise
                if attempt < RETRIES - 1:
                    time.sleep(0.6 * (attempt + 1))
        return None


def _is_transient(error: APIStatusError) -> bool:
    if error.status_code in TRANSIENT_STATUS:
        return True
    body = error.body if isinstance(error.body, dict) else {}
    return body.get("error", {}).get("code") == TRANSIENT_CODE


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
