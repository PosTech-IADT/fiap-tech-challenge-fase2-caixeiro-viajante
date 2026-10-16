from __future__ import annotations

import networkx as nx
import osmnx as ox

from route_engine.data import (
    CONFIGURACAO_ALGORITMO_GENETICO,
    SEDE,
    VEICULO_PADRAO,
)
from route_engine.genetic import otimizar_rota_genetica
from route_engine.points import buscar_unidade, preparar_unidades


ROTULOS_PRIORIDADE = {
    1: "alta",
    2: "media",
    3: "normal",
}


def listar_unidades():
    return preparar_unidades()


def montar_grafo_por_ruas(pontos):
    centro_mapa = (
        sum(ponto["coords"][0] for ponto in pontos) / len(pontos),
        sum(ponto["coords"][1] for ponto in pontos) / len(pontos),
    )

    maior_distancia_graus = max(
        (
            (ponto["coords"][0] - centro_mapa[0]) ** 2
            + (ponto["coords"][1] - centro_mapa[1]) ** 2
        )
        ** 0.5
        for ponto in pontos
    )
    raio_busca_m = int(maior_distancia_graus * 111_000) + 2_000

    return ox.graph_from_point(
        centro_mapa,
        dist=raio_busca_m,
        network_type="drive",
        simplify=True,
    )


def comprimento_caminho_m(grafo_ruas, caminho):
    distancia = 0.0

    for origem, destino in zip(caminho, caminho[1:]):
        arestas = grafo_ruas.get_edge_data(origem, destino).values()
        distancia += min(aresta.get("length", 0) for aresta in arestas)

    return distancia


def _aplicar_restricoes_unidades(
    unidades: list[dict],
    prioridades: dict[str, int] | None,
    demandas_kg: dict[str, float] | None,
) -> None:
    for nome_informado, prioridade in (prioridades or {}).items():
        unidade = buscar_unidade(nome_informado, unidades)
        prioridade = int(prioridade)

        if prioridade not in ROTULOS_PRIORIDADE:
            raise ValueError("A prioridade deve ser 1 (alta), 2 (media) ou 3 (normal).")

        unidade["prioridade"] = prioridade

    for nome_informado, demanda_kg in (demandas_kg or {}).items():
        unidade = buscar_unidade(nome_informado, unidades)
        demanda_kg = float(demanda_kg)

        if demanda_kg < 0:
            raise ValueError("A demanda de carga nao pode ser negativa.")

        unidade["demanda_kg"] = demanda_kg


def _calcular_matriz_rotas(grafo_ruas, pontos):
    """Precalcula as menores distancias reais usadas pelo fitness do GA.

    Esta etapa usa a malha viaria antes da evolucao; nao e um operador genetico.
    """
    distancias = {}
    caminhos = {}

    for ponto in pontos:
        latitude, longitude = ponto["coords"]
        ponto["no_rua"] = ox.distance.nearest_nodes(
            grafo_ruas,
            X=longitude,
            Y=latitude,
        )

    for origem in pontos:
        for destino in pontos:
            if origem == destino:
                continue

            chave = (origem["nome"], destino["nome"])
            caminho = nx.shortest_path(
                grafo_ruas,
                origem["no_rua"],
                destino["no_rua"],
                weight="length",
            )
            caminhos[chave] = caminho
            distancias[chave] = comprimento_caminho_m(grafo_ruas, caminho)

    return distancias, caminhos


def _montar_coordenadas_percurso(
    viagens: list[list[str]],
    unidades_por_nome: dict[str, dict],
    caminhos: dict[tuple[str, str], list],
    grafo_ruas,
) -> tuple[list[tuple[float, float]], list[dict], list[dict]]:
    coordenadas = []
    pontos_percurso = []
    coordenadas_por_viagem = []

    for numero_viagem, nomes_viagem in enumerate(viagens, start=1):
        coordenadas_viagem = []
        pontos_viagem = [SEDE] + [
            unidades_por_nome[nome]
            for nome in nomes_viagem
        ] + [SEDE]

        for ponto in pontos_viagem:
            pontos_percurso.append(
                {
                    "viagem": numero_viagem,
                    "nome": ponto["nome"],
                    "coords": ponto["coords"],
                }
            )

        for origem, destino in zip(pontos_viagem, pontos_viagem[1:]):
            trecho = caminhos[(origem["nome"], destino["nome"])]

            if coordenadas_viagem:
                trecho = trecho[1:]

            coordenadas_viagem.extend(
                (grafo_ruas.nodes[no]["y"], grafo_ruas.nodes[no]["x"])
                for no in trecho
            )

        coordenadas_por_viagem.append(
            {
                "numero": numero_viagem,
                "coordenadas": coordenadas_viagem,
            }
        )

        if coordenadas and coordenadas_viagem:
            coordenadas.extend(coordenadas_viagem[1:])
        else:
            coordenadas.extend(coordenadas_viagem)

    return coordenadas, pontos_percurso, coordenadas_por_viagem


