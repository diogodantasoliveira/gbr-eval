# CLAUDE.md — gbr-eval

## Identidade do projeto
- **Nome:** gbr-eval
- **Propósito:** Framework de avaliação eval-first para os produtos GarantiaBR
- **Repos alvo:** engine-integracao, garantia_ia, notifier, engine-billing, atom-back-end (5 prioritários)
- **Relação:** Projeto SEPARADO — não vive dentro do monorepo gbr-engines
- **Owner:** Diogo Dantas (CAIO)
- **Jira:** https://garantiabr.atlassian.net/jira/software/c/projects/ADA/boards/266 | Projeto: ADA
- **Confluence:** https://garantiabr.atlassian.net/wiki/spaces/team77124ebccfd54308acd71a43125ef8b5 | Espaço: Produtos Core
- **Stack:** Python 3.12+, uv, pytest, ruff, mypy | Frontend: Next.js 16, pnpm, Drizzle ORM, SQLite

## O que é este projeto

gbr-eval é o framework de avaliação que define e verifica critérios de qualidade para dois tipos de uso de LLM na GarantiaBR:

1. **Camada Engineering:** Claude Code gerando código para a plataforma — segue CLAUDE.md? Filtra por tenant_id? Não hardcoda dados de negócio?
2. **Camada Product:** ai-engine, extractor, parecer, compliance_agent produzindo outputs para clientes — extrai o CPF correto? O scoring bate com o golden set?

### Metodologia: Eval-First

Este projeto existe ANTES dos sistemas que ele avalia. Os produtos legados (plataforma-modular, originacao_imobiliaria) serão descontinuados e reconstruídos. gbr-eval define os critérios de qualidade que as novas construções devem atender desde o dia 1.

### Quatro camadas de qualidade

gbr-eval é o **backbone centralizado de qualidade** da GarantiaBR. Todas as regras vivem aqui, consumidas por cada repo via CI.

| Camada | Nome | O que avalia | Status |
|--------|------|-------------|--------|
| **E** | Engineering Quality | Código segue padrões de engenharia e regras de domínio por repo? | Planejado — regras definidas para 5 repos |
| **P** | Product Quality | Outputs de IA corretos contra golden sets? | Parcial — 34 tasks, 40 golden cases, 12 graders, self-eval operacional |
| **O** | Operational | SLAs, custos, disponibilidade | Futuro |
| **C** | Compliance | LGPD, BACEN, audit trail, ISO 27001 | Futuro |

### 5 repos alvo (Camada E)

| Repo | Domínio | Regras de domínio |
|------|---------|-------------------|
| engine-integracao | Integrações externas | retry/backoff, circuit breaker, timeout por provider, credential vault |
| garantia_ia | IA/prompts | prompt versionado, PII sanitizada, output schema, cost tracking |
| notifier | Notificações | template aprovado, idempotência, LGPD opt-out, rate limiting |
| engine-billing | Billing | Decimal (nunca float), idempotency key, audit trail, reconciliação par |
| atom-back-end | Backoffice | tenant_id em toda query, RBAC, audit log, dados sensíveis filtrados |

## Regra Zero — Nunca Inferir

> **Herdada de gbr-engines. Aplica-se integralmente.**

A LLM NÃO toma decisões sobre:
- Quais critérios de qualidade usar (humano decide)
- O que constitui "correto" em um golden set (CLO valida)
- Limiares de aprovação/reprovação (configuração, não código)
- Se um grader deve ser blocking ou informative (decisão de negócio)
- Quais campos são CRITICAL vs IMPORTANT vs INFORMATIVE (decisão de negócio)

Na dúvida, **perguntar**. Na dúvida sobre a dúvida, **perguntar também**.

A LLM **nunca** deve:
- Adicionar graders extras "já que estamos mexendo aqui"
- Sugerir novos critérios de qualidade que não foram pedidos
- Expandir o escopo de um task YAML além do solicitado
- Criar golden sets sintéticos sem autorização explícita

## Mentalidade Enterprise — NÃO é MVP

Este framework avalia uma **plataforma enterprise em produção** para grandes instituições financeiras (Itaú, Bradesco, Banco Pine). Toda decisão técnica segue essa premissa:

- **Reprodutibilidade** — qualquer engenheiro roda o eval na máquina local com resultado idêntico
- **Rastreabilidade** — cada eval run tem ID, timestamp, versão dos golden sets, versão do código avaliado
- **Compliance** — golden sets contêm dados de documentos financeiros (mesmo anonimizados, são RESTRITO)
- **Auditabilidade** — resultados de eval são evidência para ISO 27001, SOC 2, e BACEN

