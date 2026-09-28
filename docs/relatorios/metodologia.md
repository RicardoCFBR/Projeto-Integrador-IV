# Metodologia de desenvolvimento do backend

Método aplicado para criar e publicar o backend e o modelo de dados da prova de conceito de saúde
de bateria (pull request 1). Cada etapa aponta a evidência que a sustenta. Só é descrito aqui o que
foi de fato executado.

## Fluxo

```text
Fontes do grupo e do orientador
            ↓
Requisitos testáveis e escopo delimitado
            ↓
Modelagem de dados (conceitual, lógica, física)
            ↓
Testes escritos antes do código
            ↓
Implementação em camadas
            ↓
Verificação em ambiente descartável, com saída capturada
            ↓
Rastreabilidade requisito, artefato, evidência
            ↓
Commits atômicos e pull request com evidências
```

A abordagem é incremental: uma fatia vertical executável por vez. A primeira fatia foi a
persistência e a API da telemetria de bateria.

## Etapas

### 1. Levantamento de requisitos a partir das fontes do grupo

Os documentos existentes (plano de ação, reestruturação do projeto, roteiro do relatório e
diretrizes do orientador) foram lidos antes de qualquer código. Os campos previstos em
`data/README.md`, a arquitetura em camadas de `docs/arquitetura/README.md` e as exigências de
evidência do Relatório Parcial viraram dez requisitos funcionais e cinco não funcionais, cada um
com critério de aceite.

Evidência: contratos da API em `backend/app/schemas.py` e testes em `backend/tests/`.

### 2. Delimitação de escopo

Entrou só a saúde de bateria: leitura de telemetria, registro do modelo, predição de vida útil
restante e faixa de risco. Ficaram de fora, declarados como roadmap: autenticação, migrações de
banco, inferência dentro da API, persistência de features derivadas e os demais sinais (memória,
CPU, rede, localização).

Evidência: seção "Limitações conhecidas" do pull request 1 e `docs/arquitetura/modelo-de-dados.md`.

### 3. Especificação antes do código

Antes de implementar, foi escrito um documento curto com problema, objetivo, requisitos, cenários
no formato "dado, quando, então", riscos e decisões técnicas com alternativas e justificativa.
Oito cenários foram escritos e depois viraram testes automatizados um a um. Exemplo: "dado um
banco sem dispositivos, quando chega uma leitura do código DEV-0001, então o dispositivo é criado
e a leitura persistida".

Evidência: cada cenário corresponde a uma função em `backend/tests/test_api.py` e
`backend/tests/test_models.py`.

### 4. Modelagem de dados em três níveis

| Nível | Resultado |
|---|---|
| Conceitual | dispositivo, leitura de telemetria, modelo treinado, política de risco, predição |
| Lógico | cinco tabelas com chaves estrangeiras, unicidade por dispositivo e instante, restrições de faixa (CHECK) |
| Físico | `backend/db/schema.sql` para PostgreSQL 16, com índices por dispositivo e instante e semente da política de risco |

Princípios adotados:

- conceitos que costumam ser confundidos ficam em colunas distintas: nível de bateria (carga
  agora), estado de saúde (capacidade frente à nominal) e vida útil restante (ciclos até o fim de
  vida);
- pseudonimização: o dispositivo é identificado só por um código como `DEV-0001`, sem IMEI,
  telefone ou nome;
- toda leitura carrega a coluna `source` com valor `synthetic` ou `real`;
- limiares de risco são dados, não código: ficam na tabela `risk_policy`, com origem declarada
  (`experimental`, `community` ou `literature`), para serem trocados após a entrevista com a
  comunidade externa sem alterar o programa.

Evidência: `docs/arquitetura/modelo-de-dados.md`, `backend/db/schema.sql`, `backend/app/models.py`.

### 5. Testes antes do código (TDD)

Os 35 testes foram escritos antes da implementação. A primeira execução falhou por ausência dos
módulos (fase vermelha). A implementação foi escrita até todos passarem (fase verde). Depois o
código foi formatado e verificado por lint sem mudar comportamento. Os testes rodam em SQLite em
memória, para qualquer integrante reproduzir sem instalar banco.

Evidência: saída de `pytest` com 35 testes passando, registrada no pull request 1 e reproduzível
com os comandos da seção "Como reproduzir".

### 6. Implementação em camadas

| Camada | Módulo | Responsabilidade |
|---|---|---|
| Contratos | `backend/app/schemas.py` | validar entrada e formatar saída da API |
| Persistência | `backend/app/models.py`, `backend/app/database.py` | mapear tabelas e abrir sessões |
| Acesso a dados | `backend/app/repositories.py` | consultas e escritas por entidade |
| Regra de negócio | `backend/app/risk.py` | converter vida útil restante em faixa de risco |
| Interface | `backend/app/main.py` | rotas HTTP |

É arquitetura em camadas, não microsserviços: existe um único serviço implantável.

### 7. Verificação em ambiente descartável

