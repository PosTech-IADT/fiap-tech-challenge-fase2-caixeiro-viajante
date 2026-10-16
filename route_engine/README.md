# Route Engine

O motor calcula rotas reais sobre a malha viaria do OpenStreetMap e usa um
algoritmo genetico para definir a ordem das entregas.

## Algoritmo genetico

Cada individuo da populacao representa uma permutacao dos pontos de entrega.
A evolucao utiliza:

- selecao por torneio;
- cruzamento ordenado (OX), que preserva uma rota sem pontos repetidos;
- mutacao por troca ou inversao de trecho;
- elitismo para manter as melhores solucoes;
- semente configuravel para permitir resultados reproduziveis.

A funcao de fitness combina a distancia total, o atraso de entregas prioritarias
e penalidades por inversao de prioridade ou por restricoes inviaveis.

## Restricoes operacionais

- **Prioridade:** `1` e a maior prioridade. Entregas urgentes recebem penalidade
  quando aparecem depois de entregas menos prioritarias.
- **Capacidade:** cada unidade possui `demanda_kg`. Quando a proxima entrega
  excederia a capacidade do veiculo, a viagem retorna para a sede e uma nova
  viagem e iniciada.
- **Autonomia:** cada viagem precisa sair da sede, atender suas paradas e ter
  autonomia suficiente para retornar. Se necessario, o percurso e dividido em
  mais viagens.
- **Inviabilidade:** uma demanda maior que a capacidade do veiculo, ou um ponto
  cuja ida e volta exceda a autonomia, gera um erro explicativo.

Os valores padrao ficam em `data.py`, nos dicionarios `VEICULO_PADRAO` e
`CONFIGURACAO_ALGORITMO_GENETICO`. As cargas cadastradas sao demonstrativas e
devem ser substituidas pelos valores reais da operacao quando estiverem
disponiveis.

## Uso

```python
from route_engine import calcular_melhor_rota_entrega

resultado = calcular_melhor_rota_entrega(
    [
        "Hospital Alemão Oswaldo Cruz",
        "HCor - Hospital do Coração",
        "UBS Humaitá",
    ],
    capacidade_kg=80,
    autonomia_km=30,
    prioridades={
        "HCor - Hospital do Coração": 1,
        "UBS Humaitá": 3,
    },
    demandas_kg={
        "HCor - Hospital do Coração": 40,
        "UBS Humaitá": 10,
    },
)
```

O resultado mantem os campos anteriores (`rota`, `distancia_total_km` e
`coordenadas_rota`) e acrescenta:

- `viagens`: divisao do percurso, carga e distancia de cada saida;
- `coordenadas_por_viagem`: percurso separado para desenhar cada viagem com
  uma cor propria no mapa;
- `total_viagens`: quantidade de saidas necessarias;
- `restricoes`: capacidade, autonomia e demanda total consideradas;
- `algoritmo`: configuracao e metadados da execucao do algoritmo genetico.