### Ordem de prioridade
Compliance > Segurança > Correção dos Graders > Features > Polish

## PREMISSA DE CONSTRUÇÃO — `uv sync && uv run pytest` sempre saudável

**Todo engenheiro que clonar o repo deve conseguir rodar o eval framework em uma máquina limpa com 3 comandos.** Essa não é uma aspiração — é um contrato de entrada.

```bash
git clone <repo> && cd gbr-eval
uv sync --all-extras
uv run pytest
```

Corolários obrigatórios em **toda iteração**:
- `uv sync` **nunca** pode falhar após merge. Se um PR adiciona dependência, o `pyproject.toml` já inclui no mesmo PR.
- `uv run pytest` **nunca** pode ter testes falhando em main. Se um teste falha, é bug — não é "teste pendente".
- `uv run ruff check .` retorna zero erros. Sem exceção.
- `uv run mypy src/` retorna zero erros. Sem exceção.
- Se o LLM-judge requer `ANTHROPIC_API_KEY`, os testes que dependem dele têm skip condicional — nunca quebram o CI por falta de env var.
- Golden sets com dados RESTRITO nunca entram no repositório sem anonimização prévia.

Se alguma dessas checagens quebrar, o PR não fecha.

## Development commands

```bash
# Setup (máquina limpa)
uv sync --all-extras

# Quality gates (rodar TODOS antes de qualquer PR)
uv run pytest                                              # testes
uv run pytest --cov=src/gbr_eval --cov-report=term-missing # cobertura (>= 80%)
uv run ruff check .                                        # lint
uv run mypy src/                                           # type check

# Rodar uma suite de eval
uv run python -m gbr_eval.harness.runner run --suite tasks/product/

# Rodar task específica
uv run python -m gbr_eval.harness.runner run --task tasks/product/extraction/matricula_cpf.yaml

# Self-eval (golden sets como output)
uv run python -m gbr_eval.harness.runner run --suite tasks/product/ --golden-dir golden/ --self-eval

# Com model roles (override de modelo para graders)
uv run python -m gbr_eval.harness.runner run --suite tasks/product/ --model-role grader=claude-sonnet-4-6

# Com endpoint HTTP real (dev local — requer --allow-internal)
uv run python -m gbr_eval.harness.runner run --task tasks/product/extraction/matricula_cpf.yaml --endpoint http://localhost:8000 --allow-internal

# Análise de trends
uv run python -m gbr_eval.harness.runner analyze --runs-dir runs/

# Rodar testes específicos
uv run pytest tests/graders/test_deterministic.py          # um arquivo
uv run pytest -k "test_exact_match"                        # por nome

# Frontend admin panel
cd frontend && pnpm install                                   # setup
cd frontend && pnpm dev                                       # dev server (port 3002)
cd frontend && pnpm type-check                                # TypeScript check
cd frontend && pnpm db:push                                   # apply DB schema
```

## Arquitetura

