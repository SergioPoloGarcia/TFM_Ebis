import asyncio
import os
import sys
import nest_asyncio
from agent_framework import Agent
from agent_framework_ag_ui import AGUIChatClient

SERVER_URL = "http://127.0.0.1:8080/"

nest_asyncio.apply()

def create_agent(server_url: str) -> Agent:
    """Crear el cliente que consume el agente con el protocolo AG-UI."""
    chat_client = AGUIChatClient(endpoint=server_url)
    return Agent(
        name="ClientAgent",
        client=chat_client,
        instructions="You are a helpful assistant.",
    )

async def run_agent(agent: Agent, thread, message: str) -> str:
    """Enviar un mensaje y recopilar la respuesta en streaming."""
    response_parts = []
    async for update in agent.run(message, session=thread, stream=True):
        if update.text:
            response_parts.append(update.text)
    return "".join(response_parts)


def run_streamlit_app() -> None:
    """Abrir una interfaz de chat con Streamlit para el agente."""
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError("Instala Streamlit primero: pip install streamlit") from exc

    server_url = SERVER_URL

    st.set_page_config(page_title="AG-UI Chat", layout="wide")
    st.title("Chat de conocimiento - Speech Analytics")
    st.caption(f"TFM - Sergio Polo Garcia")

    # Iniciar agente y sesión si no existen
    if "agent" not in st.session_state:
        st.session_state.agent = create_agent(server_url)
        st.session_state.thread = st.session_state.agent.create_session()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Botón lateral para reiniciar la conversación
    with st.sidebar:
        st.write("### Opciones")
        if st.button("Limpiar conversación"):
            st.session_state.messages = []
            st.session_state.thread = st.session_state.agent.create_session()
            st.rerun()

    # Mostrar historial de mensajes
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada del usuario
    prompt = st.chat_input("Escribe tu mensaje...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            try:
                response = asyncio.run(
                    run_agent(st.session_state.agent, st.session_state.thread, prompt)
                )

            except Exception as exc:
                placeholder.error(f"Error: {exc}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {exc}"})
            else:
                if response:
                    placeholder.markdown(response)
                else:
                    placeholder.info("No se recibió respuesta.")
                st.session_state.messages.append(
                    {"role": "assistant", "content": response or "No se recibió respuesta."}
                )

def main() -> None:
    run_streamlit_app()


if __name__ == "__main__":
    main()