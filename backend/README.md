# Backend: API e modelo de dados da PoC de saúde de bateria

API em FastAPI e banco PostgreSQL que recebem a telemetria de bateria de uma frota simulada de
smartphones Android, guardam o histórico como série temporal e registram as predições de vida
útil restante (RUL) produzidas pelo modelo de aprendizado de máquina.

## Stack

| Componente | Versão usada no desenvolvimento |
|---|---|
| Python | 3.11 |
| FastAPI | 0.141 |
| SQLAlchemy | 2.1 |
| Pydantic | 2.13 |
| psycopg | 3.3 |
| PostgreSQL | 16 |

## Como rodar

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
docker compose up -d          # Postgres 16 com o schema aplicado na primeira subida
cp .env.example .env
uvicorn app.main:app --reload # documentação interativa em http://localhost:8000/docs
```

Sem Docker, aplique `db/schema.sql` em um PostgreSQL 16 existente ou rode `python -m app.init_db`.

Testes rodam sem banco, usando SQLite em memória:

```bash
pytest
```

## Modelo de dados

```
device 1 --- N battery_telemetry
device 1 --- N battery_prediction N --- 1 ml_model
                                 N --- 1 risk_policy
```

| Tabela | O que guarda |
|---|---|
| `device` | aparelho identificado só por um código pseudonimizado no formato `DEV-0001` |
| `battery_telemetry` | uma leitura de bateria por aparelho e instante; única em `(device_id, recorded_at)` |
| `ml_model` | versão do modelo treinado, algoritmo, métricas, hiperparâmetros e features |
| `risk_policy` | limiares em ciclos que convertem o RUL em faixa de risco; só uma política ativa |
| `battery_prediction` | RUL estimado, faixa de risco, modelo usado e snapshot das features |

Três conceitos ficam em colunas distintas e não devem ser confundidos: `battery_level_pct` é a
carga no instante da leitura, `estimated_capacity_pct` é a capacidade em relação à nominal (proxy
de estado de saúde, SOH) e `rul_cycles` é a estimativa de ciclos restantes até o critério de fim
de vida.

Toda leitura carrega a coluna `source` com valor `synthetic` ou `real`. Nesta fase todos os dados
são sintéticos e o limiar da política `experimental-v1` é um valor provisório, não validado com a
operação.

## Endpoints

| Método e rota | Uso |
|---|---|
| `GET /health` | verificação de vida |
| `POST /telemetry` | ingestão em lote de até 5.000 leituras; registra aparelho desconhecido e ignora leitura repetida |
| `GET /devices` | lista de aparelhos |
| `GET /devices/{code}` | aparelho com a predição mais recente |
| `GET /devices/{code}/telemetry?since=&limit=` | histórico do mais recente ao mais antigo |
| `POST /models` e `GET /models` | registro e lista de modelos treinados |
| `POST /predictions` | grava uma predição e calcula a faixa de risco pela política ativa |
| `GET /devices/{code}/predictions` | histórico de predições do aparelho |
| `GET /predictions/summary` | contagem por faixa considerando a última predição de cada aparelho |

Exemplo de lote de telemetria:

```json
{
  "readings": [
    {
      "device_code": "DEV-0001",
      "recorded_at": "2026-09-20T10:00:00Z",
      "battery_level_pct": 78,
      "battery_temp_c": 31.2,
      "voltage_mv": 3900,
      "is_charging": false,
      "cycle_count": 184,
      "estimated_capacity_pct": 94.0,
      "ram_available_mb": 1536,
      "network_rx_mb": 12.5,
      "network_tx_mb": 3.25
    }
  ]
}
```

## Privacidade

O schema não tem coluna de identificação pessoal. O simulador gera o código do aparelho; em um
cenário com dados reais, o mapeamento entre código e aparelho físico fica fora deste banco.

## Qualidade

```bash
pytest
ruff check . && ruff format --check .
bandit -r app -ll
```

## Verificação

Nível 3 em 2026-09-27: `pytest` com 35 testes passando e `db/schema.sql` aplicada duas vezes em um
container `postgres:16-alpine` (PostgreSQL 16.15), com paridade de colunas entre DDL e ORM e
constraints de unicidade e CHECK comprovadas por inserções rejeitadas.