def calcular_melhor_rota_entrega(
    nomes_locais: list[str],
    *,
    capacidade_kg: float | None = None,
    autonomia_km: float | None = None,
    prioridades: dict[str, int] | None = None,
    demandas_kg: dict[str, float] | None = None,
    configuracao_ga: dict | None = None,
):
    """Calcula uma rota por algoritmo genetico.

    A ordem das unidades e otimizada considerando distancia e prioridade. Quando
    a proxima entrega excederia a capacidade ou a autonomia, uma nova viagem e
    iniciada na sede. Os argumentos opcionais permitem simular outro veiculo ou
    sobrescrever as restricoes das unidades sem alterar o cadastro.
    """
    if not nomes_locais:
        raise ValueError("Informe pelo menos um local para calcular a rota.")

    unidades_disponiveis = preparar_unidades()
    unidades_entrega = [
        buscar_unidade(nome, unidades_disponiveis).copy()
        for nome in nomes_locais
    ]
    nomes_encontrados = [unidade["nome"] for unidade in unidades_entrega]

    if len(nomes_encontrados) != len(set(nomes_encontrados)):
        raise ValueError("A lista de locais contem unidades duplicadas.")

    _aplicar_restricoes_unidades(
        unidades_entrega,
        prioridades,
        demandas_kg,
    )

    capacidade_kg = float(
        capacidade_kg
        if capacidade_kg is not None
        else VEICULO_PADRAO["capacidade_kg"]
    )
    autonomia_km = float(
        autonomia_km
        if autonomia_km is not None
        else VEICULO_PADRAO["autonomia_km"]
    )
    configuracao = CONFIGURACAO_ALGORITMO_GENETICO.copy()
    configuracao.update(configuracao_ga or {})

    pontos = [SEDE] + unidades_entrega
    ox.settings.use_cache = True
    ox.settings.log_console = False
    grafo_ruas = montar_grafo_por_ruas(pontos)
    distancias, caminhos = _calcular_matriz_rotas(grafo_ruas, pontos)

    resultado_ga = otimizar_rota_genetica(
        nome_sede=SEDE["nome"],
        unidades=unidades_entrega,
        distancias=distancias,
        capacidade_kg=capacidade_kg,
        autonomia_km=autonomia_km,
        configuracao=configuracao,
    )

    unidades_por_nome = {
        unidade["nome"]: unidade
        for unidade in unidades_entrega
    }
    melhor_rota = []
    viagens = []

    for numero_viagem, nomes_viagem in enumerate(
        resultado_ga["viagens"],
        start=1,
    ):
        paradas = []

        for ordem_viagem, nome in enumerate(nomes_viagem, start=1):
            unidade = unidades_por_nome[nome].copy()
            unidade["viagem"] = numero_viagem
            unidade["ordem_na_viagem"] = ordem_viagem
            unidade["prioridade_rotulo"] = ROTULOS_PRIORIDADE.get(
                unidade["prioridade"],
                f"nivel {unidade['prioridade']}",
            )
            melhor_rota.append(unidade)
            paradas.append(unidade)

        distancia_viagem_m = resultado_ga["distancias_viagens_m"][
            numero_viagem - 1
        ]
        viagens.append(
            {
                "numero": numero_viagem,
                "carga_kg": resultado_ga["cargas_kg"][numero_viagem - 1],
                "distancia_m": distancia_viagem_m,
                "distancia_km": distancia_viagem_m / 1000,
                "paradas": paradas,
            }
        )

    (
        coordenadas_rota,
        pontos_percurso,
        coordenadas_por_viagem,
    ) = _montar_coordenadas_percurso(
        resultado_ga["viagens"],
        unidades_por_nome,
        caminhos,
        grafo_ruas,
    )

    for viagem, percurso in zip(viagens, coordenadas_por_viagem):
        viagem["coordenadas_rota"] = percurso["coordenadas"]
    demanda_total_kg = sum(
        float(unidade["demanda_kg"])
        for unidade in unidades_entrega
    )

    return {
        "sede": SEDE,
        "distancia_total_m": resultado_ga["distancia_total_m"],
        "distancia_total_km": resultado_ga["distancia_total_m"] / 1000,
        "rota": melhor_rota,
        "pontos_rota": [SEDE] + melhor_rota,
        "pontos_percurso": pontos_percurso,
        "coordenadas_rota": coordenadas_rota,
        "coordenadas_por_viagem": coordenadas_por_viagem,
        "viagens": viagens,
        "total_viagens": len(viagens),
        "retorna_para_sede": True,
        "restricoes": {
            "capacidade_veiculo_kg": capacidade_kg,
            "autonomia_veiculo_km": autonomia_km,
            "demanda_total_kg": demanda_total_kg,
            "prioridade": (
                "1 representa a maior prioridade; numeros maiores possuem "
                "menor prioridade."
            ),
        },
        "algoritmo": {
            "nome": "algoritmo_genetico",
            "fitness": resultado_ga["fitness"],
            "geracoes_executadas": resultado_ga["geracoes_executadas"],
            "geracao_melhor_resultado": resultado_ga[
                "geracao_melhor_resultado"
            ],
            "tamanho_populacao": resultado_ga["tamanho_populacao"],
            "semente": resultado_ga["semente"],
            "inversoes_prioridade": resultado_ga["inversoes_prioridade"],
        },
    }
