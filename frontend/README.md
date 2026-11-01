# Frontend — Monitoramento Preditivo de Baterias

Aplicação web (React + Vite + TypeScript + Material UI + Zustand) da prova de conceito de monitoramento preditivo da saúde de baterias em dispositivos móveis corporativos, parte do Projeto Integrador IV.

O frontend consome a API FastAPI do backend através da camada de serviço `src/services/api.ts`. O backend é a fonte de verdade da política de risco: as telas só traduzem `low`, `medium` e `high` para Saudável, Atenção e Risco.

## Rodando localmente

Com o backend no ar e populado (veja `backend/README.md`):

```bash
npm install
cp .env.example .env
npm run dev
```

| Variável | Padrão | Uso |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Endereço da API |
| `VITE_USE_MOCKS` | `false` | `true` usa os dados fictícios de `src/mocks`, sem precisar do backend |

Os limiares fixos que existem em `src/mocks` só valem no modo mock e não afetam os dados da API.

Dispositivos com telemetria, mas ainda sem predição, não aparecem nas telas da frota: a classificação depende da predição.

## Estrutura

```
src/
├── components/   # layout, cards, charts e componentes de dispositivos
├── pages/        # telas roteadas (Dashboard, Devices, Predictions, Alerts, ML, About)
├── services/     # camada de acesso a dados (API real e modo mock)
├── stores/       # estado global (Zustand)
├── mocks/        # dados sintéticos de demonstração
├── types/        # tipos TypeScript compartilhados
├── theme/        # tema Material UI
└── router/       # definição das rotas
```

> Dados e métricas exibidos são sintéticos e servem apenas para validar o pipeline técnico desta PoC.
