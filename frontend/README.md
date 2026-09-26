# Frontend — Monitoramento Preditivo de Baterias

Aplicação web (React + Vite + TypeScript + Material UI + Zustand) da prova de conceito de monitoramento preditivo da saúde de baterias em dispositivos móveis corporativos, parte do Projeto Integrador IV.

Nesta etapa o frontend consome dados **mockados** através de uma camada de serviço (`src/services/api.ts`) que já espelha o formato esperado da futura API, para que a troca de mock por integração real não exija reescrever as telas.

## Rodando localmente

```bash
npm install
npm run dev
```

## Estrutura

```
src/
├── components/   # layout, cards, charts e componentes de dispositivos
├── pages/        # telas roteadas (Dashboard, Devices, Predictions, Alerts, ML, About)
├── services/     # camada de acesso a dados (hoje: mocks; futuro: API real)
├── stores/       # estado global (Zustand)
├── mocks/        # dados sintéticos de demonstração
├── types/        # tipos TypeScript compartilhados
├── theme/        # tema Material UI
└── router/       # definição das rotas
```

> Dados e métricas exibidos são sintéticos e servem apenas para validar o pipeline técnico desta PoC.
