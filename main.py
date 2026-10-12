from pathlib import Path

from route_engine import SEDE, calcular_melhor_rota_entrega, criar_mapa_rota


# ---------------------------------------------------------
# CONFIGURACAO DA ENTREGA
# Edite esta lista com os hospitais/unidades que deseja visitar.
# A rota sempre sai da sede.
# ---------------------------------------------------------

LOCAIS_ENTREGA = [
    "Hospital IGESP Paulista",
    "HCor - Hospital do Coração",
    "Hospital Luz Vila Mariana",
]

ARQUIVO_MAPA = "rota_entrega.html"


def imprimir_resultado(resultado):
    print("Melhor ordem para esta entrega:")
    print(f"0. {SEDE['nome']} (sede)")

    for ordem, unidade in enumerate(resultado["rota"], start=1):
        print(f"{ordem}. {unidade['nome']} - {unidade['tipo']}")

    print(f"\nDistancia total estimada pelas ruas: {resultado['distancia_total_km']:.2f} km")


def main():
    resultado = calcular_melhor_rota_entrega(LOCAIS_ENTREGA)
    mapa = criar_mapa_rota(resultado)

    caminho_mapa = Path(ARQUIVO_MAPA)
    mapa.save(caminho_mapa)

    imprimir_resultado(resultado)
    print(f"\nMapa salvo em: {caminho_mapa.resolve()}")


if __name__ == "__main__":
    main()