Cada afirmação técnica é classificada pelo grau de verificação que a sustenta, sempre com comando,
versão e data.

| Nível | Significado |
|---|---|
| 1 | conferido contra documentação oficial |
| 2 | passa no validador da ferramenta, sem executar |
| 3 | executa em ambiente descartável, com saída capturada |

O backend está no nível 3. A DDL foi aplicada duas vezes em um container `postgres:16-alpine`
(PostgreSQL 16.15) descartável; as colunas do banco criado foram comparadas com as do ORM sem
divergência; quatro restrições (unicidade de leitura, faixa de percentual, valores permitidos de
risco e política única ativa) foram provadas por inserções rejeitadas.

Evidência: seção "Evidências" do pull request 1.

### 8. Qualidade automatizada

`pytest` (testes), `ruff` (lint e formatação) e `bandit` (análise estática de segurança) rodam sem
achados a cada mudança. Configuração em `backend/pyproject.toml`.

### 9. Rastreabilidade

Cada requisito tem pelo menos um teste nomeado que o cobre, e cada evidência aponta o artefato de
origem. A tabela da seção "Evidências e onde estão" é a versão resumida.

### 10. Privacidade

Princípios de finalidade, adequação e necessidade da LGPD aplicados ao desenho do banco: nenhuma
coluna de identificação pessoal, código de dispositivo pseudonimizado, distinção estrutural entre
dado sintético e real, e nenhum arquivo de credencial versionado (`.env` fica fora do repositório,
com `.env.example` como modelo).

### 11. Limitações declaradas

Só é afirmado o que pode ser demonstrado. Os limiares de risco (50 e 150 ciclos) estão gravados
como `experimental` e descritos como provisórios; os dados são sintéticos e a coluna `source` diz
isso em cada linha; a inferência ainda não roda dentro da API. Tudo está escrito no pull request 1
e no README do backend.

### 12. Versionamento e publicação

- Branch por tarefa a partir de `main`, no padrão do `CONTRIBUTING.md` (`feat/backend-data-model`).
- Cópia do código para o repositório conferida por diff e pela suíte de testes rodando a partir da
  cópia, antes de qualquer commit.
- Seis commits atômicos, um por preocupação (configuração, DDL, modelos, API, testes,
  documentação), com mensagem no padrão Conventional Commits (`tipo(escopo): descrição`). Isso
  permite revisar e reverter cada parte isoladamente.
- Verificação de higiene antes do push: nenhum segredo, nenhum dado pessoal, nenhum caminho de
  máquina local, nenhum nome de terceiros.
- Pull request com o template do repositório: o que foi feito, como testar, evidências, limitações
  e checklist. Revisão por outro integrante antes do merge.

Evidência: histórico de commits e descrição do pull request 1.

## Ferramentas e versões

| Ferramenta | Papel | Versão usada |
|---|---|---|
| Python | linguagem do backend e dos testes | 3.11 |
| FastAPI | API REST e documentação interativa (OpenAPI) | 0.141 |
| SQLAlchemy | mapeamento objeto-relacional | 2.1 |
| Pydantic | validação de contratos de entrada e saída | 2.13 |
| PostgreSQL | banco de dados | 16 |
| psycopg | driver de conexão | 3.3 |
| pytest | testes automatizados | 9.1 |
| ruff | lint e formatação | 0.16 |
| bandit | análise estática de segurança | 1.9 |
| Docker Compose | banco local reproduzível | imagem `postgres:16-alpine` |
| Git e GitHub | versionamento, branches, pull requests | |

## Evidências e onde estão

Legendas e ressalvas de cada captura em `evidencias/backend/README.md`.

| Evidência | Onde está | Formato |
|---|---|---|
| Diagrama do modelo de dados e dicionário por tabela | `docs/arquitetura/modelo-de-dados.md` | figura e tabela |
| DDL PostgreSQL | `backend/db/schema.sql` | trecho de código ou anexo |
| Saída de `pytest` com 35 testes | `evidencias/backend/01-pytest-35-testes.png` | print do terminal |
| Documentação interativa da API | `evidencias/backend/03-fastapi-docs-rotas.png` | print da tela |
| Lista de tabelas no banco (`\dt`) e semente da política | `evidencias/backend/02-psql-tabelas-e-politica-de-risco.png` | print do terminal |
| Resposta JSON de ingestão, resumo por risco e detalhe de dispositivo | `evidencias/backend/04-...png`, `05-...png` e `06-...png` | print do terminal |
| Histórico de commits atômicos | pull request 1 | print |

## Como reproduzir

```bash
git clone git@github.com:RicardoCFBR/Projeto-Integrador-IV.git
cd Projeto-Integrador-IV/backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest                          # 35 testes, sem banco
ruff check . && ruff format --check .
docker compose up -d            # Postgres 16 com o schema aplicado
uvicorn app.main:app --reload   # abrir http://localhost:8000/docs
```

Com o banco de pé, `docker compose exec db psql -U postgres -d fleet_battery -c '\dt'` lista as
cinco tabelas.
