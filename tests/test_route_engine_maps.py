"""Testes da visualizacao das viagens no mapa."""

import folium

from route_engine.maps import ESTILOS_VIAGENS, _estilo_viagem, criar_mapa_rota


def criar_parada(nome, viagem, ordem, coords):
    return {
        "nome": nome,
        "tipo": "Hospital",
        "viagem": viagem,
        "ordem_na_viagem": ordem,
        "coords": coords,
        "prioridade_rotulo": "alta",
        "demanda_kg": 10.0,
        "endereco": {
            "logradouro": "Rua Teste",
            "numero": "1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01000-000",
        },
    }


def test_estilo_de_viagem_alterna_cores_e_reinicia_paleta():
    assert _estilo_viagem(1) != _estilo_viagem(2)
    assert _estilo_viagem(len(ESTILOS_VIAGENS) + 1) == _estilo_viagem(1)


def test_mapa_renderiza_uma_cor_e_legenda_por_viagem():
    resultado = {
        "rota": [
            criar_parada("A", 1, 1, (-23.51, -46.61)),
            criar_parada("B", 2, 1, (-23.52, -46.62)),
        ],
        "coordenadas_rota": [],
        "coordenadas_por_viagem": [
            {
                "numero": 1,
                "coordenadas": [(-23.50, -46.60), (-23.51, -46.61)],
            },
            {
                "numero": 2,
                "coordenadas": [(-23.50, -46.60), (-23.52, -46.62)],
            },
        ],
        "viagens": [
            {"numero": 1, "distancia_km": 2.0, "carga_kg": 10.0},
            {"numero": 2, "distancia_km": 3.0, "carga_kg": 10.0},
        ],
    }

    mapa = criar_mapa_rota(resultado)
    html = mapa.get_root().render()

    assert isinstance(mapa, folium.Map)
    assert ESTILOS_VIAGENS[0]["linha"] in html
    assert ESTILOS_VIAGENS[1]["linha"] in html
    assert "Viagem 1" in html
    assert "Viagem 2" in html
