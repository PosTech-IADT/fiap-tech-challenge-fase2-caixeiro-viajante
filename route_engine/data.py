REF_LAT = -23.5560
REF_LON = -46.6450

# Parametros operacionais usados quando nenhum valor e informado ao engine.
# Os valores de carga sao demonstrativos e podem ser ajustados conforme a
# operacao real sem alterar o algoritmo.
VEICULO_PADRAO = {
    "capacidade_kg": 120.0,
    "autonomia_km": 45.0,
}

CONFIGURACAO_ALGORITMO_GENETICO = {
    "tamanho_populacao": 120,
    # Criterio de parada: numero fixo de geracoes.
    "geracoes": 300,
    # Probabilidade de aplicar mutacao Swap ou inversao em cada filho.
    "taxa_mutacao": 0.18,
    # Quantidade de candidatos sorteados na selecao por torneio.
    "tamanho_torneio": 5,
    # Quantidade de melhores individuos preservados por elitismo.
    "elitismo": 4,
    # Torna as escolhas aleatorias reproduziveis.
    "semente": 42,
    # Pesos utilizados pelo fitness para tratar a prioridade das entregas.
    "penalidade_inversao_prioridade_m": 5_000.0,
    "peso_atraso_prioridade": 0.35,
}

SEDE = {
    "nome": "Hub Logístico Saúde Centro",
    "tipo": "Sede de início das entregas",
    "coords": (-23.55052, -46.63331),
    "endereco": {
        "logradouro": "Praça da Sé",
        "numero": "s/n",
        "bairro": "Sé",
        "cidade": "São Paulo",
        "uf": "SP",
        "cep": "01001-000",
    },
    "observacao": (
        "Ponto operacional de referência da aplicação; não representa um "
        "estabelecimento real cadastrado nesse endereço."
    ),
}

UNIDADES = [
    {
        "nome": "Hospital Leforte Liberdade",
        "tipo": "Hospital Geral",
        "plus_code": "C9R8+R3",
        "prioridade": 2,
        "demanda_kg": 35.0,
        "endereco": {
            "logradouro": "Rua Barão de Iguape",
            "numero": "209",
            "bairro": "Liberdade",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01507-000",
        },
    },
    {
        "nome": "Hospital Alemão Oswaldo Cruz",
        "tipo": "Hospital Privado",
        "plus_code": "C9J4+7Q",
        "prioridade": 1,
        "demanda_kg": 30.0,
        "endereco": {
            "logradouro": "Rua João Julião",
            "numero": "331",
            "bairro": "Paraíso",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01323-903",
        },
    },
    {
        "nome": "Hospital Pró Matre Paulista",
        "tipo": "Maternidade",
        "plus_code": "C9M2+R2",
        "prioridade": 1,
        "demanda_kg": 25.0,
        "endereco": {
            "logradouro": "Rua São Carlos do Pinhal",
            "numero": "174",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01333-001",
        },
    },
    {
        "nome": "Hospital TotalCor",
        "tipo": "Hospital Cardiológico",
        "plus_code": "C8MX+2M",
        "prioridade": 3,
        "demanda_kg": 20.0,
        "endereco": {
            "logradouro": "Alameda Santos",
            "numero": "764",
            "bairro": "Cerqueira César",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01418-100",
        },
    },
    {
        "nome": "Hospital Samaritano Paulista",
        "tipo": "Hospital Geral",
        "plus_code": "C9M3+X7",
        "prioridade": 2,
        "demanda_kg": 30.0,
        "endereco": {
            "logradouro": "Rua Doutor Fausto Ferraz",
            "numero": "204-232",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01333-030",
        },
    },
    {
        "nome": "Hospital IGESP Paulista",
        "tipo": "Hospital Geral",
        "plus_code": "C8QX+PP",
        "prioridade": 2,
        "demanda_kg": 25.0,
        "endereco": {
            "logradouro": "Rua Sílvia",
            "numero": "276",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01331-010",
        },
    },
    {
        "nome": "HCor - Hospital do Coração",
        "tipo": "Hospital Cardiológico",
        "plus_code": "C9G4+RG",
        "prioridade": 1,
        "demanda_kg": 35.0,
        "endereco": {
            "logradouro": "Rua Desembargador Eliseu Guilherme",
            "numero": "147",
            "bairro": "Paraíso",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "04004-030",
        },
    },
    {
        "nome": "Hospital Luz Vila Mariana",
        "tipo": "Hospital Geral",
        "plus_code": "C995+CV",
        "prioridade": 2,
        "demanda_kg": 25.0,
        "endereco": {
            "logradouro": "Rua Azevedo Macedo",
            "numero": "113",
            "bairro": "Vila Mariana",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "04013-060",
        },
    },
    {
        "nome": "UBS Humaitá",
        "tipo": "UBS / Posto de Saúde",
        "plus_code": "C9V5+66",
        "prioridade": 3,
        "demanda_kg": 15.0,
        "endereco": {
            "logradouro": "Rua Humaitá",
            "numero": "520",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01321-010",
        },
    },
    {
        "nome": "Hospital Municipal Infantil Menino Jesus",
        "tipo": "Hospital Infantil",
        "plus_code": "C9Q3+W2",
        "prioridade": 1,
        "demanda_kg": 30.0,
        "endereco": {
            "logradouro": "Rua dos Franceses",
            "numero": "251",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01329-010",
        },
    },
    {
        "nome": "UBS Nossa Senhora do Brasil",
        "tipo": "UBS / Posto de Saúde",
        "plus_code": "C9P2+W7",
        "prioridade": 3,
        "demanda_kg": 15.0,
        "endereco": {
            "logradouro": "Rua Almirante Marques Leão",
            "numero": "684",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01330-010",
        },
    },
    {
        "nome": "Hospital Santa Catarina - Paulista",
        "tipo": "Hospital",
        "plus_code": "C9J3+2Q",
        "prioridade": 2,
        "demanda_kg": 35.0,
        "endereco": {
            "logradouro": "Avenida Paulista",
            "numero": "200",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01310-000",
        },
    },
]
