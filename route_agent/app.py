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
from ui_state import (
    obter_tool_mapa_da_ultima_interacao,
    preservar_quebras_linha_markdown,
)


load_dotenv()

APP_TITLE = "Assistente de Rota"
POINTS_MAP_HTML_PATH = Path(
    os.getenv("POINTS_MAP_HTML_PATH", "/maps/mapa_pontos.html")
)
ROUTE_MAP_HTML_PATH = Path(
    os.getenv("ROUTE_MAP_HTML_PATH", "/maps/mapa_rota.html")
)
MENSAGENS_TOOL = {
    "listar_pontos_entrega": "Listando os pontos de entrega cadastrados...",
    "consultar_ponto_entrega": "Consultando os dados do ponto de entrega...",
    "gerar_mapa_pontos": "Gerando o mapa dos pontos...",
    "otimizar_rota_genetica": "Calculando e otimizando a rota...",
    "gerar_relatorio_operacional": "Gerando o relatório operacional...",
    "ping": "Verificando a conexão com o servidor MCP...",
}

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
                st.markdown(
                    preservar_quebras_linha_markdown(
                        mensagem.get("content", "")
                    )
                )

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
        "otimizar_rota_genetica": ("Mapa da rota otimizada", ROUTE_MAP_HTML_PATH),
    }

    nome_tool = obter_tool_mapa_da_ultima_interacao(
        st.session_state.history,
        mapas_por_tool,
    )
    if nome_tool:
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


def obter_nome_tool_evento(evento) -> str | None:
    item = getattr(evento, "item", None)
    raw_item = getattr(item, "raw_item", None)

    return getattr(raw_item, "name", None) or getattr(item, "name", None)


def obter_mensagem_tool(nome_tool: str) -> str:
    return MENSAGENS_TOOL.get(nome_tool, f"Executando {nome_tool}...")


async def resolver_chat(status) -> None:
    async with MCPManager.get_server() as server:
        st.session_state.agent.mcp_servers = [server]

        resultado = Runner.run_streamed(
            starting_agent=st.session_state.agent,
            input=st.session_state.history,
            context=st.session_state.history,
        )

        async for evento in resultado.stream_events():
            if evento.type != "run_item_stream_event":
                continue

            if evento.name == "tool_called":
                nome_tool = obter_nome_tool_evento(evento)
                if nome_tool:
                    status.update(label=obter_mensagem_tool(nome_tool))
                else:
                    status.update(label="Executando uma ferramenta...")

            elif evento.name == "tool_output":
                status.update(label="Analisando o resultado da ferramenta...")

            elif evento.name == "message_output_created":
                status.update(label="Finalizando a resposta...")

        st.session_state.agent = resultado.last_agent
        st.session_state.history = resultado.to_input_list()


if "agent" not in st.session_state:
    st.session_state.agent = AgentsFactory.create_agent()

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header(APP_TITLE)
    st.caption("Conectado ao servidor MCP de pontos hospitalares.")

    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.agent = AgentsFactory.create_agent()
        st.session_state.history = []
        st.rerun()

st.title(APP_TITLE)
st.caption(
    "Consulte unidades, calcule rotas e gere instrucoes ou relatorios operacionais."
)

if not os.getenv("OPENAI_API_KEY"):
    st.error("Configure a variavel OPENAI_API_KEY para utilizar o agente.")
    st.stop()

renderizar_historico()
renderizar_mapa()

prompt = st.chat_input(
    "Pergunte sobre os pontos ou solicite a geração do mapa..."
)

if prompt:
    st.session_state.history.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(preservar_quebras_linha_markdown(prompt))

    with st.status("Analisando sua solicitação...", expanded=False) as status:
        try:
            asyncio.run(resolver_chat(status))
        except Exception as erro:
            status.update(
                label="Não foi possível concluir a solicitação.",
                state="error",
            )
            st.error(f"Nao foi possivel concluir a solicitacao: {erro}")
        else:
            status.update(label="Solicitação concluída.", state="complete")
            st.rerun()
