from route_agent.ui_state import preservar_quebras_linha_markdown


def test_preserva_quebras_simples_para_renderizacao_markdown():
    texto = "Hospital A, 10 kg\nHospital B, 20 kg\n\nA partir da sede."

    assert preservar_quebras_linha_markdown(texto) == (
        "Hospital A, 10 kg  \n"
        "Hospital B, 20 kg  \n"
        "  \n"
        "A partir da sede."
    )


def test_normaliza_quebras_de_linha_de_outros_sistemas():
    assert preservar_quebras_linha_markdown("A\r\nB\rC") == "A  \nB  \nC"
