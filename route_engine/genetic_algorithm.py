"""Evolucao do algoritmo genetico de TSP fornecido pela FIAP.

Os operadores mantem os nomes do codigo-base e acrescentam as restricoes
operacionais necessarias ao roteamento hospitalar.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RouteEvaluation:
    fitness: float
    distancia_total_m: float
    viagens: tuple[tuple[str, ...], ...]
    cargas_kg: tuple[float, ...]
    distancias_viagens_m: tuple[float, ...]
    inversoes_prioridade: int
    violacoes: tuple[str, ...]


def _validate_configuration(
    capacidade_kg: float,
    autonomia_m: float,
    configuracao: dict,
) -> None:
    if capacidade_kg <= 0:
        raise ValueError("A capacidade do veiculo deve ser maior que zero.")
    if autonomia_m <= 0:
        raise ValueError("A autonomia do veiculo deve ser maior que zero.")
    if configuracao["tamanho_populacao"] < 2:
        raise ValueError(
            "A populacao do algoritmo genetico deve ter ao menos 2 individuos."
        )
    if configuracao["geracoes"] < 1:
        raise ValueError("O algoritmo genetico deve executar ao menos uma geracao.")
    if not 0 <= configuracao["taxa_mutacao"] <= 1:
        raise ValueError("A taxa de mutacao deve estar entre 0 e 1.")
    if configuracao["tamanho_torneio"] < 1:
        raise ValueError("O torneio deve possuir ao menos um individuo.")
    if configuracao["elitismo"] < 1:
        raise ValueError("O elitismo deve preservar ao menos um individuo.")


def _count_priority_inversions(
    ordem: tuple[str, ...],
    unidades_por_nome: dict[str, dict],
) -> int:
    # TECNICA: penalidade por restricao de prioridade.
    # Conta quantas entregas menos prioritarias aparecem antes das prioritarias.
    prioridades = [unidades_por_nome[nome]["prioridade"] for nome in ordem]
    return sum(
        1
        for indice, prioridade in enumerate(prioridades)
        for prioridade_seguinte in prioridades[indice + 1 :]
        if prioridade > prioridade_seguinte
    )


def calculate_fitness(
    ordem: tuple[str, ...],
    nome_sede: str,
    unidades_por_nome: dict[str, dict],
    distancias: dict[tuple[str, str], float],
    capacidade_kg: float,
    autonomia_m: float,
    configuracao: dict,
) -> RouteEvaluation:
    """Calcula o fitness da rota considerando distancia e restricoes."""
    viagens: list[tuple[str, ...]] = []
    cargas: list[float] = []
    distancias_viagens: list[float] = []
    violacoes: list[str] = []
    distancias_ate_entrega: dict[str, float] = {}

    viagem_atual: list[str] = []
    carga_atual = 0.0
    distancia_viagem = 0.0
    distancia_concluida = 0.0
    ultimo_ponto = nome_sede

    def concluir_viagem() -> None:
        nonlocal carga_atual, distancia_viagem, distancia_concluida, ultimo_ponto

        if not viagem_atual:
            return

        distancia_viagem += distancias[(ultimo_ponto, nome_sede)]
        viagens.append(tuple(viagem_atual))
        cargas.append(carga_atual)
        distancias_viagens.append(distancia_viagem)
        distancia_concluida += distancia_viagem
        viagem_atual.clear()
        carga_atual = 0.0
        distancia_viagem = 0.0
        ultimo_ponto = nome_sede

    for nome in ordem:
        unidade = unidades_por_nome[nome]
        demanda_kg = float(unidade["demanda_kg"])

        if demanda_kg > capacidade_kg:
            violacoes.append(
                f"{nome}: demanda de {demanda_kg:.1f} kg excede a capacidade "
                f"de {capacidade_kg:.1f} kg."
            )

        distancia_ate_ponto = distancias[(ultimo_ponto, nome)]
        distancia_retorno = distancias[(nome, nome_sede)]
        excede_carga = viagem_atual and carga_atual + demanda_kg > capacidade_kg
        excede_autonomia = (
            viagem_atual
            and distancia_viagem + distancia_ate_ponto + distancia_retorno
            > autonomia_m
        )

        # TECNICA: reparacao de individuo.
        # Se a viagem ficaria inviavel, a rota e dividida com retorno a sede.
        if excede_carga or excede_autonomia:
            concluir_viagem()
            distancia_ate_ponto = distancias[(nome_sede, nome)]
            distancia_retorno = distancias[(nome, nome_sede)]

        if distancia_ate_ponto + distancia_retorno > autonomia_m:
            violacoes.append(
                f"{nome}: o percurso de ida e volta excede a autonomia "
                f"de {autonomia_m / 1000:.1f} km."
            )

        viagem_atual.append(nome)
        carga_atual += demanda_kg
        distancia_viagem += distancia_ate_ponto
        ultimo_ponto = nome
        distancias_ate_entrega[nome] = distancia_concluida + distancia_viagem

    concluir_viagem()

    distancia_total_m = sum(distancias_viagens)
    inversoes = _count_priority_inversions(ordem, unidades_por_nome)
    penalidade_prioridade = sum(
        distancias_ate_entrega[nome]
        * (4 - int(unidades_por_nome[nome]["prioridade"]))
        for nome in ordem
    )
    penalidade_violacoes = len(violacoes) * 1_000_000_000.0
    # TECNICA: fitness ponderado com penalidades.
    # Como o problema e de minimizacao, a melhor solucao possui o menor valor.
    fitness = (
        distancia_total_m
        + inversoes * configuracao["penalidade_inversao_prioridade_m"]
        + penalidade_prioridade * configuracao["peso_atraso_prioridade"]
        + penalidade_violacoes
    )

    return RouteEvaluation(
        fitness=fitness,
        distancia_total_m=distancia_total_m,
        viagens=tuple(viagens),
        cargas_kg=tuple(cargas),
        distancias_viagens_m=tuple(distancias_viagens),
        inversoes_prioridade=inversoes,
        violacoes=tuple(violacoes),
    )


def order_crossover(
    pai_a: tuple[str, ...],
    pai_b: tuple[str, ...],
    gerador: random.Random,
) -> tuple[str, ...]:
    """Ordered Crossover (OX): combina os pais sem repetir pontos."""
    if len(pai_a) < 2:
        return pai_a

    inicio, fim = sorted(gerador.sample(range(len(pai_a)), 2))
    trecho = pai_a[inicio : fim + 1]
    restantes = [gene for gene in pai_b if gene not in trecho]
    return tuple(restantes[:inicio] + list(trecho) + restantes[inicio:])


def mutate(
    individuo: tuple[str, ...],
    taxa_mutacao: float,
    gerador: random.Random,
) -> tuple[str, ...]:
    """Aplica mutacao Swap ou por inversao conforme a taxa configurada."""
    if len(individuo) < 2 or gerador.random() >= taxa_mutacao:
        return individuo

    genes = list(individuo)
    inicio, fim = sorted(gerador.sample(range(len(genes)), 2))

    if gerador.random() < 0.5:
        # TECNICA: Swap Mutation - troca dois pontos de posicao.
        genes[inicio], genes[fim] = genes[fim], genes[inicio]
    else:
        # TECNICA: Inversion Mutation - inverte um trecho da rota.
        genes[inicio : fim + 1] = reversed(genes[inicio : fim + 1])

    return tuple(genes)


def generate_random_population(
    genes: tuple[str, ...],
    population_size: int,
    generator: random.Random,
    *,
    initial_individual: tuple[str, ...] | None = None,
) -> list[tuple[str, ...]]:
    """Generate valid route permutations for the initial GA population.

    This extends the function from the FIAP base project by accepting an
    optional heuristic individual while keeping the remaining population
    random and diverse.
    """
    population = [initial_individual] if initial_individual is not None else []

    while len(population) < population_size:
        individual = list(genes)
        generator.shuffle(individual)
        population.append(tuple(individual))

    return population


def sort_population(
    population: list[tuple[str, ...]],
    fitness: list[RouteEvaluation],
) -> tuple[list[tuple[str, ...]], list[RouteEvaluation]]:
    """Sort routes and their evaluations from best to worst fitness."""
    ordered = sorted(
        zip(population, fitness),
        key=lambda item: item[1].fitness,
    )
    sorted_population, sorted_fitness = zip(*ordered)
    return list(sorted_population), list(sorted_fitness)


def run_genetic_algorithm(
    nome_sede: str,
    unidades: list[dict],
    distancias: dict[tuple[str, str], float],
    capacidade_kg: float,
    autonomia_km: float,
    configuracao: dict,
) -> dict:
    """Retorna a melhor rota encontrada pelo algoritmo genetico."""
    autonomia_m = autonomia_km * 1000
    _validate_configuration(capacidade_kg, autonomia_m, configuracao)

    # REPRESENTACAO: cada individuo e uma permutacao dos nomes das entregas.
    unidades_por_nome = {unidade["nome"]: unidade for unidade in unidades}
    genes = tuple(unidades_por_nome)
    gerador = random.Random(configuracao["semente"])

    if not genes:
        raise ValueError("O algoritmo genetico precisa de ao menos uma unidade.")

    tamanho_populacao = int(configuracao["tamanho_populacao"])
    # TECNICA: populacao inicial hibrida (hot start + diversidade aleatoria).
    # O primeiro individuo e uma heuristica por prioridade e proximidade da sede.
    individuo_inicial = tuple(
        sorted(
            genes,
            key=lambda nome: (
                unidades_por_nome[nome]["prioridade"],
                distancias[(nome_sede, nome)],
            ),
        )
    )
    populacao = generate_random_population(
        genes,
        tamanho_populacao,
        gerador,
        initial_individual=individuo_inicial,
    )

    def evaluate(individuo: tuple[str, ...]) -> RouteEvaluation:
        return calculate_fitness(
            individuo,
            nome_sede,
            unidades_por_nome,
            distancias,
            capacidade_kg,
            autonomia_m,
            configuracao,
        )

    def tournament_selection(
        avaliacoes: dict[tuple[str, ...], RouteEvaluation],
    ) -> tuple[str, ...]:
        # TECNICA: selecao por torneio.
        # Sorteia candidatos e escolhe como pai aquele com o menor fitness.
        tamanho = min(int(configuracao["tamanho_torneio"]), len(populacao))
        candidatos = gerador.sample(populacao, tamanho)
        return min(candidatos, key=lambda individuo: avaliacoes[individuo].fitness)

    melhor_individuo = populacao[0]
    melhor_avaliacao = evaluate(melhor_individuo)
    geracao_melhor_resultado = 0

    # CRITERIO DE PARADA: quantidade fixa de geracoes.
    for geracao in range(1, int(configuracao["geracoes"]) + 1):
        valores_fitness = [evaluate(individuo) for individuo in populacao]
        populacao, valores_fitness = sort_population(populacao, valores_fitness)
        avaliacoes = dict(zip(populacao, valores_fitness))

        if avaliacoes[populacao[0]].fitness < melhor_avaliacao.fitness:
            melhor_individuo = populacao[0]
            melhor_avaliacao = avaliacoes[melhor_individuo]
            geracao_melhor_resultado = geracao

        if geracao == int(configuracao["geracoes"]):
            break

        # TECNICA: elitismo.
        # Copia os melhores individuos sem cruzamento ou mutacao.
        quantidade_elite = min(int(configuracao["elitismo"]), tamanho_populacao)
        nova_populacao = populacao[:quantidade_elite]

        while len(nova_populacao) < tamanho_populacao:
            # TECNICAS: torneio -> OX -> mutacao Swap ou inversao.
            pai_a = tournament_selection(avaliacoes)
            pai_b = tournament_selection(avaliacoes)
            filho = order_crossover(pai_a, pai_b, gerador)
            filho = mutate(filho, configuracao["taxa_mutacao"], gerador)
            nova_populacao.append(filho)

        populacao = nova_populacao

    avaliacao_final = melhor_avaliacao

    if avaliacao_final.violacoes:
        raise ValueError(" ".join(avaliacao_final.violacoes))

    return {
        "ordem": list(melhor_individuo),
        "fitness": avaliacao_final.fitness,
        "distancia_total_m": avaliacao_final.distancia_total_m,
        "viagens": [list(viagem) for viagem in avaliacao_final.viagens],
        "cargas_kg": list(avaliacao_final.cargas_kg),
        "distancias_viagens_m": list(avaliacao_final.distancias_viagens_m),
        "inversoes_prioridade": avaliacao_final.inversoes_prioridade,
        "geracoes_executadas": int(configuracao["geracoes"]),
        "geracao_melhor_resultado": geracao_melhor_resultado,
        "tamanho_populacao": tamanho_populacao,
        "semente": configuracao["semente"],
    }
