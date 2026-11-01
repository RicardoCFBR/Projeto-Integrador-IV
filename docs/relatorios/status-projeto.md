# Status do Projeto Integrador IV

Atualizado em 2026-11-01.

## Marco atual

**Entrega final: Relatório Final e vídeo da solução**

## Estado por componente

| Componente | Estado | Evidência |
|---|---|---|
| Gerador de telemetria sintética | Implementado | `ml/data_generator/generate_battery_data_v2.py` |
| Engenharia de atributos | Implementada | `ml/feature_engineering/build_battery_features_v2_1.py` |
| Modelo Random Forest V2.2 ajustado | Treinado, avaliado e versionado | `ml/artifacts/v2_2_tuned/` |
| API e banco de dados | Implementados | `backend/`, 70 testes automatizados |
| Inferência sob demanda pela API | Implementada | `POST /devices/{code}/predictions/run` |
| Frontend conectado à API | Implementado | `frontend/`, capturas em `evidencias/integracao/` |
| Alertas preventivos | Implementados, com limiares experimentais | `GET /alerts` e tela de Alertas |
| Demonstração em um comando | Implementada | `backend/scripts/run_demo_pipeline.py` |
| Validação com dados reais | Não realizada | Ver `validacao-e-limitacoes.md` |

## Pendências da entrega

- [ ] gravar o vídeo seguindo `demonstracao.md`;
- [ ] consolidar o Relatório Final com as evidências e as limitações declaradas;
- [ ] confirmar com o grupo o estado do contato com a comunidade externa, que este repositório não registra.

## Fora do escopo desta entrega

Novo treinamento com dados reais, processamento contínuo de telemetria, autenticação, observabilidade e implantação em nuvem.
