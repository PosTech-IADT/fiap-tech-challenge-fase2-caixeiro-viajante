import asyncio
import json
import os
from pathlib import Path

from agents import Runner
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

from agent_factory import AgentsFactory
from mcp_manager import MCPManager


load_dotenv()

APP_TITLE = "Route Assistant"
POINTS_MAP_HTML_PATH = Path(
    os.getenv("POINTS_MAP_HTML_PATH", "/maps/mapa_pontos.html")
)
ROUTE_MAP_HTML_PATH = Path(
    os.getenv("ROUTE_MAP_HTML_PATH", "/maps/mapa_rota.html")
)

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1100px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stChatMessage"] {
            border: 1px solid rgba(128, 128, 128, 0.18);
            border-radius: 14px;
            padding: 0.35rem 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def extrair_texto_assistente(conteudo) -> str:
    if isinstance(conteudo, str):
        return conteudo

    textos = []
    for item in conteudo or []:
        if isinstance(item, dict) and item.get("text"):
            textos.append(item["text"])

    return "\n\n".join(textos)


def renderizar_historico() -> None:
    for mensagem in st.session_state.history:
        tipo = mensagem.get("role") or mensagem.get("type")

        if tipo == "user":
            with st.chat_message("user"):
                st.markdown(mensagem.get("content", ""))

        elif tipo == "assistant":
            texto = extrair_texto_assistente(mensagem.get("content"))
            if texto:
                with st.chat_message("assistant"):
                    st.markdown(texto)

        elif tipo == "function_call":
            with st.chat_message(name="tool"):
                st.markdown(f"Chamando tool **{mensagem.get('name', 'desconhecida')}**")
                with st.expander("Argumentos enviados"):
                    st.code(mensagem.get("arguments", "{}"), language="json")

        elif tipo == "function_call_output":
            saida = mensagem.get("output", "")
            with st.chat_message(name="tool"):
                with st.expander("Resposta da tool"):
                    try:
                        st.json(json.loads(saida) if isinstance(saida, str) else saida)
                    except (json.JSONDecodeError, TypeError):
                        st.code(str(saida))


def obter_mapa_solicitado() -> tuple[str, Path] | None:
    mapas_por_tool = {
        "gerar_mapa_pontos": ("Mapa dos pontos", POINTS_MAP_HTML_PATH),
        "calcular_rota_entrega": ("Mapa da rota", ROUTE_MAP_HTML_PATH),
    }

    for mensagem in reversed(st.session_state.history):
        tipo = mensagem.get("role") or mensagem.get("type")
        nome_tool = mensagem.get("name")

        if tipo == "function_call" and nome_tool in mapas_por_tool:
            return mapas_por_tool[nome_tool]

    return None


def renderizar_mapa() -> None:
    mapa_solicitado = obter_mapa_solicitado()
    if not mapa_solicitado:
        return

    titulo, caminho_mapa = mapa_solicitado
    if not caminho_mapa.exists():
        return

    st.subheader(titulo)
    components.html(
        caminho_mapa.read_text(encoding="utf-8"),
        height=650,
        scrolling=False,
    )


def obter_mensagem_carregamento(prompt: str) -> str:
    mensagens_recentes = st.session_state.history[-6:]
    contexto = " ".join(
        str(mensagem.get("content", ""))
        for mensagem in mensagens_recentes
    )
    texto = f"{contexto} {prompt}".casefold()

    termos_rota = (
        "rota",
        "trajeto",
        "caminho",
        "paradas",
        "partir da sede",
        "saindo da sede",
    )

    if any(termo in texto for termo in termos_rota):
        return "Calculando a melhor rota pelas ruas. Isso pode levar alguns instantes..."

    if "mapa" in texto:
        return "Gerando o mapa dos pontos..."

    return "Consultando o servidor MCP..."


async def resolver_chat() -> None:
    async with MCPManager.get_server() as server:
        st.session_state.agent.mcp_servers = [server]

        resultado = await Runner.run(
            starting_agent=st.session_state.agent,
            input=st.session_state.history,
            context=st.session_state.history,
        )

        st.session_state.agent = resultado.last_agent
        st.session_state.history = resultado.to_input_list()


if "agent" not in st.session_state:
    st.session_state.agent = AgentsFactory.create_agent()

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Route Assistant")
    st.caption("Conectado ao servidor MCP de pontos hospitalares.")

    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.agent = AgentsFactory.create_agent()
        st.session_state.history = []
        st.rerun()

st.title("Route Assistant")
st.caption("Consulte unidades de entrega e gere o mapa interativo dos pontos.")

if not os.getenv("OPENAI_API_KEY"):
    st.error("Configure a variavel OPENAI_API_KEY para utilizar o agente.")
    st.stop()

renderizar_historico()
renderizar_mapa()

prompt = st.chat_input(
    "Pergunte sobre os pontos ou solicite a geração do mapa..."
)

if prompt:
    mensagem_carregamento = obter_mensagem_carregamento(prompt)

    st.session_state.history.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner(mensagem_carregamento):
        try:
            asyncio.run(resolver_chat())
        except Exception as erro:
            st.error(f"Nao foi possivel concluir a solicitacao: {erro}")
        else:
            st.rerun()
