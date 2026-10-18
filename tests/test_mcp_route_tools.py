"""Testes das tools MCP sem dependencias externas ou chamadas de rede."""

from __future__ import annotations

import importlib

import pytest


class ServidorMcpFalso:
    """Substituto minimo para registrar as tools decoradas no modulo."""

    def __init__(self, _nome):
        self.tools = {}

    def tool(self):
        def decorar(funcao):
            self.tools[funcao.__name__] = funcao
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
        "distancia_total_km": 3.5,
        "restricoes": {"capacidade_veiculo_kg": 120.0},
        "comparativo_referencia": {
            "distancia_referencia_km": 5.0,
            "economia_distancia_km": 1.5,
            "economia_percentual": 30.0,
        },
    }


def test_registra_as_tools_de_rota_e_relatorio(servidor):
    assert {
        "calcular_rota_entrega",
        "gerar_relatorio_operacional",
    }.issubset(servidor.mcp.tools)


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
    assert resposta["comparativo_referencia"]["economia_distancia_km"] == 1.5
    assert resposta["registro_historico"]["status"] == "registrado"


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
