"""Testes das tools MCP sem dependencias externas ou chamadas de rede."""

from __future__ import annotations

import importlib

import pytest


class ServidorMcpFalso:
    """Substituto minimo para registrar as tools decoradas no modulo."""

    def __init__(self, _nome):
        self.tools = {}
        self.tool_options = {}

    def tool(self, **opcoes):
        def decorar(funcao):
            self.tools[funcao.__name__] = funcao
            self.tool_options[funcao.__name__] = opcoes
            return funcao

        return decorar

    def run(self, **_kwargs):
        return None


@pytest.fixture
def servidor(monkeypatch):
    import mcp.server

    monkeypatch.setattr(mcp.server, "MCPServer", ServidorMcpFalso, raising=False)
    modulo = importlib.import_module("mcp_server.server")
    return importlib.reload(modulo)


def _endereco():
    return {
        "logradouro": "Rua Teste",
        "numero": "1",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "uf": "SP",
        "cep": "01000-000",
    }


def _resultado_rota():
    parada = {
        "nome": "Hospital A",
        "tipo": "Hospital",
        "endereco": _endereco(),
        "coords": (-23.55, -46.63),
        "prioridade": 1,
        "prioridade_rotulo": "alta",
        "demanda_kg": 20.0,
        "viagem": 1,
        "ordem_na_viagem": 1,
        "situacao": "desativado",
        "observacao": "Informacao interna",
    }
    return {
        "sede": {
            "nome": "Hub Logístico Saúde Centro",
            "tipo": "Sede de início das entregas",
            "endereco": _endereco(),
            "coords": (-23.55, -46.63),
        },
        "rota": [parada],
        "viagens": [
            {
                "numero": 1,
                "carga_kg": 20.0,
                "distancia_km": 3.5,
                "paradas": [parada],
            }
        ],
        "total_viagens": 1,
        "retorna_para_sede": True,
        "distancia_total_km": 3.5,
        "restricoes": {"capacidade_veiculo_kg": 120.0},
        "comparativo_referencia": {
            "distancia_referencia_km": 5.0,
            "economia_distancia_km": 1.5,
            "economia_percentual": 30.0,
        },
        "algoritmo": {
            "nome": "algoritmo_genetico",
            "geracoes_executadas": 20,
        },
    }


def test_registra_as_tools_de_rota_e_relatorio(servidor):
    assert {
        "calcular_rota_entrega",
        "otimizar_rota_genetica",
        "gerar_relatorio_operacional",
    }.issubset(servidor.mcp.tools)


def test_calcular_rota_entrega_esta_marcada_como_descontinuada(servidor):
    opcoes = servidor.mcp.tool_options["calcular_rota_entrega"]

    assert "DESCONTINUADA" in opcoes["title"]
    assert opcoes["meta"]["fiap/deprecated"] is True
    assert opcoes["meta"]["fiap/replacementTool"] == "otimizar_rota_genetica"


def test_calcular_rota_retorna_dados_para_instrucoes_e_registra_historico(
    servidor,
    monkeypatch,
    tmp_path,
):
    class MapaFalso:
        def save(self, caminho):
            caminho.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setenv("MCP_ROUTE_MAP_OUTPUT", str(tmp_path / "mapa.html"))
    monkeypatch.setattr(
        "route_engine.engine.calcular_melhor_rota_entrega",
        lambda _pontos: _resultado_rota(),
    )
    monkeypatch.setattr(servidor, "criar_mapa_rota", lambda _resultado: MapaFalso())
    monkeypatch.setattr(
        servidor,
        "registrar_calculo_rota",
        lambda _resultado, _pontos: {"gerado_em": "2026-10-18T12:00:00-03:00"},
    )

    resposta = servidor.calcular_rota_entrega(["Hospital A"], partir_da_sede=True)

    assert resposta["status"] == "ok"
    assert resposta["viagens"] == [
        {
            "numero": 1,
            "carga_kg": 20.0,
            "distancia_km": 3.5,
            "paradas": ["Hospital A"],
        }
    ]
    assert resposta["restricoes"]["capacidade_veiculo_kg"] == 120.0
    assert resposta["rota"][0]["prioridade"] == 1
    assert resposta["rota"][0]["prioridade_rotulo"] == "alta"
    assert resposta["rota"][0]["demanda_kg"] == 20.0
    assert "situacao" not in resposta["rota"][0]
    assert "observacao" not in resposta["rota"][0]
    assert resposta["total_viagens"] == 1
    assert resposta["algoritmo"]["nome"] == "algoritmo_genetico"
    assert resposta["aviso_descontinuacao"]["substituta"] == (
        "otimizar_rota_genetica"
    )
    assert resposta["comparativo_referencia"]["economia_distancia_km"] == 1.5
    assert resposta["registro_historico"]["status"] == "registrado"


def test_otimizar_rota_genetica_repassa_restricoes_ao_engine(
    servidor,
    monkeypatch,
    tmp_path,
):
    class MapaFalso:
        def save(self, caminho):
            caminho.write_text("<html></html>", encoding="utf-8")

    argumentos_recebidos = {}

    def calcular(pontos, **restricoes):
        argumentos_recebidos["pontos"] = pontos
        argumentos_recebidos["restricoes"] = restricoes
        return _resultado_rota()

    monkeypatch.setenv("MCP_ROUTE_MAP_OUTPUT", str(tmp_path / "mapa.html"))
    monkeypatch.setattr(
        "route_engine.engine.calcular_melhor_rota_entrega",
        calcular,
    )
    monkeypatch.setattr(servidor, "criar_mapa_rota", lambda _resultado: MapaFalso())
    monkeypatch.setattr(
        servidor,
        "registrar_calculo_rota",
        lambda _resultado, _pontos: {"gerado_em": "2026-10-18T12:00:00-03:00"},
    )

    resposta = servidor.otimizar_rota_genetica(
        ["Hospital A"],
        partir_da_sede=True,
        capacidade_kg=80.0,
        autonomia_km=30.0,
        prioridades={"Hospital A": 1},
        demandas_kg={"Hospital A": 20.0},
        configuracao_ga={"geracoes": 20},
    )

    assert resposta["status"] == "ok"
    assert argumentos_recebidos == {
        "pontos": ["Hospital A"],
        "restricoes": {
            "capacidade_kg": 80.0,
            "autonomia_km": 30.0,
            "prioridades": {"Hospital A": 1},
            "demandas_kg": {"Hospital A": 20.0},
            "configuracao_ga": {"geracoes": 20},
        },
    }


def test_relatorio_mcp_retorna_metricas_e_trata_periodo_invalido(
    servidor,
    monkeypatch,
):
    metricas = {"periodo": "diario", "rotas_analisadas": 2}
    monkeypatch.setattr(servidor, "obter_metricas_relatorio", lambda _periodo: metricas)

    assert servidor.gerar_relatorio_operacional("diario") == {
        "status": "ok",
        "metricas": metricas,
    }

    def periodo_invalido(_periodo):
        raise ValueError("O periodo deve ser 'diario' ou 'semanal'.")

    monkeypatch.setattr(servidor, "obter_metricas_relatorio", periodo_invalido)
    resposta_erro = servidor.gerar_relatorio_operacional("mensal")

    assert resposta_erro["status"] == "dados_invalidos"
    assert "periodo" in resposta_erro["mensagem"]
