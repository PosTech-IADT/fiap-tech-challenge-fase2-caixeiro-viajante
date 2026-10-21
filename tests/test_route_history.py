import json
from datetime import datetime

from mcp_server import history


def resultado_exemplo():
    return {
        "rota": [{"nome": "Hospital A"}, {"nome": "Hospital B"}],
        "total_viagens": 1,
        "distancia_total_km": 12.5,
        "comparativo_referencia": {
            "distancia_referencia_km": 15.0,
            "economia_distancia_km": 2.5,
        },
    }


def test_registra_calculo_em_arquivo_local(monkeypatch, tmp_path):
    arquivo = tmp_path / "historico.json"
    monkeypatch.setenv("MCP_ROUTE_HISTORY_OUTPUT", str(arquivo))

    registro = history.registrar_calculo_rota(
        resultado_exemplo(),
        ["Hospital A", "Hospital B"],
    )

    assert registro["total_paradas"] == 2
    assert json.loads(arquivo.read_text(encoding="utf-8"))[0]["total_viagens"] == 1


def test_agrega_metricas_diarias_e_pontos_frequentes(monkeypatch, tmp_path):
    arquivo = tmp_path / "historico.json"
    monkeypatch.setenv("MCP_ROUTE_HISTORY_OUTPUT", str(arquivo))
    agora = datetime.now(history.FUSO_HORARIO).isoformat()
    arquivo.write_text(
        json.dumps(
            [
                {
                    "gerado_em": agora,
                    "total_paradas": 2,
                    "total_viagens": 1,
                    "distancia_total_km": 12.5,
                    "distancia_referencia_km": 15.0,
                    "economia_distancia_km": 2.5,
                    "paradas": ["Hospital A", "Hospital B"],
                },
                {
                    "gerado_em": agora,
                    "total_paradas": 1,
                    "total_viagens": 1,
                    "distancia_total_km": 5.0,
                    "distancia_referencia_km": 6.0,
                    "economia_distancia_km": 1.0,
                    "paradas": ["Hospital A"],
                },
            ]
        ),
        encoding="utf-8",
    )

    metricas = history.obter_metricas_relatorio("diario")

    assert metricas["rotas_analisadas"] == 2
    assert metricas["distancia_total_km"] == 17.5
    assert metricas["economia_distancia_km"] == 3.5
    assert metricas["pontos_mais_frequentes"][0] == {
        "nome": "Hospital A",
        "ocorrencias": 2,
    }


def test_rejeita_periodo_invalido(monkeypatch, tmp_path):
    monkeypatch.setenv("MCP_ROUTE_HISTORY_OUTPUT", str(tmp_path / "historico.json"))

    try:
        history.obter_metricas_relatorio("mensal")
    except ValueError as erro:
        assert "periodo" in str(erro)
    else:
        raise AssertionError("O periodo invalido deveria gerar ValueError.")


def test_relatorio_sem_historico_retorna_metricas_zeradas(monkeypatch, tmp_path):
    monkeypatch.setenv("MCP_ROUTE_HISTORY_OUTPUT", str(tmp_path / "ausente.json"))

    metricas = history.obter_metricas_relatorio("semanal")

    assert metricas["rotas_analisadas"] == 0
    assert metricas["distancia_total_km"] == 0.0
    assert metricas["pontos_mais_frequentes"] == []
