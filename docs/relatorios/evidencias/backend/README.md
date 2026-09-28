# Evidências do backend

Capturas feitas em 2026-09-28 na máquina de desenvolvimento, com o código do pull request 1.
Barras de título e de favoritos foram recortadas. Todos os dados exibidos são sintéticos.

| Arquivo | O que mostra | Legenda sugerida |
|---|---|---|
| `01-pytest-35-testes.png` | `pytest` com 35 testes passando em 0,57 s, sem banco de dados | Execução da suíte de testes automatizados do backend |
| `02-psql-tabelas-e-politica-de-risco.png` | `\dt` com as cinco tabelas criadas pela DDL e a política de risco `experimental-v1` semeada; abaixo, o servidor da API iniciando | Tabelas do banco PostgreSQL e política de risco provisória |
| `03-fastapi-docs-rotas.png` | documentação interativa gerada pela API (OpenAPI) com as dez rotas | Rotas da API e documentação gerada automaticamente |
| `04-post-telemetry-e-get-historico.png` | ingestão de três leituras sintéticas e consulta do histórico do dispositivo DEV-0001, com a coluna `source` igual a `synthetic` | Ingestão de telemetria em lote e consulta de histórico |
| `05-modelo-predicoes-e-resumo-por-risco.png` | registro de um modelo sem métricas, três predições e o resumo por faixa de risco | Registro de predições e resumo por faixa de risco |
| `06-detalhe-dispositivo-risco-alto.png` | detalhe do dispositivo DEV-0003 com a última predição em risco alto | Consulta de um dispositivo com a última predição |

Sobre as figuras 05 e 06: o modelo de aprendizado de máquina ainda não foi treinado. Os valores de
vida útil restante (284, 103 e 24 ciclos) foram enviados manualmente para demonstrar o fluxo de
registro e classificação, e a faixa de risco vem da política provisória com limiares de 50 e 150
ciclos. Não são saídas de modelo e não devem ser apresentados como resultado.