```
gbr-eval/
├── src/gbr_eval/
│   ├── graders/              # 12 graders + dispatcher context-aware
│   │   ├── base.py           # Grader + ContextAwareGrader Protocols, _CONTEXT_AWARE registry, grade() dispatcher
│   │   ├── deterministic.py  # 7 graders puros (exact_match, numeric_range, etc.)
│   │   ├── engineering.py    # 3 graders de engenharia (pattern_required/forbidden, convention_check) + ReDoS guard
│   │   ├── field_f1.py       # F1 por campo com fuzzy matching
│   │   └── model_judge.py    # LLM-as-judge (Claude Sonnet) — NÃO puro, context_aware=True, PII recursivo
│   ├── solvers/              # Solver Protocol (async) + AgentTrace models
│   │   ├── base.py           # Solver Protocol, registry (@register_solver)
│   │   ├── models.py         # ToolCall, Message, AgentTrace (Pydantic)
│   │   └── passthrough.py    # PassthroughSolver (returns trace unchanged)
│   ├── harness/              # Runner de avaliação
│   │   ├── models.py         # Pydantic: Task, TaskResult, GraderResult, EvalRun, GraderContext, ScoreReducer
│   │   ├── runner.py         # load_task, run_task, run_suite, _run_single_epoch, CLI
│   │   ├── async_runner.py   # run_task_with_solver (async, uses _run_single_epoch)
│   │   ├── task_helpers.py   # task_with() — copia tasks com overrides validados
│   │   ├── client.py         # EvalClient (HTTP + SSRF protection), OutputRecorder
│   │   ├── code_loader.py    # Code Loader: carrega arquivos de repos alvo para eval de engenharia
│   │   ├── reporter.py       # Console, JSON, JUnit XML, CI summary
│   │   ├── regression.py     # RegressionDelta, classify_gate
│   │   ├── trends.py         # TrendAlert, detect_trends
│   │   └── analyzer.py       # Utilitários de análise
│   ├── contracts/            # Schema snapshots dos repos alvo
│   │   └── validator.py      # JSON Schema validation (standalone, sem deps externas)
│   └── calibration/          # Concordância inter-anotador
│       └── iaa.py            # Cohen's kappa, concordance tracking
├── tasks/                    # 48 task YAMLs
│   ├── product/              # classification(10), extraction(7), citation(6), cost(1), latency(1), decision(1)
│   └── engineering/          # atom-back-end(5), engine-billing(4), engine-integracao(5), garantia-ia(4), notifier(4)
├── golden/                   # Golden sets — ground truth anotado por humano (40 cases)
│   ├── matricula/            # 8 cases (5 standard + 2 edge + 1 confuser)
│   ├── contrato_social/      # 8 cases (5 standard + 2 edge + 1 confuser)
│   ├── cnd/                  # 8 cases (5 standard + 2 edge + 1 confuser)
│   ├── procuracao/           # 8 cases (5 standard + 2 edge + 1 confuser)
│   ├── certidao_trabalhista/ # 8 cases (5 standard + 2 edge + 1 confuser)
│   ├── balanco/              # 0 cases (blocked — 0 docs disponíveis)
│   └── red_team/             # 0 cases (blocked — authenticity_flag pendente)
├── frontend/                 # Admin panel — Next.js 16 + SQLite (40 páginas, 57 API routes)
│   ├── src/app/              # Pages e API routes
│   ├── src/db/               # Drizzle ORM, 23 tabelas
│   ├── src/lib/              # PII redaction, validations, scoring
│   └── src/components/       # UI components (shadcn/ui)
├── tools/                    # Scripts auxiliares
│   ├── generate_synthetic.py # Gerador de golden sets sintéticos (4 categorias, Claude em contexto separado)
│   ├── generate_all_synthetic.py # Batch generation com env allowlist
│   ├── compute_hashes.py     # SHA-256 dos PDFs originais
│   └── sync_frontend.py      # Sincronização frontend com auth token
├── tests/                    # ~496 testes do framework (pytest)
│   ├── graders/              # test_deterministic, test_field_f1, test_engineering, test_model_judge
│   ├── harness/              # test_runner, test_epochs, test_model_roles, test_grader_context, test_async_runner, test_task_helpers, test_client, test_reporter, test_regression, test_trends, test_cli, test_resolve_output, test_analyzer, test_code_loader, test_eval_first_validation, test_golden_set_tags, test_postmortem
│   ├── solvers/              # test_models, test_base
│   ├── contracts/            # Testes de contract testing
│   ├── integration/          # test_golden_set_smoke
│   └── test_calibration.py   # Testes de IAA (root level)
├── docs/                     # Documentação (19 documentos)
└── runs/                     # Resultados de eval runs (JSON)
```

### Runners e Solvers

| Runner | O que faz | Quando roda |
|--------|-----------|-------------|
| **pytest** | Testa o framework (graders, models, runner, calibration) | CI do gbr-eval (`uv run pytest`) |
| **CLI (runner.py)** | Executa suites de eval contra outputs reais ou gravados | CI dos repos alvo + avaliações manuais |
| **async_runner.py** | Executa tasks via Solver Protocol (async, captura AgentTrace) | Eval de trajetória de agentes |

pytest testa SE os graders funcionam. O CLI testa O QUE os graders avaliam. O async_runner testa COMO o agente chegou no resultado.

Ambos os runners (sync e async) delegam grading para `_run_single_epoch()` — função compartilhada que garante lógica idêntica. Suportam multi-epoch com short-circuit para graders determinísticos e score reducers (MEAN, MEDIAN, AT_LEAST_ONE, ALL_PASS, MAJORITY).

## Invariantes — NUNCA violar

