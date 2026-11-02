# Hospedagem de demonstração BatteryCare no Render

Este deploy é uma **PoC acadêmica** com dados **somente sintéticos**, não adequada
a uso operacional. O objetivo é permitir que o professor acesse o site e teste
a inferência do Random Forest. Nenhuma credencial deve ser enviada ao Git.

## 1. Criar os três serviços gratuitos

1. No Render, conectar o GitHub `RicardoCFBR/Projeto-Integrador-IV`.
2. Abrir **New > Blueprint** e selecionar a branch `main`.
3. Aplicar `render.yaml`. Conferir que todos os planos são **Free** antes
   de confirmar; não selecionar planos pagos.
4. O Blueprint cria o site estático `batterycare-web-pi4`, a API
   `batterycare-api-pi4` e o PostgreSQL `batterycare-postgres-pi4`.
5. O backend usa a raiz do monorepo para que o artefato
   `ml/artifacts/v2_2_tuned/*.joblib` fique acessível.
6. O backend cria tabelas e ativa a política experimental v2 na primeira
   inicialização, sem apagar conteúdo existente.

O hostname da API é injetado no build do frontend, e o hostname do frontend
é adicionado às origens de CORS do backend. Após a primeira publicação, confira
os valores reais de `VITE_API_URL` e `FRONTEND_ORIGINS` nos serviços.
Caso tenha ocorrido um build antes da resolução das variáveis de serviço,
refaça o deploy do frontend.

## 2. Popular o banco hospedado

Inicialize somente depois que `https://<API>/health` responder
`{"status":"ok"}`. No Windows PowerShell, com Python 3.12 instalado:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts\run_demo_pipeline.py --api-url https://<API>.onrender.com
```

Troque `<API>` pelo subdomínio fornecido pelo Render. O script lê ou gera
os dados sintéticos e envia os 80 dispositivos fora do treinamento. Na primeira
execução espera-se **80 dispositivos**, **14.400 leituras** e **480 predições
históricas**. O resumo esperado é 59 saudáveis, 17 em atenção e 4 em risco.
A carga inicial é feita uma única vez; repetir o script não substitui dados.

## 3. Verificações

- Abrir o URL público do frontend. O dashboard não deve apresentar erro de CORS.
- Conferir a rota `https://<API>.onrender.com/health`.
- Abrir `/devices/DEVICE-0070` no frontend.
- Executar **Rodar predição** e verificar se o resultado foi gravado.
- Validar `/alerts`, `/predictions/summary` e `/models` pela API.
- Confirmar no Render os logs de inicialização e memória da instância.

## 4. Limitações e segurança

- **Não há autenticação na API**: visitantes podem enviar telemetria e executar
  predições. O banco deve conter apenas dados sintéticos. Para publicação
  prolongada, implementar controle de acesso ou restringir rotas mutáveis.
- O serviço web gratuito entra em repouso e a primeira visita pode demorar.
- O PostgreSQL gratuito do Render expira em **30 dias** e não é apropriado
  para dados persistentes de produção. Conferir a data de expiração no painel.
- O modelo e as dependências de ML precisam caber na memória do plano gratuito.
  Não há garantia antes de uma execução real em nuvem.
- Como o frontend incorpora `VITE_API_URL` no momento do build, qualquer
  mudança de endereço da API requer novo build do site estático.
- Nunca executar `docker compose down -v` em banco com dados a preservar.
