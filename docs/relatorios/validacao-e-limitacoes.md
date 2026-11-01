# Validação e limitações da prova de conceito

Medições feitas em 2026-11-01. Todos os dados são sintéticos.

## Declaração para o relatório

A arquitetura, o pipeline de dados e o modelo foram desenvolvidos e validados tecnicamente com dados sintéticos estruturados. A revalidação com dados reais não foi executada, porque não houve acesso a uma base histórica persistente com volume e continuidade suficientes para novo treinamento e validação.

Os resultados quantitativos são evidência da viabilidade técnica do pipeline. Eles não comprovam o desempenho do modelo em ambiente operacional real.

## O que foi validado

| Item | Como foi verificado | Resultado |
|---|---|---|
| Backend | `pytest`, `ruff` e `bandit`, Python 3.12 | 70 testes passando, sem achados |
| Fluxo completo | `run_demo_pipeline.py` do banco vazio, PostgreSQL 16.15 | 14.400 leituras, predições em 80 aparelhos, 58 s |
| Paridade das features | Comparação com a saída do pipeline de ML em 400 aparelhos | 13 de 17 idênticas; 4 de ciclos diários com desvio máximo de 0,006 |
| Reprodutibilidade do modelo | Pipeline executado a partir do código, semente 42 | MAE 126,84, RMSE 156,45 e R² 0,578, iguais aos registrados |
| Latência | `POST /devices/{code}/predictions/run` | Cerca de 0,1 s por predição |
| Interface | Navegação real nas telas com a API e sem a API | Dados do banco; com a API fora do ar, mensagem de erro |

## Limitações do modelo e dos alertas

### Dados sintéticos

O R² de 0,578 vale para o conjunto sintético. Não se sabe o desempenho com dados reais.

### Faixas de risco relativas à frota

Os limiares de 776 e 983 ciclos são os percentis 10 e 33 do RUL dos 320 aparelhos de desenvolvimento. Eles ordenam os aparelhos dentro da frota simulada e não representam regra de substituição validada com a operação. Nos 80 aparelhos de teste, no último dia:

| Faixa | Previsto | Real |
|---|---|---|
| Risco | 4 | 11 |
| Atenção | 17 | 15 |
| Saudável | 59 | 54 |

O acerto de faixa foi de 82%. Nenhum dos 11 aparelhos em risco real apareceu como saudável, mas só 4 foram marcados como risco, e 6 dos 15 em atenção real apareceram como saudáveis. Os percentis 10 e 33 foram escolhidos depois de comparados com os percentis 20 e 50 (64% de acerto) nos próprios aparelhos de teste. Essa comparação é uma contaminação leve do conjunto de teste e por isso está declarada aqui.

### RUL em ciclos não é tempo restante

O alvo do modelo é o RUL em ciclos, que depende do ritmo de uso: um aparelho pouco usado gasta menos ciclos por dia. Nos 80 aparelhos de teste, a correlação entre o RUL previsto e os anos restantes foi de 0,06. A faixa de risco acompanha principalmente o calor (correlação de -0,82 com os dias quentes) e o baixo uso (0,47 com os ciclos por dia).

| Faixa | Aparelhos | RUL previsto | Ciclos por dia | Dias quentes em 30 | Anos restantes no simulador |
|---|---|---|---|---|---|
| Risco | 4 | 700 | 0,48 | 19,5 | 3,8 |
| Atenção | 17 | 866 | 0,71 | 17,1 | 3,5 |
| Saudável | 59 | 1.198 | 0,80 | 4,0 | 4,5 |

Por isso o alerta recomenda priorizar uma inspeção e não pede a troca imediata. Uma evolução natural é prever o RUL em dias.

### Frota jovem e sem extrapolação

O conjunto cobre 180 dias, e o menor RUL é 497 ciclos. Nenhum aparelho simulado está perto do fim de vida. Como o Random Forest não prevê abaixo do menor valor visto no treino, o modelo não representa aparelhos em fim de vida: a menor predição nas 60.000 linhas foi 574.

### Simplificações da implementação

- A inferência é sob demanda e não contínua, e não deve ser chamada de tempo real.
- São necessários 31 dias consecutivos de telemetria para gerar uma predição.
- O gerador não simula o estado de carga. A demonstração envia `is_charging = false`, e o modelo não usa esse campo.
- O SoH exibido nas telas é sintético e não entra no modelo.
- `cycle_count` é fracionário porque o treino usou esse formato. Um contador real inteiro exigiria revisar as features de ciclos diários.
- Aparelhos com telemetria e sem predição não aparecem nas telas da frota.
- A API não tem autenticação e foi validada apenas em ambiente local.
