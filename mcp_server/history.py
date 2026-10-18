"""Historico local e metricas para os relatorios operacionais de rotas."""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")
ARQUIVO_PADRAO = Path(__file__).resolve().parent / "output" / "historico_rotas.json"


def _caminho_historico() -> Path:
    return Path(os.getenv("MCP_ROUTE_HISTORY_OUTPUT", str(ARQUIVO_PADRAO)))


def _ler_historico(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []

    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    return conteudo if isinstance(conteudo, list) else []


def registrar_calculo_rota(resultado: dict, pontos_solicitados: list[str]) -> dict:
    """Registra metricas objetivas de uma rota calculada com sucesso."""
    caminho = _caminho_historico()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    comparativo = resultado["comparativo_referencia"]
    registro = {
        "gerado_em": datetime.now(FUSO_HORARIO).isoformat(),
        "pontos_solicitados": pontos_solicitados,
        "total_paradas": len(resultado["rota"]),
        "total_viagens": resultado["total_viagens"],
        "distancia_total_km": round(resultado["distancia_total_km"], 3),
        "distancia_referencia_km": round(
            comparativo["distancia_referencia_km"],
            3,
        ),
        "economia_distancia_km": round(
            comparativo["economia_distancia_km"],
            3,
        ),
        "paradas": [unidade["nome"] for unidade in resultado["rota"]],
    }

    historico = _ler_historico(caminho)
    historico.append(registro)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(
        json.dumps(historico, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporario.replace(caminho)
    return registro


def obter_metricas_relatorio(periodo: str) -> dict:
    """Agrega os calculos registrados no periodo solicitado."""
    periodos = {"diario": 1, "semanal": 7}
    periodo_normalizado = periodo.casefold().strip()
    if periodo_normalizado not in periodos:
        raise ValueError("O periodo deve ser 'diario' ou 'semanal'.")

    agora = datetime.now(FUSO_HORARIO)
    inicio = agora - timedelta(days=periodos[periodo_normalizado])
    registros = []
    for registro in _ler_historico(_caminho_historico()):
        try:
            data_registro = datetime.fromisoformat(registro["gerado_em"])
        except (KeyError, TypeError, ValueError):
            continue
        if data_registro >= inicio:
            registros.append(registro)

    total_rotas = len(registros)
    distancia_total = sum(float(item["distancia_total_km"]) for item in registros)
    distancia_referencia = sum(
        float(item["distancia_referencia_km"])
        for item in registros
    )
    economia = sum(float(item["economia_distancia_km"]) for item in registros)
    pontos_frequentes = Counter(
        parada
        for registro in registros
        for parada in registro.get("paradas", [])
    )

    return {
        "periodo": periodo_normalizado,
        "inicio": inicio.isoformat(),
        "fim": agora.isoformat(),
        "rotas_analisadas": total_rotas,
        "total_paradas": sum(int(item["total_paradas"]) for item in registros),
        "total_viagens": sum(int(item["total_viagens"]) for item in registros),
        "distancia_total_km": round(distancia_total, 2),
        "distancia_media_por_rota_km": round(
            distancia_total / total_rotas,
            2,
        ) if total_rotas else 0.0,
        "distancia_referencia_km": round(distancia_referencia, 2),
        "economia_distancia_km": round(economia, 2),
        "economia_percentual": round(
            economia / distancia_referencia * 100,
            2,
        ) if distancia_referencia else 0.0,
        "pontos_mais_frequentes": [
            {"nome": nome, "ocorrencias": ocorrencias}
            for nome, ocorrencias in pontos_frequentes.most_common(5)
        ],
        "observacao": (
            "As metricas comparam a rota otimizada com a ordem de paradas "
            "informada no calculo. O sistema nao registra tempo real, "
            "combustivel ou custo financeiro."
        ),
    }
