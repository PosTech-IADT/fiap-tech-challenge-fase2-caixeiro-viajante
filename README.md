# Otimizador de rotas hospitalares

Projeto para calcular a melhor rota de entrega saindo sempre da sede e visitando as unidades selecionadas.

## Evolução do código-base da FIAP

Este projeto foi desenvolvido a partir dos conceitos e operadores apresentados
no código-base
[`FIAP/genetic_algorithm_tsp`](https://github.com/FIAP/genetic_algorithm_tsp).
O exemplo original resolve o TSP sobre pontos cartesianos e usa distância em
linha reta. Nesta evolução, a mesma estrutura genética foi adaptada para o
contexto hospitalar e para trajetos sobre ruas reais do OpenStreetMap.

Os nomes centrais foram mantidos para tornar essa evolução rastreável:

| Código-base | Implementação deste projeto | Evolução realizada |
| --- | --- | --- |
| `genetic_algorithm.py` | `route_engine/genetic_algorithm.py` | Núcleo genético modular e testável |
| `generate_random_population` | `generate_random_population` | Inclui um indivíduo inicial heurístico |
| `calculate_fitness` | `calculate_fitness` | Considera ruas, prioridade, carga e autonomia |
| `order_crossover` | `order_crossover` | Combina dois pais e preserva rotas válidas |
| `mutate` | `mutate` | Aplica mutação por troca ou inversão |
| `sort_population` | `sort_population` | Ordena indivíduos pelo fitness ampliado |

O Pygame do exemplo foi substituído por mapas Folium. O cálculo euclidiano em
pixels foi substituído por uma matriz de menores caminhos calculada com OSMnx e
NetworkX. A API de negócio continua em português para representar o domínio de
entregas hospitalares.

## Como executar o projeto

A forma recomendada de executar a aplicação completa é com Docker Compose. Esse
modo inicia o servidor MCP e a interface Streamlit do agente.

### 1. Verifique os pré-requisitos

Antes de iniciar, tenha instalado:

- Docker Desktop, com o Docker Compose habilitado;
- Git;
- uma chave de API da OpenAI.

Confirme que o Docker está em execução:

```bash
docker --version
docker compose version
```

### 2. Acesse a pasta do projeto

Depois de clonar ou baixar o repositório, abra um terminal na raiz do projeto:

```bash
cd fiap-tech-challenger-fase2
```

Os comandos seguintes devem ser executados nessa pasta, onde está localizado o
arquivo `docker-compose.yml`.

### 3. Configure as variáveis de ambiente

Crie o arquivo `.env` a partir do exemplo fornecido:

```bash
cp .env.example .env
```

Abra o arquivo `.env` e substitua o valor de exemplo pela sua chave:

```dotenv
OPENAI_API_KEY=coloque_sua_chave_aqui
```

Não adicione o arquivo `.env` ao Git, pois ele contém uma credencial privada.

### 4. Faça o build e inicie os containers

```bash
docker compose up --build -d
```

Na primeira execução, o Docker baixa as imagens e instala as dependências, por
isso o processo pode levar alguns minutos.

### 5. Confira se os serviços estão ativos

```bash
docker compose ps
```

Os serviços `mcp-server` e `route-agent` devem aparecer como ativos. O servidor
MCP também deve apresentar o estado `healthy`.

Se algum serviço não iniciar, consulte os logs:

```bash
docker compose logs -f
```

Use `Ctrl+C` para sair da visualização dos logs sem encerrar os containers.

### 6. Abra a aplicação

Acesse no navegador:

- Route Assistant: [http://localhost:8501](http://localhost:8501);
- servidor MCP via SSE: [http://localhost:8000/sse](http://localhost:8000/sse).

Na interface do Route Assistant, envie uma pergunta sobre as unidades ou
solicite uma rota. Por exemplo:

```text
Calcule a melhor rota a partir da sede para o HCor e o Hospital IGESP Paulista.
```

### 7. Encerre a aplicação

Quando terminar, pare e remova os containers:

```bash
docker compose down
```

Para iniciar novamente sem reconstruir as imagens:

```bash
docker compose up -d
```

Depois de alterar o código ou as dependências, reconstrua as imagens:

```bash
docker compose up --build -d
```

## Execução local do motor de rotas (opcional)

Este modo executa apenas o script Python do motor de rotas, sem iniciar a
interface Streamlit nem o servidor MCP.

1. Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

2. Instale/atualize as dependências:

```bash
pip install -r requirements.txt
```

3. Edite a lista `LOCAIS_ENTREGA` no arquivo `main.py`:

```python
LOCAIS_ENTREGA = [
    "Hospital IGESP Paulista",
    "HCor - Hospital do Coração",
    "Hospital Luz Vila Mariana",
]
```

4. Execute:

```bash
python main.py
```

O script imprime a melhor ordem de visita no terminal e gera o arquivo `rota_entrega.html` com o mapa animado da rota.

## Uso pelo notebook

Para mostrar o mapa com todos os pontos cadastrados:

```python
from route_engine import exibir_mapa_unidades

exibir_mapa_unidades()
```

Para calcular uma rota de entrega e mostrar o mapa:

```python
from route_engine import calcular_melhor_rota_entrega, criar_mapa_rota

resultado = calcular_melhor_rota_entrega([
    "Hospital IGESP Paulista",
    "HCor - Hospital do Coração",
    "Hospital Luz Vila Mariana",
])

criar_mapa_rota(resultado)
```

## Arquivos principais

- `main.py`: ponto de entrada para calcular uma entrega.
- `route_engine/`: motor de rotas usado pelo `main.py` e pelos futuros serviços.
- `route_engine/data.py`: cadastro da sede e das unidades.
- `route_engine/engine.py`: cálculo da melhor rota pelas ruas.
- `route_engine/genetic_algorithm.py`: evolução do algoritmo genético fornecido
  pela FIAP, com operadores especializados e restrições hospitalares.
- `route_engine/maps.py`: geração do mapa de unidades e do mapa animado em HTML.
- `main.ipynb`: notebook usado para exploração, testes e visualização.
- `requirements.txt`: dependências Python do projeto.
- `cache/`: cache usado pelo OSMnx/OpenStreetMap para acelerar novas execuções.

## Servidor MCP com Docker

O servidor MCP fica em `mcp_server/` e usa o transporte SSE.
Ele expõe as ferramentas `ping`, `listar_pontos_entrega`,
`consultar_ponto_entrega`, `gerar_mapa_pontos` e
`calcular_rota_entrega` (descontinuada), `otimizar_rota_genetica` e
`gerar_relatorio_operacional` no endpoint
`http://localhost:8000/sse`.

A ferramenta `gerar_mapa_pontos` cria o mapa interativo em
`mcp_server/output/mapa_pontos.html`.

A ferramenta `calcular_rota_entrega` recebe os nomes dos pontos e a confirmação
de saída da sede. Ela retorna a melhor ordem das paradas, a distância total e
cria o mapa em `mcp_server/output/mapa_rota.html`. Essa ferramenta está
descontinuada, permanece disponível apenas para clientes antigos e não é
exposta ao Route Assistant. Novas integrações devem usar
`otimizar_rota_genetica`.

A ferramenta `otimizar_rota_genetica` também recebe capacidade e autonomia do
veículo, além de demandas e prioridades por unidade. Prioridade 1 representa
criticidade alta, 2 média e 3 normal. Parâmetros técnicos do algoritmo podem
ser enviados em `configuracao_ga`, mas devem permanecer nos valores padrão
quando o usuário não solicitar sua alteração.

No MCP Inspector, selecione o transporte `SSE` e use a URL acima.

Suba o servidor a partir da raiz do projeto:

```bash
docker compose up --build -d
```

Confira o estado do container:

```bash
docker compose ps
```

Execute o cliente de teste dentro do container:

```bash
docker compose exec mcp-server python mcp_server/test_client.py
```

Para acompanhar os logs ou encerrar o servidor:

```bash
docker compose logs -f mcp-server
docker compose down
```

## Frontend do agente

O frontend Streamlit fica em `route_agent/` e roda em um container separado.
Ele utiliza o OpenAI Agents SDK com o modelo `gpt-5.4-mini`, raciocínio
configurado como `low` e respostas de baixa verbosidade. O agente se conecta
ao MCP Server por SSE.

Chamadas demoradas ao MCP usam um timeout configurável pela variável
`MCP_CLIENT_TIMEOUT_SECONDS`. O valor padrão no Docker Compose é de 300
segundos. Esse limite pertence ao Route Assistant; clientes externos, como o
MCP Inspector, possuem seu próprio timeout e devem ser configurados
separadamente.

Crie o arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Preencha `OPENAI_API_KEY` e suba os containers com Docker Compose. O frontend
ficará disponível em `http://localhost:8501`.

Quando a tool `gerar_mapa_pontos` for chamada, o mapa salvo pelo MCP Server é
renderizado diretamente na interface do agente.

### Instruções e relatórios com LLM

O agente usa a LLM para transformar dados retornados pelas tools em instruções
de entrega e relatórios operacionais, sem criar métricas que não existam no
motor de rotas. Exemplos de pedidos no chat:

- "Gere instruções para o motorista para a rota saindo da sede até HCor e IGESP";
- "Otimize a rota saindo da sede para HCor e IGESP com capacidade de 50 kg,
  autonomia de 30 km e informe peso e criticidade de cada parada";
- "Gere o relatório diário de eficiência das rotas";
- "Quais melhorias você sugere com base no relatório semanal?".

Cada cálculo bem-sucedido é registrado em
`mcp_server/output/historico_rotas.json` (arquivo local ignorado pelo Git). Os
relatórios agregam quantidade de rotas, paradas, viagens, distância e a economia
de distância frente à ordem originalmente informada. Tempo real, combustível e
custos não são estimados porque o projeto não coleta esses dados.
