# Evidências da integração

Capturas feitas em 2026-11-01 com a aplicação rodando em ambiente local: frontend em modo API, backend em Python 3.12 e PostgreSQL 16.15 descartável. Todos os dados exibidos são sintéticos. O passo a passo para reproduzir está em `../../demonstracao.md`.

| Arquivo | O que mostra | Legenda sugerida |
|---|---|---|
| `01-dashboard-dados-da-api.png` | 80 aparelhos, 59 saudáveis, 17 em atenção e 4 em risco, vindos de `GET /devices/overview` e `GET /fleet/trend` | Dashboard do gestor com dados da API |
| `02-dispositivos-da-api.png` | Lista de aparelhos com SoH, RUL previsto e faixa de risco | Frota monitorada |
| `03-alertas-preventivos.png` | Aparelhos em risco e atenção, com recomendação, data da predição e aviso de limiar experimental | Alertas preventivos gerados pelas predições |
| `04-dispositivo-predicao-sob-demanda.png` | Clique em Rodar predição depois de nova leitura: RUL de 658 para 643 ciclos | Predição sob demanda a partir do histórico persistido |
| `05-predicoes-filtradas-por-risco.png` | Predições filtradas pela faixa que veio do backend | Predições por faixa de risco |
| `06-modelo-registrado.png` | Modelo RF-V2.2-TUNED registrado, com métricas, hiperparâmetros e importância das características | Modelo em uso e suas métricas no conjunto sintético |
| `07-swagger-rotas.png` | Documentação interativa com as rotas, incluindo a de inferência | Rotas da API |
