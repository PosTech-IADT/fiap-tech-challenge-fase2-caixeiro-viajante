"""Testes do nucleo genetico do motor de rotas."""

from __future__ import annotations

import random

import pytest

from route_engine.genetic_algorithm import (
    _count_priority_inversions,
    calculate_fitness,
    generate_random_population,
    mutate,
    order_crossover,
    run_genetic_algorithm,
)


SEDE = "Sede"


def criar_unidades(
    prioridades: tuple[int, ...] = (1, 2, 3),
    demandas: tuple[float, ...] = (10.0, 10.0, 10.0),
) -> list[dict]:
    return [
        {"nome": nome, "prioridade": prioridade, "demanda_kg": demanda}
        for nome, prioridade, demanda in zip(
            ("A", "B", "C"),
            prioridades,
            demandas,
        )
    ]


def criar_distancias(valores: dict[tuple[str, str], float] | None = None):
    pontos = (SEDE, "A", "B", "C")
    distancias = {
        (origem, destino): 10.0
        for origem in pontos
        for destino in pontos
        if origem != destino
    }
    distancias.update(valores or {})
    return distancias


def criar_configuracao(**sobrescritas):
    configuracao = {
        "tamanho_populacao": 20,
        "geracoes": 30,
        "taxa_mutacao": 0.20,
        "tamanho_torneio": 3,
        "elitismo": 2,
        "semente": 42,
        "penalidade_inversao_prioridade_m": 5_000.0,
        "peso_atraso_prioridade": 0.35,
    }
    configuracao.update(sobrescritas)
    return configuracao


class GeradorControlado:
    """Gerador minimo para escolher deterministicamente o tipo de mutacao."""

    def __init__(self, sorteios: tuple[int, int], aleatorios: list[float]):
        self.sorteios = sorteios
        self.aleatorios = iter(aleatorios)

    def random(self):
        return next(self.aleatorios)

    def sample(self, _populacao, _quantidade):
        return list(self.sorteios)


def test_cruzamento_ordenado_preserva_genes_sem_repeticao():
    pai_a = ("A", "B", "C", "D", "E")
    pai_b = ("E", "D", "C", "B", "A")

    filho = order_crossover(pai_a, pai_b, random.Random(7))

    assert sorted(filho) == sorted(pai_a)
    assert len(filho) == len(set(filho))


def test_populacao_inicial_preserva_individuo_heuristico_e_permutacoes():
    genes = ("A", "B", "C")
    inicial = ("A", "B", "C")

    populacao = generate_random_population(
        genes,
        10,
        random.Random(7),
        initial_individual=inicial,
    )

    assert populacao[0] == inicial
    assert len(populacao) == 10
    assert all(sorted(individuo) == sorted(genes) for individuo in populacao)


def test_cruzamento_com_individuo_unitario_mantem_individuo():
    assert order_crossover(("A",), ("A",), random.Random(7)) == ("A",)


def test_mutacao_zero_mantem_individuo():
    individuo = ("A", "B", "C", "D")
    assert mutate(individuo, 0.0, random.Random(7)) == individuo


def test_mutacao_swap_troca_duas_posicoes():
    individuo = ("A", "B", "C", "D")
    gerador = GeradorControlado((0, 2), [0.0, 0.25])

    assert mutate(individuo, 1.0, gerador) == ("C", "B", "A", "D")


def test_mutacao_por_inversao_inverte_trecho():
    individuo = ("A", "B", "C", "D")
    gerador = GeradorControlado((1, 3), [0.0, 0.75])

    assert mutate(individuo, 1.0, gerador) == ("A", "D", "C", "B")


def test_conta_inversoes_quando_prioridade_alta_fica_depois():
    unidades = {
        unidade["nome"]: unidade
        for unidade in criar_unidades(prioridades=(1, 2, 3))
    }

    assert _count_priority_inversions(("C", "B", "A"), unidades) == 3


def test_rota_prioritaria_possui_fitness_menor():
    unidades = {
        unidade["nome"]: unidade
        for unidade in criar_unidades(prioridades=(1, 2, 3))
    }
    argumentos = {
        "nome_sede": SEDE,
        "unidades_por_nome": unidades,
        "distancias": criar_distancias(),
        "capacidade_kg": 100.0,
        "autonomia_m": 1_000.0,
        "configuracao": criar_configuracao(),
    }

    rota_prioritaria = calculate_fitness(("A", "B", "C"), **argumentos)
    rota_invertida = calculate_fitness(("C", "B", "A"), **argumentos)

    assert rota_prioritaria.fitness < rota_invertida.fitness
    assert rota_prioritaria.inversoes_prioridade == 0
    assert rota_invertida.inversoes_prioridade == 3


