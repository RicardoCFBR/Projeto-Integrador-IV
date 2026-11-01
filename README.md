# Projeto Integrador IV — Plataforma de Monitoramento Preditivo de Dispositivos Android

Projeto acadêmico desenvolvido para a disciplina **Projeto Integrador em Computação IV — UNIVESP**.

## Visão geral

A proposta atual investiga o uso de **telemetria de dispositivos Android**, **processamento de dados em escala**, **aprendizado de máquina** e **visualização web** para apoiar a identificação preventiva de problemas em frotas de smartphones corporativos.

O primeiro caso de uso priorizado é a **saúde da bateria**, com uma prova de conceito voltada à estimativa de degradação e vida útil restante (RUL — Remaining Useful Life).

> **Status atual:** fluxo ponta a ponta funcionando com dados sintéticos: telemetria, API, banco, modelo, alertas e dashboard. Os resultados validam o pipeline técnico e não foram validados com dados reais. Veja [validação e limitações](docs/relatorios/validacao-e-limitacoes.md).

## Objetivo da PoC

```text
Telemetria simulada
      ↓
Processamento em Python
      ↓
Modelo de Machine Learning
      ↓
Estimativa de RUL / risco
      ↓
API / persistência
      ↓
Dashboard web
```

## Como rodar a demonstração

Em poucos passos, sem repetir o treinamento: o modelo final está versionado em `ml/artifacts/v2_2_tuned/`.

```bash
# Terminal 1
cd backend
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
docker compose up -d
uvicorn app.main:app

# Terminal 2, depois de o banco e a API subirem
cd backend && source .venv/bin/activate
python scripts/run_demo_pipeline.py

# Terminal 3
cd frontend
npm install
cp .env.example .env
npm run dev
```

O roteiro completo, com o passo a passo do vídeo, está em [demonstração](docs/relatorios/demonstracao.md).

## Roadmap posterior

- detecção de anomalias de rede;
- análise de travamentos/memória;
- previsão de consumo de dados;
- integração mais completa com telemetria real;
- melhorias de deploy, autenticação e observabilidade.

## Arquitetura prevista

- **Dados e ML:** Python, pandas, scikit-learn;
- **Backend:** FastAPI (API REST em Python), SQLAlchemy e Pydantic;
- **Banco de dados:** PostgreSQL;
- **Frontend:** React + Vite + Material UI + Zustand;
- **Dados de entrada:** inicialmente sintéticos, com possibilidade de evolução para dados anonimizados ou padrões reais de operação.

## Estrutura do repositório

```text
.
├── backend/
├── frontend/
├── ml/
├── data/
│   ├── synthetic/
│   └── README.md
├── docs/
│   ├── arquitetura/
│   ├── comunidade-externa/
│   ├── relatorios/
│   └── referencias/
├── .github/
│   └── ISSUE_TEMPLATE/
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Equipe

| Squad | Integrantes | Responsabilidade principal |
|---|---|---|
| Dados e IA | Ricardo, Rafael | geração de dados, experimentos e modelos |
| Backend e Banco | Iuri, Sérgio | API, modelagem e persistência |
| Frontend | Robson, David | dashboard e componentes visuais |
| Documentação e Qualidade | Fábio, Janis | relatório, referências, revisão e audiovisual |

## Convenções

- branch principal: `main`;
- branches de tarefa: `feat/...`, `fix/...`, `docs/...`, `chore/...`;
- não versionar credenciais nem dados sensíveis;
- diferenciar claramente dados reais, parâmetros reais e dados sintéticos;
- não apresentar funcionalidade planejada como implementada.

## Estado de implementação

| Área | Estado |
|---|---|
| Organização do repositório | Estruturada |
| Dados sintéticos | Implementados e validados para a PoC |
| Engenharia de atributos | Implementada |
| Modelo de bateria | Random Forest V2.2 ajustado, treinado, avaliado e versionado |
| Backend | API FastAPI com ingestão, consulta, inferência sob demanda e alertas; 70 testes automatizados |
| Banco | PostgreSQL com dispositivos, histórico de telemetria, versões de modelos, políticas de risco e predições, com distinção entre dados sintéticos e reais |
| Inferência | Sob demanda: `POST /devices/{code}/predictions/run` calcula as 17 features do histórico gravado, executa o modelo e grava a predição. Não é processamento contínuo |
| Frontend | Telas conectadas à API; modo de demonstração com mocks por `VITE_USE_MOCKS=true` |
| Alertas preventivos | Implementados com limiares experimentais, relativos à frota sintética |
| Integração com telemetria real | Não realizada, dependente da disponibilização dos dados da organização parceira |
| Validação com dados reais | Não realizada |

## Critério de sucesso da solução inicial

A solução inicial deverá demonstrar, de ponta a ponta, ao menos:

1. geração ou ingestão de telemetria;
2. processamento dos dados;
3. execução de um modelo de ML;
4. saída interpretável para um dispositivo;
5. visualização do resultado;
6. vínculo documentado com o problema levantado junto à comunidade externa.

## Observação metodológica

Resultados obtidos com dados sintéticos servem, nesta fase, para validar o **pipeline técnico** e a integração dos componentes. Eles não devem ser apresentados como validação de desempenho em ambiente real sem dados reais e validação externa adequada.
