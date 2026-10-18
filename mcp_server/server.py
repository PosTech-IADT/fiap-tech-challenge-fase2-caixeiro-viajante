import logging
import os
from pathlib import Path

from mcp.server import MCPServer
from route_engine.data import SEDE
from route_engine.maps import criar_mapa_rota, exibir_mapa_unidades
from route_engine.points import consultar_ponto, formatar_endereco, listar_pontos

from mcp_server.history import obter_metricas_relatorio, registrar_calculo_rota


logger = logging.getLogger(__name__)
mcp = MCPServer("fiap-route-mcp")


@mcp.tool()
def ping(mensagem: str = "MCP funcionando!") -> dict[str, str]:
    """Verifica se o servidor MCP esta respondendo."""
    return {
        "status": "ok",
        "mensagem": mensagem,
    }


@mcp.tool()
def listar_pontos_entrega(
    tipo: str | None = None,
    incluir_sede: bool = True,
) -> dict[str, object]:
    """Lista os pontos de entrega e seus enderecos completos.

    O filtro `tipo` e opcional e aceita textos parciais, como `Hospital`,
    `Cardiologico`, `UBS` ou `Maternidade`.
    """
    return listar_pontos(tipo=tipo, incluir_sede=incluir_sede)


@mcp.tool()
def consultar_ponto_entrega(nome: str) -> dict[str, object]:
    """Consulta um ponto pelo nome e retorna seu endereco completo."""
    return consultar_ponto(nome)


@mcp.tool()
def gerar_mapa_pontos() -> dict[str, object]:
    """Gera um mapa HTML interativo com a sede e os pontos de entrega."""
    caminho_saida = Path(
        os.getenv("MCP_MAP_OUTPUT", "/app/output/mapa_pontos.html")
    )
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    mapa = exibir_mapa_unidades()
    mapa.save(caminho_saida)

    return {
        "status": "ok",
        "mensagem": "Mapa dos pontos gerado com sucesso.",
        "arquivo": os.getenv(
            "MCP_MAP_PUBLIC_PATH",
            str(caminho_saida),
        ),
        "arquivo_container": str(caminho_saida),
        "total_pontos": listar_pontos()["total"],
    }


@mcp.tool()
def calcular_rota_entrega(
    pontos: list[str],
    partir_da_sede: bool,
) -> dict[str, object]:
    """Calcula a melhor rota pelas ruas entre os pontos informados.

    O engine atual sempre inicia a rota na sede. Antes de chamar esta tool,
    confirme com o usuario que a entrega deve partir da sede quando essa origem
    ainda nao estiver clara. Envie `partir_da_sede=true` apos a confirmacao.
    """
    caminho_mapa = Path(
        os.getenv("MCP_ROUTE_MAP_OUTPUT", "/app/output/mapa_rota.html")
    )
    caminho_mapa.parent.mkdir(parents=True, exist_ok=True)
    caminho_mapa.unlink(missing_ok=True)

    if not partir_da_sede:
        return {
            "status": "confirmacao_necessaria",
            "mensagem": (
                "O engine calcula rotas somente a partir da sede "
                f"{SEDE['nome']}. Confirme essa origem antes de continuar."
            ),
        }

    if not pontos:
        return {
            "status": "dados_insuficientes",
            "mensagem": "Informe pelo menos um ponto de entrega.",
        }

    try:
        from route_engine.engine import calcular_melhor_rota_entrega

        resultado = calcular_melhor_rota_entrega(pontos)
    except ValueError as erro:
        logger.warning("Dados invalidos para calcular a rota: %s", erro)
        return {
            "status": "dados_invalidos",
            "mensagem": str(erro),
        }
    except Exception as erro:
        logger.exception("Erro inesperado ao calcular a rota")
        return {
            "status": "erro_calculo",
            "mensagem": "Nao foi possivel calcular a rota informada.",
            "tipo_erro": type(erro).__name__,
            "detalhes": str(erro),
        }

    mapa_gerado = True
    aviso_mapa = None

    try:
        mapa = criar_mapa_rota(resultado)
        mapa.save(caminho_mapa)
    except Exception as erro:
        logger.exception("A rota foi calculada, mas o mapa nao foi gerado")
        mapa_gerado = False
        aviso_mapa = {
            "mensagem": "A rota foi calculada, mas o mapa nao pôde ser gerado.",
            "tipo_erro": type(erro).__name__,
            "detalhes": str(erro),
        }

    rota = []

    for ordem, ponto in enumerate(resultado["rota"], start=1):
        parada = {
            "ordem": ordem,
            "nome": ponto["nome"],
            "tipo": ponto["tipo"],
            "endereco": ponto["endereco"].copy(),
            "endereco_formatado": formatar_endereco(ponto["endereco"]),
            "coordenadas": {
                "latitude": ponto["coords"][0],
                "longitude": ponto["coords"][1],
            },
        }

        if ponto.get("situacao"):
            parada["situacao"] = ponto["situacao"]

        if ponto.get("observacao"):
            parada["observacao"] = ponto["observacao"]

        rota.append(parada)

    viagens = [
        {
            "numero": viagem["numero"],
            "carga_kg": round(viagem["carga_kg"], 2),
            "distancia_km": round(viagem["distancia_km"], 2),
            "paradas": [parada["nome"] for parada in viagem["paradas"]],
        }
        for viagem in resultado["viagens"]
    ]

    try:
        registro = registrar_calculo_rota(resultado, pontos)
    except OSError as erro:
        logger.warning("Nao foi possivel registrar o historico da rota: %s", erro)
        registro = None

    resposta = {
        "status": "ok",
        "origem": {
            "nome": resultado["sede"]["nome"],
            "tipo": resultado["sede"]["tipo"],
            "observacao": resultado["sede"].get("observacao"),
            "endereco": resultado["sede"]["endereco"].copy(),
            "endereco_formatado": formatar_endereco(
                resultado["sede"]["endereco"]
            ),
            "coordenadas": {
                "latitude": resultado["sede"]["coords"][0],
                "longitude": resultado["sede"]["coords"][1],
            },
        },
        "total_paradas": len(rota),
        "distancia_total_km": round(resultado["distancia_total_km"], 2),
        "rota": rota,
        "viagens": viagens,
        "restricoes": resultado["restricoes"],
        "comparativo_referencia": {
            chave: (
                round(valor, 2) if isinstance(valor, float) else valor
            )
            for chave, valor in resultado["comparativo_referencia"].items()
        },
        "mapa_gerado": mapa_gerado,
    }

    if registro:
        resposta["registro_historico"] = {
            "gerado_em": registro["gerado_em"],
            "status": "registrado",
        }

    if mapa_gerado:
        resposta["mapa"] = os.getenv(
            "MCP_ROUTE_MAP_PUBLIC_PATH",
            str(caminho_mapa),
        )
    else:
        resposta["aviso_mapa"] = aviso_mapa

    return resposta


@mcp.tool()
def gerar_relatorio_operacional(periodo: str) -> dict[str, object]:
    """Retorna metricas para um relatorio diario ou semanal de rotas.

    Use ``periodo='diario'`` ou ``periodo='semanal'``. Os dados retornados
    correspondem aos calculos de rota bem-sucedidos registrados pelo sistema.
    A LLM deve transformar essas metricas em um relatorio claro, sem inventar
    tempos, combustivel ou custos que nao estejam nos dados.
    """
    try:
        metricas = obter_metricas_relatorio(periodo)
    except ValueError as erro:
        return {"status": "dados_invalidos", "mensagem": str(erro)}

    return {
        "status": "ok",
        "metricas": metricas,
    }


if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8000")),
    )
