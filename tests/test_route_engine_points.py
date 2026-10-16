"""Testes de cadastro, busca e serializacao dos pontos de entrega."""

import pytest

from route_engine.points import (
    buscar_unidade,
    formatar_endereco,
    normalizar_texto,
    preparar_unidades,
    serializar_ponto,
)


def unidade(nome="Hospital São José", tipo="Hospital Geral"):
    return {
        "nome": nome,
        "tipo": tipo,
        "plus_code": "C9R8+R3",
        "prioridade": 1,
        "demanda_kg": 25.0,
        "endereco": {
            "logradouro": "Rua Exemplo",
            "numero": "10",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01000-000",
        },
    }


def test_normalizacao_remove_acentos_espacos_e_diferenca_de_caixa():
    assert normalizar_texto("  HOSPITAL São José ") == "hospital sao jose"


def test_preparar_unidades_adiciona_coordenadas_sem_alterar_cadastro():
    original = unidade()

    preparada = preparar_unidades([original])[0]

    assert "coords" not in original
    assert len(preparada["coords"]) == 2
    assert preparada["plus_code_completo"].endswith("C9R8+R3")


def test_busca_aceita_nome_parcial_sem_acentos():
    encontrada = buscar_unidade("sao jose", [unidade()])
    assert encontrada["nome"] == "Hospital São José"


def test_busca_ambigua_solicita_nome_mais_especifico():
    unidades = [
        unidade("Hospital Central Norte"),
        unidade("Hospital Central Sul"),
    ]

    with pytest.raises(ValueError, match="mais de uma unidade"):
        buscar_unidade("Hospital Central", unidades)


def test_busca_inexistente_lista_opcoes_disponiveis():
    with pytest.raises(ValueError, match="Hospital São José"):
        buscar_unidade("Unidade inexistente", [unidade()])


def test_serializacao_expoe_endereco_prioridade_e_demanda_amigaveis():
    ponto = preparar_unidades([unidade()])[0]

    resultado = serializar_ponto(ponto, "unidade_de_entrega")

    assert resultado["categoria"] == "unidade_de_entrega"
    assert resultado["prioridade_rotulo"] == "alta"
    assert resultado["demanda_kg"] == 25.0
    assert resultado["endereco_formatado"] == (
        "Rua Exemplo, 10 — Centro, São Paulo/SP — CEP 01000-000"
    )


def test_formatacao_de_endereco_mantem_padrao_da_aplicacao():
    assert formatar_endereco(unidade()["endereco"]) == (
        "Rua Exemplo, 10 — Centro, São Paulo/SP — CEP 01000-000"
    )
