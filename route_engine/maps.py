import folium
from branca.element import Element
from folium.plugins import AntPath

from route_engine.data import SEDE
from route_engine.points import formatar_endereco, preparar_unidades


ESTILOS_VIAGENS = [
    {"linha": "#2563eb", "marcador": "blue", "nome": "Azul"},
    {"linha": "#dc2626", "marcador": "red", "nome": "Vermelha"},
    {"linha": "#16a34a", "marcador": "green", "nome": "Verde"},
    {"linha": "#9333ea", "marcador": "purple", "nome": "Roxa"},
    {"linha": "#ea580c", "marcador": "orange", "nome": "Laranja"},
    {"linha": "#0891b2", "marcador": "cadetblue", "nome": "Ciano"},
    {"linha": "#be123c", "marcador": "darkred", "nome": "Vinho"},
    {"linha": "#166534", "marcador": "darkgreen", "nome": "Verde escura"},
    {"linha": "#c026d3", "marcador": "pink", "nome": "Rosa"},
    {"linha": "#4338ca", "marcador": "darkpurple", "nome": "Indigo"},
    {"linha": "#ca8a04", "marcador": "beige", "nome": "Amarela"},
    {"linha": "#475569", "marcador": "gray", "nome": "Cinza"},
]


def _estilo_viagem(numero_viagem: int) -> dict[str, str]:
    indice = (numero_viagem - 1) % len(ESTILOS_VIAGENS)
    return ESTILOS_VIAGENS[indice]


def exibir_mapa_unidades():
    unidades = preparar_unidades()
    mapa_unidades = folium.Map(
        location=SEDE["coords"],
        zoom_start=13,
    )

    folium.Marker(
        location=SEDE["coords"],
        tooltip=SEDE["nome"],
        popup=folium.Popup(
            f"<b>{SEDE['nome']}</b><br>{SEDE['tipo']}<br>"
            f"{formatar_endereco(SEDE['endereco'])}",
            max_width=280,
        ),
        icon=folium.Icon(color="green", icon="home"),
    ).add_to(mapa_unidades)

    for unidade in unidades:
        cor = "blue" if "UBS" in unidade["tipo"] else "red"

        popup_html = f"""
        <b>{unidade['nome']}</b><br>
        Tipo: {unidade['tipo']}<br>
        Endereço: {formatar_endereco(unidade['endereco'])}<br>
        Prioridade: {unidade['prioridade']}<br>
        Carga: {unidade['demanda_kg']:.1f} kg
        """

        folium.Marker(
            location=unidade["coords"],
            tooltip=unidade["nome"],
            popup=folium.Popup(popup_html, max_width=350),
            icon=folium.Icon(color=cor),
        ).add_to(mapa_unidades)

    return mapa_unidades


def criar_mapa_rota(resultado):
    mapa_entrega = folium.Map(
        location=SEDE["coords"],
        zoom_start=13,
    )

    folium.Marker(
        location=SEDE["coords"],
        tooltip="0 - Sede",
        popup=folium.Popup(
            f"<b>0 - {SEDE['nome']}</b><br>Ponto inicial<br>"
            f"{formatar_endereco(SEDE['endereco'])}",
            max_width=280,
        ),
        icon=folium.Icon(color="green", icon="home"),
    ).add_to(mapa_entrega)

    for ordem, unidade in enumerate(resultado["rota"], start=1):
        estilo = _estilo_viagem(unidade["viagem"])

        folium.Marker(
            location=unidade["coords"],
            tooltip=(
                f"Viagem {unidade['viagem']} - "
                f"Parada {unidade['ordem_na_viagem']} - {unidade['nome']}"
            ),
            popup=folium.Popup(
                f"<b>{ordem} - {unidade['nome']}</b><br>"
                f"Viagem: {unidade['viagem']}<br>"
                f"Tipo: {unidade['tipo']}<br>"
                f"Prioridade: {unidade['prioridade_rotulo']}<br>"
                f"Carga: {unidade['demanda_kg']:.1f} kg<br>"
                f"{formatar_endereco(unidade['endereco'])}",
                max_width=350,
            ),
            icon=folium.Icon(color=estilo["marcador"], icon="flag"),
        ).add_to(mapa_entrega)

    percursos = resultado.get("coordenadas_por_viagem") or [
        {
            "numero": 1,
            "coordenadas": resultado["coordenadas_rota"],
        }
    ]

    for percurso in percursos:
        numero_viagem = percurso["numero"]
        estilo = _estilo_viagem(numero_viagem)
        viagem = resultado["viagens"][numero_viagem - 1]
        descricao = (
            f"Viagem {numero_viagem}: {viagem['distancia_km']:.2f} km, "
            f"{viagem['carga_kg']:.1f} kg"
        )

        folium.PolyLine(
            locations=percurso["coordenadas"],
            color=estilo["linha"],
            weight=4,
            opacity=0.45,
            tooltip=descricao,
        ).add_to(mapa_entrega)

        AntPath(
            locations=percurso["coordenadas"],
            color=estilo["linha"],
            pulse_color="white",
            weight=6,
            opacity=0.9,
            delay=700,
            tooltip=descricao,
        ).add_to(mapa_entrega)

    itens_legenda = "".join(
        (
            '<div style="margin-top: 6px;">'
            f'<span style="display:inline-block;width:12px;height:12px;'
            f'background:{_estilo_viagem(viagem["numero"])["linha"]};'
            'margin-right:7px;border-radius:2px;"></span>'
            f'<b>Viagem {viagem["numero"]}</b>: '
            f'{viagem["carga_kg"]:.1f} kg, '
            f'{viagem["distancia_km"]:.2f} km'
            "</div>"
        )
        for viagem in resultado["viagens"]
    )
    legenda = Element(
        '<div style="position:fixed;bottom:30px;left:30px;z-index:9999;'
        'background:white;padding:12px 14px;border:1px solid #bbb;'
        'border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.18);'
        'font-size:13px;">'
        "<b>Rotas de entrega</b>"
        f"{itens_legenda}"
        "</div>"
    )
    mapa_entrega.get_root().html.add_child(legenda)

    return mapa_entrega
