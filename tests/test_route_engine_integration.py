"""Testes de integracao interna do engine sem chamadas ao OpenStreetMap."""

import networkx as nx
import pytest

from route_engine import engine
from route_engine.data import SEDE


def criar_unidade(nome, prioridade, demanda_kg, coords):
    return {
        "nome": nome,
        "tipo": "Hospital",
        "coords": coords,
        "prioridade": prioridade,
        "demanda_kg": demanda_kg,
        "endereco": {
            "logradouro": "Rua Teste",
            "numero": "1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01000-000",
        },
    }


@pytest.fixture
def unidades():
    return [
        criar_unidade("A", 1, 30.0, (-23.51, -46.61)),
        criar_unidade("B", 2, 30.0, (-23.52, -46.62)),
        criar_unidade("C", 3, 10.0, (-23.53, -46.63)),
    ]


def matriz_distancias():
    nomes = (SEDE["nome"], "A", "B", "C")
    return {
        (origem, destino): 1_000.0
        for origem in nomes
        for destino in nomes
        if origem != destino
    }


def test_comprimento_escolhe_menor_aresta_paralela():
    grafo = nx.MultiDiGraph()
    grafo.add_edge(1, 2, length=120.0)
    grafo.add_edge(1, 2, length=80.0)
    grafo.add_edge(2, 3, length=50.0)

    assert engine.comprimento_caminho_m(grafo, [1, 2, 3]) == 130.0


def test_monta_coordenadas_separadas_por_viagem(unidades):
    grafo = nx.MultiDiGraph()
    coordenadas_nos = {
        0: (-23.50, -46.60),
        1: (-23.51, -46.61),
        2: (-23.52, -46.62),
    }
    for no, (latitude, longitude) in coordenadas_nos.items():
        grafo.add_node(no, y=latitude, x=longitude)

    caminhos = {
        (SEDE["nome"], "A"): [0, 1],
        ("A", SEDE["nome"]): [1, 0],
        (SEDE["nome"], "B"): [0, 2],
        ("B", SEDE["nome"]): [2, 0],
    }
    unidades_por_nome = {item["nome"]: item for item in unidades}

    coordenadas, pontos, por_viagem = engine._montar_coordenadas_percurso(
        [["A"], ["B"]],
        unidades_por_nome,
        caminhos,
        grafo,
    )

    assert len(por_viagem) == 2
    assert por_viagem[0]["coordenadas"] == [
        coordenadas_nos[0],
        coordenadas_nos[1],
        coordenadas_nos[0],
    ]
    assert [ponto["nome"] for ponto in pontos] == [
        SEDE["nome"],
        "A",
        SEDE["nome"],
        SEDE["nome"],
        "B",
        SEDE["nome"],
    ]
    assert coordenadas


def test_engine_entrega_resultado_completo_sem_rede(monkeypatch, unidades):
    monkeypatch.setattr(engine, "preparar_unidades", lambda: unidades)
    monkeypatch.setattr(engine, "montar_grafo_por_ruas", lambda _pontos: object())
    monkeypatch.setattr(
        engine,
        "_calcular_matriz_rotas",
        lambda _grafo, _pontos: (matriz_distancias(), {}),
    )

    def coordenadas_simuladas(viagens, _unidades, _caminhos, _grafo):
        por_viagem = [
            {"numero": numero, "coordenadas": [(numero, numero)]}
            for numero, _ in enumerate(viagens, start=1)
        ]
        return [(1, 1)], [], por_viagem

    monkeypatch.setattr(
        engine,
        "_montar_coordenadas_percurso",
        coordenadas_simuladas,
    )

    resultado = engine.calcular_melhor_rota_entrega(
        ["C", "B", "A"],
        capacidade_kg=50.0,
        autonomia_km=20.0,
        configuracao_ga={
            "tamanho_populacao": 20,
            "geracoes": 20,
            "tamanho_torneio": 3,
            "elitismo": 2,
        },
    )

    assert [item["nome"] for item in resultado["rota"]] == ["A", "B", "C"]
    assert resultado["total_viagens"] == 2
    assert [viagem["carga_kg"] for viagem in resultado["viagens"]] == [30.0, 40.0]
    assert resultado["restricoes"]["capacidade_veiculo_kg"] == 50.0
    assert resultado["algoritmo"]["inversoes_prioridade"] == 0
    assert len(resultado["coordenadas_por_viagem"]) == 2
    comparativo = resultado["comparativo_referencia"]
    assert comparativo["distancia_referencia_km"] == 5.0
    assert comparativo["economia_distancia_km"] == 0.0
    assert comparativo["economia_percentual"] == 0.0


def test_engine_rejeita_locais_duplicados_antes_de_acessar_rede(
    monkeypatch,
    unidades,
):
    monkeypatch.setattr(engine, "preparar_unidades", lambda: unidades)

    with pytest.raises(ValueError, match="duplicadas"):
        engine.calcular_melhor_rota_entrega(["A", "A"])


@pytest.mark.parametrize(
    ("argumento", "valor", "mensagem"),
    [
        ("prioridades", {"A": 4}, "prioridade"),
        ("demandas_kg", {"A": -1}, "demanda"),
    ],
)
def test_engine_rejeita_restricao_de_unidade_invalida(
    monkeypatch,
    unidades,
    argumento,
    valor,
    mensagem,
):
    monkeypatch.setattr(engine, "preparar_unidades", lambda: unidades)

    with pytest.raises(ValueError, match=mensagem):
        engine.calcular_melhor_rota_entrega(["A"], **{argumento: valor})
