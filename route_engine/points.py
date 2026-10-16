import unicodedata

from openlocationcode import openlocationcode as olc

from route_engine.data import REF_LAT, REF_LON, SEDE, UNIDADES


def normalizar_texto(texto: str) -> str:
    texto_sem_acento = unicodedata.normalize("NFKD", texto)
    texto_sem_acento = "".join(
        caractere
        for caractere in texto_sem_acento
        if not unicodedata.combining(caractere)
    )
    return texto_sem_acento.casefold().strip()


def plus_code_para_coords(
    codigo_curto: str,
    ref_lat: float = REF_LAT,
    ref_lon: float = REF_LON,
) -> tuple[tuple[float, float], str]:
    codigo_completo = olc.recoverNearest(codigo_curto, ref_lat, ref_lon)
    area = olc.decode(codigo_completo)
    return (area.latitudeCenter, area.longitudeCenter), codigo_completo


def preparar_unidades(unidades=UNIDADES) -> list[dict]:
    unidades_preparadas = []

    for unidade in unidades:
        unidade_preparada = unidade.copy()
        coords, plus_code_completo = plus_code_para_coords(unidade["plus_code"])
        unidade_preparada["coords"] = coords
        unidade_preparada["plus_code_completo"] = plus_code_completo
        unidades_preparadas.append(unidade_preparada)

    return unidades_preparadas


def formatar_endereco(endereco: dict[str, str]) -> str:
    return (
        f"{endereco['logradouro']}, {endereco['numero']} — "
        f"{endereco['bairro']}, {endereco['cidade']}/{endereco['uf']} — "
        f"CEP {endereco['cep']}"
    )


def serializar_ponto(ponto: dict, categoria: str) -> dict[str, object]:
    latitude, longitude = ponto["coords"]
    resultado: dict[str, object] = {
        "nome": ponto["nome"],
        "tipo": ponto["tipo"],
        "categoria": categoria,
        "endereco": ponto["endereco"].copy(),
        "endereco_formatado": formatar_endereco(ponto["endereco"]),
        "coordenadas": {
            "latitude": latitude,
            "longitude": longitude,
        },
    }

    if ponto.get("prioridade") is not None:
        prioridade = int(ponto["prioridade"])
        resultado["prioridade"] = prioridade
        resultado["prioridade_rotulo"] = {
            1: "alta",
            2: "media",
            3: "normal",
        }.get(prioridade, f"nivel {prioridade}")

    if ponto.get("demanda_kg") is not None:
        resultado["demanda_kg"] = float(ponto["demanda_kg"])

    if ponto.get("plus_code"):
        resultado["plus_code"] = ponto["plus_code"]
        resultado["plus_code_completo"] = ponto["plus_code_completo"]

    if ponto.get("situacao"):
        resultado["situacao"] = ponto["situacao"]

    if ponto.get("observacao"):
        resultado["observacao"] = ponto["observacao"]

    return resultado


def listar_pontos(
    tipo: str | None = None,
    incluir_sede: bool = True,
) -> dict[str, object]:
    pontos = []

    if incluir_sede:
        pontos.append(serializar_ponto(SEDE, "sede"))

    pontos.extend(
        serializar_ponto(unidade, "unidade_de_entrega")
        for unidade in preparar_unidades()
    )

    if tipo:
        tipo_normalizado = normalizar_texto(tipo)
        pontos = [
            ponto
            for ponto in pontos
            if tipo_normalizado in normalizar_texto(str(ponto["tipo"]))
        ]

    return {
        "total": len(pontos),
        "filtro_tipo": tipo,
        "inclui_sede": incluir_sede,
        "pontos": pontos,
    }


def consultar_ponto(nome: str) -> dict[str, object]:
    termo = normalizar_texto(nome)
    pontos = listar_pontos()["pontos"]

    if not termo:
        return {
            "encontrado": False,
            "motivo": "Informe ao menos uma parte do nome do ponto.",
        }

    correspondencias_exatas = [
        ponto
        for ponto in pontos
        if normalizar_texto(str(ponto["nome"])) == termo
    ]
    if correspondencias_exatas:
        return {
            "encontrado": True,
            "ponto": correspondencias_exatas[0],
        }

    correspondencias_parciais = [
        ponto
        for ponto in pontos
        if termo in normalizar_texto(str(ponto["nome"]))
    ]

    if len(correspondencias_parciais) == 1:
        return {
            "encontrado": True,
            "ponto": correspondencias_parciais[0],
        }

    if correspondencias_parciais:
        return {
            "encontrado": False,
            "motivo": "O nome informado corresponde a mais de um ponto.",
            "candidatos": [
                ponto["nome"]
                for ponto in correspondencias_parciais
            ],
        }

    return {
        "encontrado": False,
        "motivo": f"Nenhum ponto encontrado para: {nome}",
        "pontos_disponiveis": [ponto["nome"] for ponto in pontos],
    }


def buscar_unidade(nome_local: str, unidades: list[dict]) -> dict:
    nome_normalizado = normalizar_texto(nome_local)
    unidades_por_nome = {
        normalizar_texto(unidade["nome"]): unidade
        for unidade in unidades
    }

    if nome_normalizado in unidades_por_nome:
        return unidades_por_nome[nome_normalizado]

    candidatas = [
        unidade
        for unidade in unidades
        if nome_normalizado in normalizar_texto(unidade["nome"])
    ]

    if len(candidatas) == 1:
        return candidatas[0]

    if not candidatas:
        nomes_disponiveis = "\n".join(
            f"- {unidade['nome']}"
            for unidade in unidades
        )
        raise ValueError(
            f"Local nao encontrado: {nome_local}\n\n"
            f"Locais disponiveis:\n{nomes_disponiveis}"
        )

    nomes_candidatos = "\n".join(
        f"- {unidade['nome']}"
        for unidade in candidatas
    )
    raise ValueError(
        f"O texto '{nome_local}' encontrou mais de uma unidade. "
        f"Use um nome mais especifico:\n{nomes_candidatos}"
    )
