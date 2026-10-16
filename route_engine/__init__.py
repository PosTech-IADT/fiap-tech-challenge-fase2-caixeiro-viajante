from route_engine.data import (
    CONFIGURACAO_ALGORITMO_GENETICO,
    SEDE,
    UNIDADES,
    VEICULO_PADRAO,
)


def calcular_melhor_rota_entrega(nomes_locais, **restricoes):
    from route_engine.engine import calcular_melhor_rota_entrega as calcular

    return calcular(nomes_locais, **restricoes)


def listar_unidades():
    from route_engine.engine import listar_unidades as listar

    return listar()


def criar_mapa_rota(resultado):
    from route_engine.maps import criar_mapa_rota as criar

    return criar(resultado)


def exibir_mapa_unidades():
    from route_engine.maps import exibir_mapa_unidades as exibir

    return exibir()

__all__ = [
    "SEDE",
    "UNIDADES",
    "VEICULO_PADRAO",
    "CONFIGURACAO_ALGORITMO_GENETICO",
    "calcular_melhor_rota_entrega",
    "criar_mapa_rota",
    "exibir_mapa_unidades",
    "listar_unidades",
]