### 1. Graders são funções puras
```python
class Grader(Protocol):
    def grade(self, output: dict, expected: dict, spec: GraderSpec) -> GraderResult: ...

class ContextAwareGrader(Protocol):
    def grade(self, output: dict, expected: dict, spec: GraderSpec, *, context: GraderContext | None = None) -> GraderResult: ...
```
Mesma assinatura para CI, sampling em produção, e triggers de ação.
**Exceção documentada:** LLM-judge não é puro (chama API externa, não-determinístico). Registrado com `context_aware=True` — recebe resultados de graders anteriores via `GraderContext`. Runtime dispatch via `_CONTEXT_AWARE` set (não `@runtime_checkable` isinstance).

### 2. Zero tautologia
O golden set NUNCA é gerado automaticamente a partir do expected do task. Cada golden set é:
- Anotado por humano (Diogo como CLO)
- Validado por segundo revisor (Claude como annotator auxiliar, com limites documentados)
- Versionado e rastreável (quem anotou, quando, hash do documento)

### 3. Contract testing via snapshots
gbr-eval mantém estrutura para cópias dos schemas de API dos repos alvo em `contracts/schemas/` (atualmente vazio — preparado para populamento). Quando populado, mudanças de schema sem atualizar o snapshot quebram o CI. O frontend já tem CRUD de contracts, versioning e drift detection prontos.

### 4. Separação build-time vs operate-time
- **Build-time (CI):** graders rodam como gate antes do merge. Resultado: pass/fail no PR.
- **Operate-time (futuro camada operational):** graders rodam como sampling em produção. Resultado: métricas, alertas, dashboards.
- Mesmos graders, contextos diferentes. A configuração (threshold, blocking vs informative) muda, o código não.

### 5. Schema wide, implementation narrow
Os schemas Pydantic cobrem as 4 camadas (engineering, product, operational, compliance). A implementação atual cobre engineering e product. Schemas de operational e compliance existem mas não têm tasks nem graders — estão prontos para quando a produção existir.

### 6. LLM-judge: informative primeiro, blocking depois
O LLM-judge começa como **informative** no CI (anota no PR, não bloqueia merge). Após 50+ runs, mede auto-concordância (mesmo input 3x → mesmo resultado?). Se concordância >= 0.90, promove a blocking. Decisão baseada em dados, não palpite.

### 7. PR risk labeling: label sim, auto-merge não
O CI aplica label `eval:low-risk` quando todos os graders determinísticos passam e nenhum arquivo sensível foi tocado. O reviewer faz review focado (5 min) em vez de completo (30 min). Review humano continua obrigatório. Amostragem: 1 em cada 5 low-risk PRs recebe review completo aleatoriamente.

## Gate Fase 1 — Mapeamento para Graders

Os 13 critérios do Gate Fase 1 (Confluence ADA) que este eval deve verificar:

| # | Critério Gate | Grader(s) | Layer |
|---|---|---|---|
| 1 | Classification >= 90% | `accuracy` over golden set | product |
| 2 | Extraction >= 95% (P0) | `field_f1` per field | product |
| 3 | Citation linking = 100% | `field_not_empty` on citation | product |
| 4 | Evaluator detection >= 80% | Red team suite (injected docs) | product |
| 5 | Cost <= R$50/journey | `numeric_range` on cost metric | product |
| 6 | Audit trail = 100% | Schema completeness check | engineering/product |
| 7 | Security P0 = Zero | SAST + manual (fora do eval) | engineering |
| 8 | SLA P95 < 10 min | `numeric_range` on duration | operational |
| 9-13 | Business/UX criteria | Fora do escopo do eval automatizado | — |

## 5 P0 Skills — Golden Sets Prioritários

| Skill | Documento | Campos Críticos |
|---|---|---|
| `matricula_v1` | Matrícula imóvel | nº registro, proprietário CPF/CNPJ, área, ônus, alienação fiduciária |
| `contrato_social_v1` | Contrato social | CNPJ, razão social, sócios %, capital, poderes |
| `cnd_v1` | Certidão negativa | tipo, número, órgão, validade, status |
| `procuracao_v1` | Procuração | outorgante, outorgado, poderes específicos, validade |
| `certidao_trabalhista_v1` | Certidão trabalhista | titular, resultado, processos (array), órgão emissor |
| ~~`balanco_v1`~~ | ~~Balanço patrimonial~~ | ~~Blocked — 0 docs disponíveis. Substituído por certidao_trabalhista~~ |

## Regras de decisão determinísticas

O motor de decisão NÃO usa LLM. É determinístico e avaliável com graders puros:

