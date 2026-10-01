"""Interface Streamlit locale de l'assistant helpdesk."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.helpdesk_core import ask_agent, build_agent  # noqa: E402


st.set_page_config(page_title="Assistant helpdesk local", page_icon="🛠️")


@st.cache_resource
def get_agent():
    """Charge une seule fois les ressources lourdes partagées par l'application."""
    return build_agent()


def initialize_session() -> None:
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []


def main() -> None:
    initialize_session()
    st.title("Assistant helpdesk local")
    st.caption("Démonstration pédagogique : réponses locales avec tools et sources.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                st.caption("Sources : " + ", ".join(message["sources"]))

    question = st.chat_input("Posez une question sur les procédures ou les SLA")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche et génération locales…"):
            result = ask_agent(get_agent(), question, st.session_state.thread_id)
        st.markdown(result["answer"])
        if result["sources"]:
            st.caption("Sources : " + ", ".join(result["sources"]))
        if result["tool_calls"]:
            with st.expander("Outils utilisés"):
                st.json(result["tool_calls"])

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    })


if __name__ == "__main__":
    main()
