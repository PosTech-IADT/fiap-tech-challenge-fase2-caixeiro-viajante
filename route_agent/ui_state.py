from collections.abc import Collection


def preservar_quebras_linha_markdown(texto: str) -> str:
    """Converte quebras simples em quebras visuais do Markdown."""
    texto_normalizado = texto.replace("\r\n", "\n").replace("\r", "\n")
    return texto_normalizado.replace("\n", "  \n")


def obter_tool_mapa_da_ultima_interacao(
    historico: list[dict],
    nomes_tools_mapa: Collection[str],
) -> str | None:
    """Retorna a tool de mapa chamada desde a ultima mensagem do usuario."""
    for mensagem in reversed(historico):
        tipo = mensagem.get("role") or mensagem.get("type")

        if tipo == "user":
            break

        nome_tool = mensagem.get("name")
        if tipo == "function_call" and nome_tool in nomes_tools_mapa:
            return nome_tool

    return None
