"""Compatibility layer for the former Portuguese genetic module.

New code should import the operators from ``route_engine.genetic_algorithm``,
whose module and function names follow the FIAP TSP base project.
"""

from route_engine.genetic_algorithm import (
    RouteEvaluation,
    _count_priority_inversions,
    calculate_fitness,
    generate_random_population,
    mutate,
    order_crossover,
    run_genetic_algorithm,
    sort_population,
)

AvaliacaoRota = RouteEvaluation
_contar_inversoes_prioridade = _count_priority_inversions
avaliar_rota = calculate_fitness
_cruzamento_ordenado = order_crossover
_mutar = mutate
otimizar_rota_genetica = run_genetic_algorithm

__all__ = [
    "AvaliacaoRota",
    "RouteEvaluation",
    "_contar_inversoes_prioridade",
    "_cruzamento_ordenado",
    "_mutar",
    "avaliar_rota",
    "calculate_fitness",
    "generate_random_population",
    "mutate",
    "order_crossover",
    "otimizar_rota_genetica",
    "run_genetic_algorithm",
    "sort_population",
]
