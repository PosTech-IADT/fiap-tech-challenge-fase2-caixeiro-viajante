from functools import lru_cache

import networkx as nx
import osmnx as ox

from route_engine.data import SEDE
from route_engine.points import buscar_unidade, preparar_unidades


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
        ) ** 0.5
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
    distancia = 0

    for origem, destino in zip(caminho, caminho[1:]):
        arestas = grafo_ruas.get_edge_data(origem, destino).values()
        distancia += min(aresta.get("length", 0) for aresta in arestas)

    return distancia


def calcular_melhor_ordem(sede, unidades_entrega, distancias):
    nomes_unidades = tuple(unidade["nome"] for unidade in unidades_entrega)

    @lru_cache(None)
    def melhor_caminho(origem_nome, restantes):
        if not restantes:
            return 0, []

        melhor_distancia = float("inf")
        melhor_ordem = []

        for proximo_nome in restantes:
            proximos_restantes = tuple(
                nome for nome in restantes
                if nome != proximo_nome
            )
            distancia_restante, ordem_restante = melhor_caminho(
                proximo_nome,
                proximos_restantes,
            )
            distancia_total = (
                distancias[(origem_nome, proximo_nome)]
                + distancia_restante
            )

            if distancia_total < melhor_distancia:
                melhor_distancia = distancia_total
                melhor_ordem = [proximo_nome] + ordem_restante

        return melhor_distancia, melhor_ordem

    return melhor_caminho(sede["nome"], nomes_unidades)


def calcular_melhor_rota_entrega(nomes_locais):
    if not nomes_locais:
        raise ValueError("Informe pelo menos um local para calcular a rota.")

    unidades = preparar_unidades()
    unidades_entrega = [buscar_unidade(nome, unidades) for nome in nomes_locais]
    pontos = [SEDE] + unidades_entrega

    ox.settings.use_cache = True
    ox.settings.log_console = False

    grafo_ruas = montar_grafo_por_ruas(pontos)

    for ponto in pontos:
        lat, lon = ponto["coords"]
        ponto["no_rua"] = ox.distance.nearest_nodes(grafo_ruas, X=lon, Y=lat)

    distancias = {}
    caminhos = {}

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

    menor_distancia_m, melhor_ordem_nomes = calcular_melhor_ordem(
        SEDE,
        unidades_entrega,
        distancias,
    )
    unidades_por_nome = {unidade["nome"]: unidade for unidade in unidades_entrega}
    melhor_rota = [unidades_por_nome[nome] for nome in melhor_ordem_nomes]
    pontos_rota = [SEDE] + melhor_rota

    coordenadas_rota = []

    for origem, destino in zip(pontos_rota, pontos_rota[1:]):
        trecho = caminhos[(origem["nome"], destino["nome"])]

        if coordenadas_rota:
            trecho = trecho[1:]

        coordenadas_rota.extend(
            (grafo_ruas.nodes[no]["y"], grafo_ruas.nodes[no]["x"])
            for no in trecho
        )

    return {
        "sede": SEDE,
        "distancia_total_m": menor_distancia_m,
        "distancia_total_km": menor_distancia_m / 1000,
        "rota": melhor_rota,
        "pontos_rota": pontos_rota,
        "coordenadas_rota": coordenadas_rota,
    }
