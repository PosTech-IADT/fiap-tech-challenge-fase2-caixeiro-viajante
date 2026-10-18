# Otimizador de rotas hospitalares

Projeto para calcular a melhor rota de entrega saindo sempre da sede e visitando as unidades selecionadas.

## Como usar

1. Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

2. Instale/atualize as dependencias:

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
- `route_engine/maps.py`: geração do mapa de unidades e do mapa animado em HTML.
- `main.ipynb`: notebook usado para exploracao, testes e visualizacao.
- `requirements.txt`: dependencias Python do projeto.
- `cache/`: cache usado pelo OSMnx/OpenStreetMap para acelerar novas execucoes.

## Servidor MCP com Docker

O servidor MCP fica em `mcp_server/` e usa o transporte SSE.
Ele expoe as ferramentas `ping`, `listar_pontos_entrega`,
`consultar_ponto_entrega`, `gerar_mapa_pontos` e
`calcular_rota_entrega` no endpoint
`http://localhost:8000/sse`.

A ferramenta `gerar_mapa_pontos` cria o mapa interativo em
`mcp_server/output/mapa_pontos.html`.

A ferramenta `calcular_rota_entrega` recebe os nomes dos pontos e a confirmacao
de saida da sede. Ela retorna a melhor ordem das paradas, a distancia total e
cria o mapa em `mcp_server/output/mapa_rota.html`.

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
docker compose exec mcp-server python test_client.py
```

Para acompanhar os logs ou encerrar o servidor:

```bash
docker compose logs -f mcp-server
docker compose down
```

## Frontend do agente

O frontend Streamlit fica em `route_agent/` e roda em um container separado.
Ele utiliza o OpenAI Agents SDK e se conecta ao MCP Server por SSE.

Crie o arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Preencha `OPENAI_API_KEY` e suba os containers com Docker Compose. O frontend
ficara disponivel em `http://localhost:8501`.

Quando a tool `gerar_mapa_pontos` for chamada, o mapa salvo pelo MCP Server e
renderizado diretamente na interface do agente.

### Instrucoes e relatorios com LLM

O agente usa a LLM para transformar dados retornados pelas tools em instrucoes
de entrega e relatorios operacionais, sem criar metricas que nao existam no
motor de rotas. Exemplos de pedidos no chat:

- "Gere instrucoes para o motorista para a rota saindo da sede ate HCor e IGESP";
- "Gere o relatorio diario de eficiencia das rotas";
- "Quais melhorias voce sugere com base no relatorio semanal?".

Cada calculo bem-sucedido e registrado em
`mcp_server/output/historico_rotas.json` (arquivo local ignorado pelo Git). Os
relatorios agregam quantidade de rotas, paradas, viagens, distancia e a economia
de distancia frente a ordem originalmente informada. Tempo real, combustivel e
custos nao sao estimados porque o projeto nao coleta esses dados.
