import folium
from folium.plugins import AntPath

from route_engine.data import SEDE
from route_engine.points import formatar_endereco, preparar_unidades


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
        situacao = ""

        if unidade.get("situacao"):
            situacao = f"<br>Situação: {unidade['situacao']}"

        popup_html = f"""
        <b>{unidade['nome']}</b><br>
        Tipo: {unidade['tipo']}<br>
        Endereço: {formatar_endereco(unidade['endereco'])}{situacao}
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
        situacao = ""

        if unidade.get("situacao"):
            situacao = f"<br>Situação: {unidade['situacao']}"

        folium.Marker(
            location=unidade["coords"],
            tooltip=f"{ordem} - {unidade['nome']}",
            popup=folium.Popup(
                f"<b>{ordem} - {unidade['nome']}</b><br>"
                f"Tipo: {unidade['tipo']}<br>"
                f"{formatar_endereco(unidade['endereco'])}{situacao}",
                max_width=350,
            ),
            icon=folium.Icon(color="orange", icon="flag"),
        ).add_to(mapa_entrega)

    distancia_km = resultado["distancia_total_km"]

    folium.PolyLine(
        locations=resultado["coordenadas_rota"],
        color="purple",
        weight=3,
        opacity=0.35,
        tooltip=f"Menor rota de entrega: {distancia_km:.2f} km",
    ).add_to(mapa_entrega)

    AntPath(
        locations=resultado["coordenadas_rota"],
        color="purple",
        pulse_color="white",
        weight=6,
        opacity=0.9,
        delay=700,
        tooltip=f"Rota animada: {distancia_km:.2f} km",
    ).add_to(mapa_entrega)

    return mapa_entrega
