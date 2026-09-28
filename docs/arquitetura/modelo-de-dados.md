# Modelo de dados da PoC de bateria

Este documento descreve as tabelas do banco PostgreSQL usadas pela API do backend. A DDL de
referência está em `backend/db/schema.sql` e os modelos ORM equivalentes em `backend/app/models.py`.
Nomes de tabela e coluna ficam em inglês; os rótulos em português são usados no dashboard e no
relatório.

## Visão geral

```text
device 1 --- N battery_telemetry
device 1 --- N battery_prediction N --- 1 ml_model
                                 N --- 1 risk_policy
```

| Tabela | O que guarda |
|---|---|
| `device` | aparelho identificado só por um código pseudonimizado no formato `DEV-0001` |
| `battery_telemetry` | uma leitura de bateria por aparelho e instante, única em `(device_id, recorded_at)` |
| `ml_model` | versão do modelo treinado, algoritmo, métricas, hiperparâmetros e features |
| `risk_policy` | limiares em ciclos que convertem o RUL em faixa de risco; só uma política ativa |
| `battery_prediction` | RUL estimado, faixa de risco, modelo usado e snapshot das features |

## Três conceitos que não se misturam

| Conceito | Coluna | Significado |
|---|---|---|
| Nível de bateria | `battery_telemetry.battery_level_pct` | quanta carga há no instante da leitura |
| Estado de saúde (SOH) | `battery_telemetry.estimated_capacity_pct` | capacidade atual em relação à nominal |
| Vida útil restante (RUL) | `battery_prediction.rul_cycles` | ciclos estimados até o critério de fim de vida |

## device

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| id | BIGSERIAL | sim | chave técnica |
| code | VARCHAR(20) | sim, único | código pseudonimizado gerado pelo simulador |
| model | VARCHAR(80) | não | modelo do aparelho, se conhecido |
| os_version | VARCHAR(40) | não | versão do Android |
| battery_design_capacity_mah | INTEGER | não | capacidade nominal, referência para o SOH |
| is_active | BOOLEAN | sim | aparelho ainda monitorado |
| enrolled_at | TIMESTAMPTZ | sim | entrada na frota monitorada |
| created_at, updated_at | TIMESTAMPTZ | sim | auditoria |

Não há coluna de identificação pessoal. Em um cenário com dados reais, o mapeamento entre o
código e o aparelho físico fica fora deste banco.

## battery_telemetry

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| id | BIGSERIAL | sim | chave técnica |
| device_id | BIGINT | sim | referência a `device`, apaga em cascata |
| recorded_at | TIMESTAMPTZ | sim | instante da leitura; único junto com `device_id` |
| battery_level_pct | SMALLINT | sim | 0 a 100 |
| battery_temp_c | NUMERIC(5,2) | sim | graus Celsius |
| voltage_mv | INTEGER | sim | maior que zero |
| is_charging | BOOLEAN | sim | |
| cycle_count | INTEGER | sim | maior ou igual a zero |
| estimated_capacity_pct | NUMERIC(5,2) | não | 0 a 100 |
| ram_available_mb | INTEGER | não | maior ou igual a zero |
| network_rx_mb, network_tx_mb | NUMERIC(12,3) | não | maior ou igual a zero |
| source | VARCHAR(10) | sim | `synthetic` (padrão) ou `real` |
| ingested_at | TIMESTAMPTZ | sim | chegada na API |

Índice `(device_id, recorded_at DESC)` para o histórico por aparelho. A coluna `source` existe
para que dado sintético nunca seja confundido com dado real.

## ml_model

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| id | SERIAL | sim | |
| name, version | VARCHAR | sim, únicos em par | ex.: `battery-rul`, `0.1.0` |
| algorithm | VARCHAR(80) | sim | ex.: `RandomForestRegressor` |
| target | VARCHAR(40) | sim | padrão `rul_cycles` |
| trained_at | TIMESTAMPTZ | sim | |
| training_rows | INTEGER | não | linhas usadas no treino |
| metrics | JSONB | não | ex.: `mae`, `rmse`, `r2`; só valores realmente obtidos |
| hyperparameters | JSONB | não | |
| features | JSONB | não | lista de nomes de features |
| artifact_path | VARCHAR(255) | não | onde o arquivo do modelo está |
| notes | TEXT | não | |

## risk_policy

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| id | SERIAL | sim | |
| name | VARCHAR(80) | sim, único | ex.: `experimental-v1` |
| high_below_cycles | NUMERIC(8,2) | sim | RUL abaixo disso é `high` |
| medium_below_cycles | NUMERIC(8,2) | sim | maior que o anterior; RUL abaixo disso é `medium` |
| source | VARCHAR(20) | sim | `experimental`, `community` ou `literature` |
| is_active | BOOLEAN | sim | no máximo uma linha ativa |
| notes | TEXT | não | |

A DDL semeia a política `experimental-v1` com 50 e 150 ciclos. São valores provisórios para a
prova de conceito, não validados com a operação. Devem ser substituídos pelos limiares
levantados com a comunidade externa, gravando a nova política com `source = 'community'`.

## battery_prediction

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| id | BIGSERIAL | sim | |
| device_id | BIGINT | sim | referência a `device` |
| model_id | INTEGER | sim | referência a `ml_model` |
| risk_policy_id | INTEGER | não | política usada na classificação |
| predicted_at | TIMESTAMPTZ | sim | quando a inferência rodou |
| telemetry_until | TIMESTAMPTZ | não | última leitura considerada |
| rul_cycles | NUMERIC(8,2) | sim | saída do modelo |
| risk_level | VARCHAR(10) | sim | `low`, `medium` ou `high` |
| features | JSONB | não | valores das features usados, para o detalhe no dashboard |

Índice `(device_id, predicted_at DESC)`.

## Correspondência com o dataset previsto em `data/README.md`

| Nome no dataset | Coluna no banco | Observação |
|---|---|---|
| device_id | `device.code` | o `id` numérico de `device` é interno |
| timestamp | `battery_telemetry.recorded_at` | em UTC |
| charging | `battery_telemetry.is_charging` | |
| battery_level_pct, battery_temp_c, voltage_mv, cycle_count, estimated_capacity_pct, ram_available_mb, network_rx_mb, network_tx_mb | mesmo nome em `battery_telemetry` | |
| rul_cycles | `battery_prediction.rul_cycles` | alvo do modelo; no dataset de treino fica no CSV, não em `battery_telemetry` |

## Volume esperado na PoC

| Cenário de simulação | Leituras em `battery_telemetry` |
|---|---|
| 400 aparelhos, uma leitura por dia, 90 dias | 36.000 |
| 400 aparelhos, uma leitura a cada 15 minutos, 7 dias | 268.800 |

Os dois cenários cabem no índice composto sem particionamento. Os números descrevem carga de
teste da prova de conceito, não um benchmark de produção.

## Decisões em aberto

- Alinhar nomes, unidades e campos com o modelo de telemetria da empresa parceira assim que a
  documentação técnica dela estiver disponível.
- Decidir a granularidade da simulação. O schema aceita as duas.
- Features derivadas (média de temperatura, taxa de descarga, tendência de 7 e 30 dias) ficam em
  pandas nesta fase. Se precisarem ser persistidas, entra uma tabela própria.
