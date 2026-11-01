# Backend: API e modelo de dados da PoC de saúde de bateria

API em FastAPI e banco PostgreSQL que recebem a telemetria de bateria de uma frota simulada de
smartphones Android, guardam o histórico como série temporal e registram as predições de vida
útil restante (RUL) produzidas pelo modelo de aprendizado de máquina.

## Stack

| Componente | Versão usada no desenvolvimento |
|---|---|
| Python | 3.12 |
| FastAPI | 0.141 |
| SQLAlchemy | 2.1 |
| Pydantic | 2.13 |
| psycopg | 3.3 |
| PostgreSQL | 16 |
| scikit-learn, joblib, numpy, pandas | 1.9.1, 1.6.0, 2.5.3, 3.0.6 (as versões usadas no treino do modelo) |

## Como rodar

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev]"
docker compose up -d          # Postgres 16 com o schema aplicado na primeira subida
cp .env.example .env
uvicorn app.main:app --reload # documentação interativa em http://localhost:8000/docs
```

Se a porta 5432 já estiver em uso na sua máquina, defina `DB_PORT` no `.env` (por exemplo
`DB_PORT=5439`) e use a mesma porta no `DATABASE_URL`. O compose lê o `.env` automaticamente.

Sem Docker, aplique `db/schema.sql` em um PostgreSQL 16 existente ou rode `python -m app.init_db`.

Testes rodam sem banco, usando SQLite em memória:

```bash
pytest
```

## Demonstração em um comando

Com a API no ar e o banco vazio:

```bash
python scripts/run_demo_pipeline.py
```

O comando gera a telemetria sintética, se ainda não existir, envia os dados dos 80 aparelhos que o
modelo não viu no treino para `POST /telemetry` e pede predições a cada 30 dias de histórico, além
da última. Levou 58 s na máquina de desenvolvimento e termina com 59 aparelhos em `low`, 17 em
`medium` e 4 em `high`. O roteiro completo está em `docs/relatorios/demonstracao.md`.

Para recomeçar do zero, recrie o banco com `docker compose down -v` e `docker compose up -d`.

## Modelo de dados

```
device 1 --- N battery_telemetry
device 1 --- N battery_prediction N --- 1 ml_model
                                 N --- 1 risk_policy
```

| Tabela | O que guarda |
|---|---|
| `device` | aparelho identificado só por um código pseudonimizado no formato `DEVICE-0001` |
| `battery_telemetry` | uma leitura de bateria por aparelho e instante; inclui `deep_discharge_count` para permitir a feature `deep_discharge_events_30d`; única em `(device_id, recorded_at)` |
| `ml_model` | versão do modelo treinado, algoritmo, métricas, hiperparâmetros e features |
| `risk_policy` | limiares em ciclos que convertem o RUL em faixa de risco; só uma política ativa |
| `battery_prediction` | RUL estimado, faixa de risco, modelo usado e snapshot das features |

Três conceitos ficam em colunas distintas e não devem ser confundidos: `battery_level_pct` é a
carga no instante da leitura, `estimated_capacity_pct` é a capacidade em relação à nominal (proxy
de estado de saúde, SOH) e `rul_cycles` é a estimativa de ciclos restantes até o critério de fim
de vida.

Toda leitura carrega a coluna `source` com valor `synthetic` ou `real`. Nesta fase todos os dados
são sintéticos. A política `experimental-v2` usa 776 e 983 ciclos, os percentis 10 e 33 do RUL dos
aparelhos de desenvolvimento, reproduzidos por `ml/evaluation/calibrate_risk_policy.py`. Os limiares
ordenam os aparelhos dentro da frota sintética e não foram validados com a operação. As limitações
estão em `docs/relatorios/validacao-e-limitacoes.md`.

## Inferência

`POST /devices/{code}/predictions/run` lê o histórico gravado no banco, agrega por dia, calcula as 17
features com as mesmas janelas de 7 e 30 dias do treino, executa o Random Forest V2.2 ajustado e grava
a predição com a faixa de risco. O parâmetro opcional `as_of` limita o histórico a um instante. A
execução é sob demanda: não há processamento contínuo a cada leitura.

O modelo fica em `ml/artifacts/v2_2_tuned/`, é carregado uma vez por processo e registrado em
`ml_model` na primeira predição. Um teste compara as features calculadas aqui com a saída do pipeline
de ML. Em 400 aparelhos, 13 das 17 features são idênticas; as 4 de ciclos diários desviam no máximo
0,006, porque o conjunto de dados arredonda `cycle_count` para duas casas.

| Situação | Resposta |
|---|---|
| Aparelho inexistente | 404 |
| Menos de 31 dias de telemetria, ou lacuna nos últimos 31 dias | 422 |
| Arquivo do modelo ausente | 503 |

## Endpoints

| Método e rota | Uso |
|---|---|
| `GET /health` | verificação de vida |
| `POST /telemetry` | ingestão em lote de até 5.000 leituras; registra aparelho desconhecido e ignora leitura repetida |
| `GET /devices` | lista de aparelhos |
| `GET /devices/overview` | aparelhos com a última leitura e a última predição, em uma chamada só |
| `GET /devices/{code}` | aparelho com a predição mais recente |
| `GET /devices/{code}/telemetry?since=&limit=` | histórico do mais recente ao mais antigo |
| `POST /models` e `GET /models` | registro e lista de modelos treinados |
| `POST /predictions` | grava uma predição e calcula a faixa de risco pela política ativa |
| `POST /devices/{code}/predictions/run?as_of=` | executa o modelo sobre o histórico do aparelho e grava a predição |
| `GET /devices/{code}/predictions` | histórico de predições do aparelho |
| `GET /predictions/summary` | contagem por faixa considerando a última predição de cada aparelho |
| `GET /alerts` | aparelhos em `high` ou `medium` na última predição, do menor RUL ao maior, com a origem da política |
| `GET /fleet/trend?days=` | média diária de capacidade da frota, sem os dias em que menos da metade dos aparelhos reportou |

Exemplo de lote de telemetria:

```json
{
  "readings": [
    {
      "device_code": "DEVICE-0001",
      "recorded_at": "2026-09-20T10:00:00Z",
      "battery_level_pct": 78,
      "battery_temp_c": 31.2,
      "voltage_mv": 3900,
      "is_charging": false,
      "cycle_count": 184,
      "deep_discharge_count": 3,
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

Nível 3 em 2026-11-01, Python 3.12: `pytest` com 70 testes passando; `ruff` e `bandit` sem achados;
`scripts/run_demo_pipeline.py` executado do banco vazio até as predições em `postgres:16-alpine`
(PostgreSQL 16.15), com a tela da aplicação lendo os dados da API.


## Contrato com o frontend

Durante o desenvolvimento local, a API aceita por padrão as origens `http://localhost:5173` e
`http://127.0.0.1:5173`. A lista pode ser alterada pela variável `FRONTEND_ORIGINS`.

O código pseudonimizado de dispositivo adotado pelo frontend, backend e pipeline de ML segue o
formato `DEVICE-0001`. As faixas `low`, `medium` e `high` representam nível de risco no
backend; o frontend pode apresentá-las como Saudável, Atenção e Risco sem redefinir os limiares.
