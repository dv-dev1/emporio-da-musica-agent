"""Terminal chat with the store assistant."""

import argparse
import sys

from . import etl, prompts
from .agent import Agent, MissingApiKey


def main() -> int:
    parser = argparse.ArgumentParser(description="Atendimento da Empório da Música")
    parser.add_argument("--session", default="cli", help="identificador da conversa")
    parser.add_argument("--reset", action="store_true", help="apaga o histórico da sessão")
    parser.add_argument("--show-tools", action="store_true",
                        help="mostra as ferramentas usadas em cada resposta")
    parser.add_argument("--ask", help="faz uma única pergunta e sai")
    args = parser.parse_args()

    etl.connect().close()

    try:
        agent = Agent(session_id=args.session)
    except MissingApiKey as error:
        print(error, file=sys.stderr)
        return 1

    if args.reset:
        agent.history.clear()

    if args.ask:
        _answer(agent, args.ask, args.show_tools)
        return 0

    print(prompts.opening_line())
    print("(ctrl+c para sair)\n")
    while True:
        try:
            message = input("você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté mais!")
            return 0
        if not message:
            continue
        _answer(agent, message, args.show_tools)


def _answer(agent: Agent, message: str, show_tools: bool) -> None:
    reply = agent.reply(message)
    if show_tools:
        for call in reply.tool_calls:
            print(f"  · {call.name}({_short(call.arguments)})")
    print(f"\nTéo: {reply.text}\n")


def _short(arguments: dict) -> str:
    return ", ".join(f"{key}={value!r}" for key, value in arguments.items() if value != "")


if __name__ == "__main__":
    raise SystemExit(main())
