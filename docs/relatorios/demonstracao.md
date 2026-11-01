# Demonstração ponta a ponta

Roteiro para reproduzir a solução e gravar o vídeo. Pré-requisitos: Python 3.12, `uv`, Docker e Node.js.

## 1. Subir o banco e a API

```bash
cd backend
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
docker compose down -v
docker compose up -d
uvicorn app.main:app
```

O `docker compose down -v` apaga o banco local, para a demonstração começar vazia. Se a porta 5432 estiver ocupada, ajuste `DB_PORT` e `DATABASE_URL` no `.env`. Espere o banco terminar de iniciar antes de subir a API.

## 2. Popular o sistema

Em outro terminal, com o mesmo ambiente ativo:

```bash
cd backend
python scripts/run_demo_pipeline.py
```

O comando leva cerca de 1 minuto e termina com `{'low': 59, 'medium': 17, 'high': 4}`.

## 3. Abrir o frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

A aplicação fica em `http://localhost:5173`.

## 4. Roteiro do vídeo

1. **Dashboard:** 80 aparelhos, com 59 saudáveis, 17 em atenção e 4 em risco, vindos da API. Destacar o gráfico Temperatura × RUL.
2. **Dispositivos:** filtrar por Risco e abrir o `DEVICE-0070`.
3. **Inserir uma leitura:** em `http://localhost:8000/docs`, executar `POST /telemetry` com o corpo abaixo.
4. **Rodar predição:** voltar à tela do `DEVICE-0070` e clicar em **Rodar predição**. O RUL cai de 658 para 643 ciclos, e o histórico ganha um ponto.
5. **Alertas:** mostrar a recomendação de inspeção, a data da predição e o aviso de limiar experimental.
6. **Machine Learning:** métricas, hiperparâmetros e importância das características.
7. **Encerrar com as limitações:** dados sintéticos, sem validação real e RUL em ciclos, conforme `validacao-e-limitacoes.md`.

```json
{
  "readings": [
    {
      "device_code": "DEVICE-0070",
      "recorded_at": "2026-06-30T00:00:00Z",
      "battery_level_pct": 58,
      "battery_temp_c": 37.1,
      "voltage_mv": 3910,
      "is_charging": false,
      "cycle_count": 75.62,
      "deep_discharge_count": 13,
      "estimated_capacity_pct": 96.12,
      "source": "synthetic"
    }
  ]
}
```

## Perguntas prováveis

| Pergunta | Resposta |
|---|---|
| Esse R² vale para dados reais? | Não se sabe. Só há validação com dados sintéticos. |
| É predição em tempo real? | Não. É sob demanda, sobre o histórico gravado no banco. |
| Por que uma leitura não basta? | As features usam janelas de 7 e 30 dias, e são necessários 31 dias consecutivos. |
| Houve vazamento de dados? | As colunas `sim_*` e o SoH ficam fora das features, e treino e teste são separados por aparelho. |
| Os aparelhos da demonstração foram usados no treino? | Não. A demonstração usa só os 80 aparelhos do conjunto de teste. |
| "Risco" quer dizer que a bateria está acabando? | Não. A faixa é relativa à frota e o RUL é em ciclos, então pesa o calor e o baixo uso. |
