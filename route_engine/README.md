# Route Engine

O motor calcula rotas reais sobre a malha viaria do OpenStreetMap e usa um
algoritmo genetico para definir a ordem das entregas.

## Algoritmo genetico

Cada individuo da populacao representa uma permutacao dos pontos de entrega.
A implementacao fica em `genetic_algorithm.py`, seguindo os nomes do codigo-base
da FIAP: `generate_random_population`, `calculate_fitness`, `order_crossover`,
`mutate` e `sort_population`. As funcoes foram ampliadas para o problema
hospitalar sem perder a correspondencia com o ponto de partida fornecido.

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

## API pública

As chamadas abaixo são expostas diretamente pelo pacote route_engine e são as
recomendadas para notebooks, scripts e integrações Python. As funções internas
de engine.py, maps.py, points.py e genetic_algorithm.py não fazem parte da API
de negócio estável.

### Constantes

~~~python
from route_engine import (
    CONFIGURACAO_ALGORITMO_GENETICO,
    SEDE,
    UNIDADES,
    VEICULO_PADRAO,
)
~~~

| Nome | Conteúdo |
| --- | --- |
| SEDE | Origem operacional: nome, tipo, endereço e coordenadas. |
| UNIDADES | Cadastro-base: Plus Code, prioridade e demanda. |
| VEICULO_PADRAO | Capacidade e autonomia aplicadas sem sobrescrita. |
| CONFIGURACAO_ALGORITMO_GENETICO | População, gerações, mutação, elitismo, semente e pesos de fitness. |

### listar_unidades()

Retorna as unidades prontas para uso. Cada item recebe coords (latitude,
longitude) e plus_code_completo, derivados do Plus Code curto.

~~~python
from route_engine import listar_unidades

unidades = listar_unidades()
print(unidades[0]["nome"])
~~~

**Retorno:** lista de dicionários. A chamada não altera o cadastro original
UNIDADES.

### exibir_mapa_unidades()

Cria um mapa Folium com a sede e todas as unidades.

~~~python
from route_engine import exibir_mapa_unidades

mapa = exibir_mapa_unidades()
mapa.save("mapa_unidades.html")  # opcional
~~~

**Retorno:** folium.Map. Em um notebook, deixe mapa como última linha da célula
para renderizá-lo.

### calcular_melhor_rota_entrega(...)

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
- `comparativo_referencia`: distância da ordem informada e economia obtida
  pela otimização.

#### Parâmetros

| Parâmetro | Obrigatório | Descrição |
| --- | --- | --- |
| nomes_locais | Sim | Lista de nomes completos ou trechos não ambíguos. A rota sempre sai da sede. |
| capacidade_kg | Não | Capacidade do veículo. Padrão: VEICULO_PADRAO["capacidade_kg"]. |
| autonomia_km | Não | Limite por viagem, incluindo retorno. Padrão: VEICULO_PADRAO["autonomia_km"]. |
| prioridades | Não | Dicionário {nome: prioridade}; 1 é alta, 2 média e 3 normal. |
| demandas_kg | Não | Dicionário {nome: peso_em_kg}. |
| configuracao_ga | Não | Sobrescreve tamanho_populacao, geracoes, taxa_mutacao, tamanho_torneio, elitismo e semente. |

Prioridades, demandas e configuração genética sobrescrevem os valores somente
na execução atual.

Os itens de rota incluem nome, tipo, endereco, coords, prioridade,
prioridade_rotulo, demanda_kg, viagem e ordem_na_viagem. Cada item de viagens
contém carga, distância, paradas e coordenadas do percurso.

**Erros:** a função lança ValueError para lista vazia, unidade duplicada, nome
inexistente ou ambíguo, prioridade inválida, demanda negativa ou rota inviável.

### criar_mapa_rota(resultado)

Gera um mapa Folium a partir do resultado de calcular_melhor_rota_entrega. Cada
viagem possui uma cor e linha animada.

~~~python
from route_engine import calcular_melhor_rota_entrega, criar_mapa_rota

resultado = calcular_melhor_rota_entrega(["HCor", "Hospital IGESP Paulista"])
criar_mapa_rota(resultado).save("rota_entrega.html")
~~~

**Parâmetro:** dicionário retornado pelo cálculo. **Retorno:** folium.Map.

### Fluxo recomendado

~~~python
from route_engine import calcular_melhor_rota_entrega, criar_mapa_rota

resultado = calcular_melhor_rota_entrega(
    ["HCor", "Hospital IGESP Paulista", "UBS Humaitá"],
    capacidade_kg=80,
    autonomia_km=30,
)

for viagem in resultado["viagens"]:
    print(viagem["numero"], viagem["distancia_km"])

criar_mapa_rota(resultado).save("rota_entrega.html")
~~~

## Testes

Os testes automatizados cobrem operadores geneticos, fitness, restricoes,
cadastro de pontos, integracao interna do engine e mapas. A suite usa dados e
grafos locais, sem acessar a rede ou o OpenStreetMap.

Instale as dependencias de desenvolvimento e execute a partir da raiz:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```
