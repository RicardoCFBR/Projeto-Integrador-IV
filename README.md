# Projeto Integrador IV — Plataforma de Monitoramento Preditivo de Dispositivos Android

Projeto acadêmico desenvolvido para a disciplina **Projeto Integrador em Computação IV — UNIVESP**.

## Visão geral

A proposta atual investiga o uso de **telemetria de dispositivos Android**, **processamento de dados em escala**, **aprendizado de máquina** e **visualização web** para apoiar a identificação preventiva de problemas em frotas de smartphones corporativos.

O primeiro caso de uso priorizado é a **saúde da bateria**, com uma prova de conceito voltada à estimativa de degradação e vida útil restante (RUL — Remaining Useful Life).

> **Status atual:** estrutura inicial do projeto em construção. Nesta etapa, o foco é validar o pipeline técnico e acadêmico com dados sintéticos parametrizados por referências técnicas e, quando possível, por padrões reais levantados com a comunidade externa.

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

## Prioridade atual

- geração de dados sintéticos de telemetria;
- primeiro modelo de bateria;
- estrutura inicial de backend e banco;
- estrutura inicial de frontend;
- documentação da comunidade externa;
- evidências para o Relatório Parcial.

## Roadmap posterior

- detecção de anomalias de rede;
- análise de travamentos/memória;
- previsão de consumo de dados;
- integração mais completa com telemetria real;
- melhorias de deploy, autenticação e observabilidade.

## Arquitetura prevista

- **Dados e ML:** Python, pandas, scikit-learn;
- **Backend:** Django / API REST;
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
| Organização do repositório | Em andamento |
| Dados sintéticos | Pendente |
| Modelo inicial de bateria | Pendente |
| Backend | Pendente |
| Banco | Pendente |
| Frontend | Pendente |
| Validação com comunidade externa | Pendente |
| Relatório Parcial | Em andamento |

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