def test_capacidade_divide_rota_em_multiplas_viagens():
    unidades = {
        unidade["nome"]: unidade
        for unidade in criar_unidades(demandas=(40.0, 40.0, 40.0))
    }

    avaliacao = calculate_fitness(
        ("A", "B", "C"),
        SEDE,
        unidades,
        criar_distancias(),
        capacidade_kg=80.0,
        autonomia_m=1_000.0,
        configuracao=criar_configuracao(),
    )

    assert avaliacao.viagens == (("A", "B"), ("C",))
    assert avaliacao.cargas_kg == (80.0, 40.0)
    assert avaliacao.distancias_viagens_m == (30.0, 20.0)
    assert not avaliacao.violacoes


def test_autonomia_divide_rota_antes_de_exceder_limite():
    unidades = {
        unidade["nome"]: unidade
        for unidade in criar_unidades(demandas=(1.0, 1.0, 1.0))
    }
    distancias = criar_distancias(
        {
            (SEDE, "A"): 30.0,
            ("A", SEDE): 30.0,
            ("A", "B"): 30.0,
            (SEDE, "B"): 30.0,
            ("B", SEDE): 30.0,
            ("B", "C"): 30.0,
            (SEDE, "C"): 30.0,
            ("C", SEDE): 30.0,
        }
    )

    avaliacao = calculate_fitness(
        ("A", "B", "C"),
        SEDE,
        unidades,
        distancias,
        capacidade_kg=100.0,
        autonomia_m=70.0,
        configuracao=criar_configuracao(),
    )

    assert avaliacao.viagens == (("A",), ("B",), ("C",))
    assert all(distancia <= 70.0 for distancia in avaliacao.distancias_viagens_m)
    assert not avaliacao.violacoes


@pytest.mark.parametrize(
    ("demandas", "autonomia_km", "mensagem"),
    [
        ((150.0, 10.0, 10.0), 1.0, "excede a capacidade"),
        ((10.0, 10.0, 10.0), 0.015, "excede a autonomia"),
    ],
)
def test_otimizador_rejeita_rota_operacionalmente_inviavel(
    demandas,
    autonomia_km,
    mensagem,
):
    with pytest.raises(ValueError, match=mensagem):
        run_genetic_algorithm(
            nome_sede=SEDE,
            unidades=criar_unidades(demandas=demandas),
            distancias=criar_distancias(),
            capacidade_kg=100.0,
            autonomia_km=autonomia_km,
            configuracao=criar_configuracao(),
        )


def test_resultado_e_reproduzivel_com_a_mesma_semente():
    argumentos = {
        "nome_sede": SEDE,
        "unidades": criar_unidades(),
        "distancias": criar_distancias(),
        "capacidade_kg": 100.0,
        "autonomia_km": 1.0,
        "configuracao": criar_configuracao(semente=123),
    }

    assert run_genetic_algorithm(**argumentos) == run_genetic_algorithm(
        **argumentos
    )


def test_otimizador_retorna_permutacao_valida_e_sem_inversoes():
    resultado = run_genetic_algorithm(
        nome_sede=SEDE,
        unidades=criar_unidades(),
        distancias=criar_distancias(),
        capacidade_kg=100.0,
        autonomia_km=1.0,
        configuracao=criar_configuracao(),
    )

    assert sorted(resultado["ordem"]) == ["A", "B", "C"]
    assert resultado["inversoes_prioridade"] == 0
    assert resultado["geracoes_executadas"] == 30
    assert resultado["tamanho_populacao"] == 20


@pytest.mark.parametrize(
    ("campo", "valor", "mensagem"),
    [
        ("tamanho_populacao", 1, "populacao"),
        ("geracoes", 0, "geracao"),
        ("taxa_mutacao", 1.5, "taxa de mutacao"),
        ("tamanho_torneio", 0, "torneio"),
        ("elitismo", 0, "elitismo"),
    ],
)
def test_rejeita_configuracao_genetica_invalida(campo, valor, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        run_genetic_algorithm(
            nome_sede=SEDE,
            unidades=criar_unidades(),
            distancias=criar_distancias(),
            capacidade_kg=100.0,
            autonomia_km=1.0,
            configuracao=criar_configuracao(**{campo: valor}),
        )


@pytest.mark.parametrize(
    ("capacidade_kg", "autonomia_km", "mensagem"),
    [(0.0, 1.0, "capacidade"), (100.0, 0.0, "autonomia")],
)
def test_rejeita_parametros_operacionais_invalidos(
    capacidade_kg,
    autonomia_km,
    mensagem,
):
    with pytest.raises(ValueError, match=mensagem):
        run_genetic_algorithm(
            nome_sede=SEDE,
            unidades=criar_unidades(),
            distancias=criar_distancias(),
            capacidade_kg=capacidade_kg,
            autonomia_km=autonomia_km,
            configuracao=criar_configuracao(),
        )