```
Score >= 0.90 AND zero critical non-conforming → aprovado
Score >= 0.70 AND critical conforming AND >= 1 warning → aprovado_com_ressalvas
Any critical non-conforming → reprovado
>= 3 critical fields nao_verificavel → inconclusivo
```

Score = SUM(field_weight × field_confidence) / SUM(critical_weights)
- CRITICAL: weight 3
- IMPORTANT: weight 2
- INFORMATIVE: weight 1

## Classificação de dados e LGPD

### Classificação dos artefatos do gbr-eval

| Artefato | Classificação | Tratamento |
|----------|--------------|-----------|
| Código-fonte (graders, harness) | PÚBLICO | Pode ser open-source |
| Task YAMLs | INTERNO | Revelam critérios de qualidade, não expor a clientes |
| Golden sets (anonimizados) | RESTRITO | Contêm estrutura de documentos financeiros |
| Golden sets (PII original) | **PROIBIDO no repo** | NUNCA commitar — anonimizar ANTES |
| Resultados de eval runs | INTERNO | Contêm scores e detalhes de falhas |
| Rubrics do LLM-judge | INTERNO | Revelam critérios de julgamento |
| Contract schemas | INTERNO | Revelam estrutura de APIs internas |

### Regras LGPD para golden sets

1. **Anonimização obrigatória ANTES de entrar no repo:**
   - CPF: substituir por `000.000.000-XX` (manter últimos 2 dígitos para validação de formato)
   - CNPJ: substituir por `00.000.000/0000-XX`
   - Nomes: substituir por nomes fictícios (manter padrão: 2-3 palavras)
   - Endereços: substituir rua/número, manter cidade/estado
   - Valores monetários: manter ordem de grandeza, alterar dígitos
2. **Hash do documento original** (SHA-256) armazenado no metadata.yaml — permite rastrear sem expor
3. **Nunca logar** conteúdo de golden sets em CI output ou relatórios — apenas scores e field names
4. **Retenção:** golden sets seguem política de retenção da GarantiaBR (5 anos ISO 27001)

## Code Safety

- **Nunca logar** API keys, JWT tokens, ou prompts completos do LLM-judge
- **Nunca hardcodar** thresholds dentro de graders — receber como config via GraderSpec
- **Nunca commitar** `.env`, credenciais, ou dados não-anonimizados
- **Nunca importar** código de gbr-engines diretamente — usar contract schemas
- **Secrets:** `ANTHROPIC_API_KEY` é a única env var sensível. Testes que dependem dela usam `pytest.mark.skipif`
- **PII no LLM-judge:** sanitização recursiva de CPF, CNPJ, RG, PIS/PASEP, telefone e email antes de enviar ao modelo. Mensagens de erro também são sanitizadas via `_sanitize_pii_str()`.
- **SSRF:** `EvalClient` resolve DNS e bloqueia IPs internos (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16). Bypass explícito via `allow_internal=True` para dev local.
- **Frontend auth:** middleware com comparação timing-safe (SHA-256 via Web Crypto) + fail-closed quando `ADMIN_API_TOKEN` não configurado (retorna 503, dev bypass via `DISABLE_AUTH=true`)

## Convenções obrigatórias

- **Branch:** `tipo/descricao-curta` (ex: `feat/grader-field-f1`, `fix/runner-timeout`)
- **Commit:** `tipo(escopo): mensagem` — Conventional Commits
  - **Escopos válidos:** graders, harness, contracts, golden, calibration, tasks, docs, ci, frontend
- **PR:** `[EVAL] tipo: descricao` (sem Jira até ter projeto próprio)
- **Testes:** pytest, padrão AAA (Arrange, Act, Assert), coverage >= 80%
- **Naming:** `test_<action>_<result>` (ex: `test_exact_match_pass_when_equal`)
- **Lint:** ruff (config em pyproject.toml)
- **Types:** mypy strict
- **Python:** 3.12+
- **Cada serviço Python no gbr-engines usa:** Ruff, mypy, pytest — gbr-eval segue o mesmo padrão

## Qualidade de código

Regras detalhadas em `.claude/rules/`:

| Arquivo | Regra |
|---------|-------|
| `00-eval-principles.md` | Nunca gerar golden sets automaticamente, graders puros, zero tautologia |

### SOLID adaptado para eval

