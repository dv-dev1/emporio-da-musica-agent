"""Streamlit front end. Thin on purpose: same Agent the CLI uses."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from emporio import etl, prompts  # noqa: E402
from emporio.agent import Agent, MissingApiKey  # noqa: E402

st.set_page_config(page_title="Empório da Música", page_icon="🎸")


@st.cache_resource
def start(session_id: str) -> Agent:
    etl.connect().close()
    return Agent(session_id=session_id)


st.title("Empório da Música")
st.caption("Atendimento — Rua 14 de Maio, 3200, Campo Grande/MS")

session_id = st.sidebar.text_input("Sessão", value="streamlit")
show_tools = st.sidebar.checkbox("Mostrar consultas do agente", value=True)

try:
    agent = start(session_id)
except MissingApiKey as error:
    st.error(str(error))
    st.stop()

if st.sidebar.button("Limpar conversa"):
    agent.history.clear()
    st.rerun()

history = agent.history.messages()
if not history:
    st.chat_message("assistant").write(prompts.opening_line())
for message in history:
    st.chat_message(message["role"]).write(message["content"])

if question := st.chat_input("Escreva sua mensagem"):
    st.chat_message("user").write(question)
    with st.chat_message("assistant"):
        with st.spinner("consultando..."):
            reply = agent.reply(question)
        st.write(reply.text)
        if show_tools and reply.tool_calls:
            with st.expander(f"{len(reply.tool_calls)} consulta(s)"):
                for call in reply.tool_calls:
                    st.write(f"**{call.name}**", call.arguments)
                    st.json(call.result, expanded=False)