- **SRP:** cada grader faz uma coisa. `exact_match` compara valores, não calcula F1.
- **OCP:** novos graders via `@register_grader(name)`, não via if/else no runner.
- **LSP:** todo grader implementa a interface `Grader` (protocol). O runner não sabe qual tipo é.
- **ISP:** `GraderSpec.config` é dict genérico — cada grader lê apenas as chaves que precisa.
- **DIP:** runner depende da interface `grade()`, não de implementações concretas.

### Harness Engineering — VibeCodable vs Hardening

| Categoria | Exemplos | IA pode gerar? | Revisão necessária |
|-----------|----------|---------------|-------------------|
| **VibeCodable** | Novos graders determinísticos, task YAMLs, testes, reporter formatters | SIM | Code review normal |
| **Hardening** | Rubrics do LLM-judge, thresholds de aprovação, golden sets, calibração | NÃO — humano decide | Diogo aprova |

## Frontend — Admin Panel de Eval

O frontend é uma aplicação Next.js 16 com SQLite local que serve como painel de administração e observabilidade do eval. Não é um dashboard estático — é uma aplicação completa com 40 páginas e 57 API routes.

### Módulos

| Módulo | O que faz |
|--------|-----------|
| **Dashboard** | KPIs, recent runs, active alerts, quick links |
| **Runs** | Import, view, trends, comparison, postmortem |
| **Golden Sets** | CRUD, import/export JSON, case versioning, PII redaction |
| **Tasks** | Definição de tasks, graders, thresholds |
| **Rubrics** | CRUD, A/B testing, concordance tracking, promotion lifecycle |
| **Conventions** | Rules, coverage matrix, import de CLAUDE.md |
| **Calibration** | Sessions, annotations, disagreements, Cohen's kappa |
| **Contracts** | Schema snapshots, version history, OpenAPI import, drift detection |
| **Skills** | Skill definitions, field schemas, criticality |
| **Alerts** | Score drops, regressions, trend declines |

### Webhook para CI
`POST /api/runs/webhook` com Bearer token auth permite ingestão de eval runs diretamente do CI pipeline.

### DB local (SQLite)
23 tabelas via Drizzle ORM. WAL mode. Foreign keys enforced. PII redaction em endpoints de golden sets e grader data.

## Relação com gbr-engines

gbr-eval é **consumidor** de gbr-engines, nunca ao contrário:
- Lê schemas de API (via snapshots em `contracts/`)
- Lê golden sets exportados (via `golden/`)
- Roda graders contra outputs reais ou gravados
- NUNCA importa código de gbr-engines diretamente
- NUNCA altera código de gbr-engines

### Contexto necessário de gbr-engines

Para entender o que este eval avalia, consultar no gbr-engines:
- `CLAUDE.md` — convenções que a camada engineering verifica
- `services/ai-engine/app/prompts/` — prompts dos agentes IA (camada product eval target)
- `services/athena/` — motor de regras determinístico (camada product eval target)
- `shared/scoring/field_comparison.py` — scoring engine (referência para field_f1)
- `docs/EVALS.md` — spec do eval legado (referência do que NÃO repetir)
- `evals/harness/mock_generator.py` — anti-pattern: tautological testing

## Regras de autonomia

### AUTÔNOMO (sem aprovação)
- Criar/editar graders, tasks, testes, docs dentro do projeto
- Rodar testes locais, linters, type checkers
- Criar branches e commits
- Consultar Jira e Confluence (read-only)

### PEDIR APROVAÇÃO
- Alterar limiares de aprovação/reprovação em tasks
- Adicionar novo grader type
- Modificar schema de Task (models.py)
- Abrir Pull Request
- Instalar novas dependências (pyproject.toml)

### BLOQUEADO (nunca fazer)
- Validar golden sets (CLO valida — Diogo)
- Decidir se grader é blocking vs informative
- Push direto em main/master
- Deletar branches remotas
- Alterar contratos de API dos repos alvo
- Commitar dados não-anonimizados (PII, documentos reais)
- Acessar ou logar credentials, tokens, secrets, API keys
- Expor dados RESTRITO ou CONFIDENCIAL em logs ou outputs

## Sincronização obrigatória

Antes de qualquer alteração de código, **sempre** executar `git pull`. Múltiplos desenvolvedores podem trabalhar neste repo e divergências causam conflitos.

## Fluxo padrão de uma task

1. `git pull` — sincronizar com o remoto
2. Criar branch (`tipo/descricao-curta`)
3. Implementar + testes (cobertura >= 80%)
4. Quality gates: `uv run pytest && uv run ruff check . && uv run mypy src/`
5. Abrir PR com descrição clara do que mudou
6. Review + merge
