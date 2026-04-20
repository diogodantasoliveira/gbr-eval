# gbr-eval Frontend — Roadmap Completo

> **Owner:** Diogo Dantas (CAIO)
> **Criado:** 2026-04-18
> **Status:** Draft — aguardando aprovação para iniciar Sprint 1
> **Deadline externa:** Gate Fase 1 (Pine) ~10/Mai/2026

---

## 1. Propósito

O gbr-eval CLI avalia qualidade, mas depende de inputs humanos que hoje são hardcoded em YAMLs e JSONs.
Este frontend standalone permite que **engenheiros e não-engenheiros** gerenciem:

- Golden sets (anotação, revisão, versionamento)
- Tasks de avaliação (criação, configuração de graders)
- Rubrics do LLM-judge (critérios de julgamento)
- Scoring thresholds (limiares por documento e tenant)
- Convention rules (engineering — regras do dev agent)
- Calibração inter-anotador (Cohen's kappa)
- Contratos de API (schema snapshots)
- Resultados de eval runs (dashboard, drill-down, tendências)

**Sem este frontend**, todo input humano exige editar arquivos YAML/JSON no repo — barreira para CLO, QA, e product managers.

---

## 2. Decisão de Stack

| Camada | Escolha | Justificativa |
|--------|---------|---------------|
| **Framework** | Next.js 15 (App Router) | Mesmo stack do gbr-engines frontend e admin-panel — reuso de conhecimento |
| **UI** | shadcn/ui + Tailwind CSS | Componentização, dark mode nativo, acessibilidade |
| **Estado** | Zustand | Leve, sem boilerplate, já usado nos frontends GarantiaBR |
| **DB** | SQLite (via better-sqlite3) | Zero infra, portável, suficiente para volume de eval |
| **API** | Next.js API Routes (Route Handlers) | Monolito simplificado — sem serviço separado |
| **Monorepo** | NÃO — app standalone | Deploy independente, ciclo de release próprio |
| **Auth** | Fase 1: sem auth (uso interno). Fase 2: Cognito SSO (quando multi-user) |
| **Porta** | 3002 | Não conflita com frontend (3000) nem admin-panel (3001) |

### Por que SQLite e não PostgreSQL?

- Volume baixo: ~5 P0 skills × ~50 golden sets × ~13 graders = centenas de registros, não milhões
- Portabilidade: `gbr-eval.db` viaja com o repo (ou .gitignore se contém dados RESTRITO)
- Zero dependência: não precisa de Docker/container para rodar
- Migração futura: se volume crescer, trocar por PostgreSQL é trivial (Drizzle ORM abstrai)
- **Connection setup:** `PRAGMA journal_mode = WAL` (write-ahead logging para concorrência) + `PRAGMA foreign_keys = ON` (enforcement de FKs) em toda conexão

---

## 3. Escopo Completo — O que o gbr-eval Avalia

### 3.1 gbr-engines: 19 Serviços Alvo

| Serviço | Tipo | O que o eval verifica |
|---------|------|----------------------|
| **ai-engine (ZEUS)** | Python FastAPI | Extração, classificação, scoring, parecer, chat |
| **demeter** | Python FastAPI | Orquestração de pipeline, sequenciamento |
| **athena** | Go Lambda | Regras determinísticas, JSONLogic, most-restrictive-wins |
| **integrations (APOLO)** | Python FastAPI | 33 adapters (SERPRO, ONR, CNJ, Judit, etc.) |
| **billing (PLUTOS)** | Python FastAPI | 5 pricing models, usage recording, P&L |
| **hades** | Python FastAPI | RPAs e automações |
| **hermes** | Python FastAPI | Notificações multi-canal |
| **document-vault** | Python FastAPI | Storage de documentos, presigned URLs |
| **iam** | Python FastAPI | Roles, permissões, grupos, tenant isolation |
| **risk-scoring** | Python FastAPI | Modelos de risco |
| **audit-service** | Python FastAPI | Trail de auditoria |
| **research-service** | Python FastAPI | Pesquisa de bens, crosswalk elementos |
| **queue-service** | Python FastAPI | Filas assíncronas |
| **webhook-service** | Python FastAPI | Webhooks inbound/outbound |
| **scheduler** | Python FastAPI | Cron jobs, agendamentos |
| **analytics** | Python FastAPI | Métricas e reporting |
| **frontend** | Next.js 15 | 25 páginas, 88 BFF routes |
| **admin-panel** | Next.js 15 | 104 páginas, 179 BFF routes |
| **gateway** | Infra | API Gateway, rate limiting |

### 3.2 Camadas de Avaliação

```
┌─────────────────────────────────────────────────────────┐
│ Engineering — Static Quality + Dev Agent                │
│ (lint, type-check, tests — JÁ EXISTE no CI dos repos)  │
│ Segue CLAUDE.md? tenant_id filter? Sem hardcode?        │
│ Enum proibido? Middleware correto? BFF ports?            │
│ → 18 checklist items de MEMORY.md + CLAUDE.md           │
├─────────────────────────────────────────────────────────┤
│ Product — Product AI                                    │
│ Extração correta? Classificação >= 90%?                 │
│ Scoring bate com golden set? Custo <= R$50?             │
│ → 13 critérios Gate Fase 1 + golden sets                │
├─────────────────────────────────────────────────────────┤
│ Operational — SLAs, Custos, Disponibilidade (futuro)   │
├─────────────────────────────────────────────────────────┤
│ Compliance — LGPD, BACEN, ISO 27001 (futuro)           │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Taxonomia de Documentos (141 tipos, 5 P0)

| Prioridade | Skill | Doc Type | Campos Críticos |
|------------|-------|----------|-----------------|
| **P0** | `matricula_v1` | Matrícula imóvel | nº registro, proprietário CPF/CNPJ, área, ônus, alienação |
| **P0** | `contrato_social_v1` | Contrato social | CNPJ, razão social, sócios %, capital, poderes |
| **P0** | `cnd_v1` | Certidão negativa | tipo, número, órgão, validade, status |
| **P0** | `procuracao_v1` | Procuração | outorgante, outorgado, poderes, validade |
| **P0** | `balanco_v1` | Balanço patrimonial | ativo, passivo, PL, dívida líquida, liquidez |
| P1 | 10 skills | IPTU, RG, CNH, contracheque, extrato, etc. | Varia por tipo |
| P2 | 30+ skills | Demais tipos | Conforme expansão |
| P3 | 90+ skills | Long tail | Sob demanda |

### 3.4 Integrações (33 Adapters)

Cada adapter tem contrato de entrada/saída que precisa de eval:

| Grupo | Adapters | Eval Focus |
|-------|----------|------------|
| **SERPRO** | CPF, CNPJ, IRPF, etc. | Schema response, disponibilidade |
| **ONR** | 43 actions (matrícula, certidões) | TokenPool, retry, schema |
| **Judiciário** | CNJ, Judit, TJSP, etc. | Parsing de decisões, status |
| **Cartório** | CRC, CRI, RCPN | Schema certidões |
| **Receita** | CND, PGFN, Simples | Validade, status |
| **Outros** | ViaCEP, BacenJud, etc. | Disponibilidade, schema |

### 3.5 Billing (5 Pricing Models)

| Modelo | O que avaliar |
|--------|---------------|
| SaaS (subscription) | Plano correto atribuído, componentes JSONB |
| Transactional (per-event) | Evento correto disparado, preço cascata 8 níveis |
| Function Point | Contagem de pontos, markup tenant |
| Setup (one-time) | Cobrança única correta |
| Professional Services | Horas × rate, aprovação |

### 3.6 Athena (Motor de Decisão)

Regras 100% determinísticas — eval é puro:

| Aspecto | O que avaliar |
|---------|---------------|
| Score computation | `SUM(weight × confidence) / SUM(critical_weights)` |
| Thresholds | >= 0.90 → aprovado, >= 0.70 + warnings → ressalvas |
| Most-restrictive-wins | Múltiplas regras → resultado mais conservador |
| 5 severity levels | CRITICAL/HIGH/MEDIUM/LOW/INFO corretos |
| 5 behavior types | Mapeamento regra → ação correto |

---

## 4. Módulos do Frontend

### Módulo 1: Annotation Studio (Golden Sets)

**Prioridade: CRÍTICA — bloqueio Gate Fase 1**

Interface para criar, anotar, revisar, e versionar golden sets.

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| Upload de documento | PDF/imagem → viewer embutido | 1 |
| Formulário de anotação | Campos dinâmicos por skill (schema-driven) | 1 |
| Side-by-side view | Documento à esquerda, formulário à direita | 1 |
| Versionamento | Cada edição gera nova versão com diff | 1 |
| Status workflow | `draft → annotated → reviewed → approved` | 1 |
| Anonimização | CPF/CNPJ/nomes auto-redactados antes de salvar | 1 |
| Bulk import | Upload JSON batch de anotações existentes | 2 |
| Export | Download como JSON/YAML para uso no CLI | 1 |
| Field schema editor | Definir campos por skill (tipo, required, critical) | 2 |
| Histórico de versões | Timeline visual de cada golden set case | 2 |
| Tag management | Provenance tags: seed, regression, incident, edge_case, hitl | 1 |
| Filter by tags | Listar/filtrar cases por tag de provenance | 1 |

#### Data Model

```
golden_sets
├── id (UUID)
├── skill_id (FK → skills)
├── name (string)
├── description (text)
├── status (draft | annotated | reviewed | approved)
├── created_by (string)
├── created_at (datetime)
├── updated_at (datetime)
└── version (int)

golden_set_cases
├── id (UUID)
├── golden_set_id (FK → golden_sets)
├── case_number (int)
├── document_hash (SHA-256 do original)
├── document_path (string — referência ao arquivo)
├── input_data (JSON — payload de entrada)
├── expected_output (JSON — output esperado anotado pelo humano)
├── field_annotations (JSON — metadata por campo: quem anotou, confiança)
├── tags (JSON array — provenance: "seed", "regression", "incident", "edge_case", "hitl")
├── status (draft | annotated | reviewed | approved)
├── annotator (string)
├── reviewer (string | null)
├── created_at (datetime)
└── version (int)

golden_set_versions
├── id (UUID)
├── case_id (FK → golden_set_cases)
├── version (int)
├── expected_output (JSON — snapshot do output nesta versão)
├── changed_by (string)
├── changed_at (datetime)
└── change_reason (text)
```

#### Fluxo

```
1. Usuário seleciona skill (e.g., matricula_v1)
2. Upload ou seleciona documento existente
3. Viewer renderiza documento (PDF.js)
4. Formulário exibe campos do skill schema
5. Anotador preenche expected output
6. Sistema auto-redacta PII (CPF, CNPJ, nomes)
7. Save como draft → status "annotated"
8. Reviewer (CLO) revisa e aprova → status "approved"
9. Export gera JSON compatível com gbr-eval CLI
```

---

### Módulo 2: Skill Manager

**Prioridade: ALTA — pré-requisito do Annotation Studio**

Gerencia os skills (tipos de documento) e seus schemas de campos.

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| CRUD de skills | Nome, doc_type, versão, descrição | 1 |
| Field schema | Campos esperados por skill (nome, tipo, criticidade) | 1 |
| Criticidade por campo | CRITICAL (w:3) / IMPORTANT (w:2) / INFORMATIVE (w:1) | 1 |
| Versionamento | Novo schema = nova versão do skill | 2 |
| Import from gbr-engines | Sincronizar 141 doc types do ai-engine | 2 |
| Dependency graph | Quais graders, tasks, golden sets usam este skill | 3 |

#### Data Model

```
skills
├── id (UUID)
├── name (string — e.g., "matricula_v1")
├── doc_type (string — e.g., "matricula")
├── version (string — semver)
├── description (text)
├── priority (P0 | P1 | P2 | P3)
├── status (active | deprecated)
├── created_at (datetime)
└── updated_at (datetime)

skill_fields
├── id (UUID)
├── skill_id (FK → skills)
├── field_name (string — e.g., "cpf_proprietario")
├── field_type (string | number | boolean | date | list | nested)
├── criticality (CRITICAL | IMPORTANT | INFORMATIVE)
├── weight (float — derivado da criticidade)
├── required (boolean)
├── validation_pattern (regex | null)
├── description (text)
└── sort_order (int)
```

---

### Módulo 3: Task Builder

**Prioridade: ALTA — necessário para rodar evals**

Interface visual para criar e configurar tasks de avaliação (equivalente a escrever YAMLs manualmente).

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| Task wizard | Passo-a-passo: metadata → EVAL First checklist → input → expected → graders | 2 |
| EVAL First checklist | 7 perguntas obrigatórias antes de ativar task (sucesso, medição, baseline, gate, alvo, regressão, governança) | 2 |
| Grader picker | Selecionar graders do registry com autocompletion | 2 |
| Config editor | Formulário contextual por tipo de grader | 2 |
| YAML preview | Visualizar o YAML resultante em tempo real | 2 |
| Export YAML | Download individual ou batch | 2 |
| Import YAML | Upload de tasks existentes | 2 |
| Dry-run | Executar task localmente via API (chama CLI) | 3 |
| Templates | Criar tasks a partir de templates por categoria | 3 |
| Bulk generator | Gerar tasks para todos os cases de um golden set | 3 |

#### Data Model

```
tasks
├── id (UUID)
├── task_id (string — e.g., "extraction.matricula.cpf")
├── category (classification | extraction | decision | citation | cost | latency | code_quality | tenant_isolation | convention)
├── component (string — serviço alvo)
├── layer (engineering | product | operational | compliance)
├── tier (gate | regression | canary)
├── tenant_profile (string — default "global")
├── description (text)
├── scoring_mode (weighted | binary | hybrid)
├── pass_threshold (float 0.0-1.0)
├── target_threshold (float 0.0-1.0 | null — north star, acima do gate)
├── baseline_run_id (FK → eval_runs ON DELETE SET NULL | null — run de referência para regression delta)
├── regression_signal (text | null — descrição do que indica regressão)
├── skill_id (FK → skills | null)
├── golden_set_id (FK → golden_sets | null)
├── status (draft | active | archived)
├── created_at (datetime)
└── updated_at (datetime)

task_graders
├── id (UUID)
├── task_id (FK → tasks)
├── grader_type (string — e.g., "exact_match", "field_f1", "llm_judge")
├── field (string | null)
├── weight (float)
├── required (boolean)
├── config (JSON)
└── sort_order (int)

task_inputs
├── id (UUID)
├── task_id (FK → tasks)
├── endpoint (string | null)
├── payload (JSON)
└── fixture_path (string | null)
```

---

### Módulo 4: Rubric Editor (LLM-Judge)

**Prioridade: MÉDIA — necessário para graders model-based**

Interface para criar e versionar rubrics do LLM-judge.

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| Editor de rubric | Markdown/rich-text com preview | 2 |
| Critérios estruturados | Lista de critérios com peso por item | 2 |
| Exemplos inline | Pares (input, output, score) como few-shot | 2 |
| Versionamento | Cada edição gera nova versão com diff | 2 |
| A/B testing | Comparar duas rubrics no mesmo golden set | 4 |
| Auto-concordância | Métricas de consistência (3x mesmo input) | 4 |
| Promotion tracker | Informative → blocking status por rubric | 4 |

#### Data Model

```
rubrics
├── id (UUID)
├── name (string — e.g., "matricula_extraction_quality")
├── skill_id (FK → skills | null)
├── category (extraction | classification | decision | general)
├── rubric_text (text — o prompt de avaliação)
├── min_score (float — threshold para pass)
├── model (string — e.g., "claude-sonnet-4-5-20250514")
├── status (draft | active | deprecated)
├── promotion_status (informative | blocking)
├── version (int)
├── created_at (datetime)
└── updated_at (datetime)

rubric_criteria
├── id (UUID)
├── rubric_id (FK → rubrics)
├── criterion (text)
├── weight (float)
├── score_anchor_low (text — o que score 1 significa)
├── score_anchor_high (text — o que score 5 significa)
└── sort_order (int)

rubric_examples
├── id (UUID)
├── rubric_id (FK → rubrics)
├── input_data (JSON)
├── output_data (JSON)
├── expected_score (int 1-5)
├── reasoning (text)
└── sort_order (int)

rubric_versions
├── id (UUID)
├── rubric_id (FK → rubrics)
├── version (int)
├── rubric_text (text)
├── changed_by (string)
├── changed_at (datetime)
└── change_reason (text)
```

---

### Módulo 5: Convention Manager (Engineering Rules)

**Prioridade: ALTA — necessário para engineering eval**

Gerencia as regras que o dev agent (Claude Code) deve seguir.

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| Rule CRUD | Criar/editar regras com nome, padrão, severidade | 3 |
| Categories | Agrupar por: tenant isolation, naming, architecture, security | 3 |
| Pattern editor | Regex ou AST pattern para detectar violação | 3 |
| Anti-patterns | Exemplos de código que viola a regra | 3 |
| Positive examples | Exemplos de código que segue a regra | 3 |
| Import from CLAUDE.md | Parse automático das regras existentes | 3 |
| Export | Gerar tasks YAML engineering a partir das regras | 3 |
| Coverage matrix | Quais regras têm tasks, quais faltam | 3 |

#### Data Model

```
convention_rules
├── id (UUID)
├── name (string — e.g., "tenant_id_filter")
├── category (tenant_isolation | naming | architecture | security | data_handling | api_design)
├── severity (critical | high | medium | low)
├── description (text)
├── detection_pattern (text — regex ou description para LLM)
├── detection_type (regex | ast | llm_judge)
├── positive_example (text — código correto)
├── negative_example (text — código que viola)
├── source (string — e.g., "CLAUDE.md #12")
├── status (active | deprecated)
├── created_at (datetime)
└── updated_at (datetime)
```

#### Regras Engineering a Mapear (dos 18 itens MEMORY.md)

| # | Regra | Severidade | Detection |
|---|-------|-----------|-----------|
| 1 | BFF → ATOM: atomHeaders(), NUNCA serviceAuthKey() | critical | regex |
| 2 | Client-side fetch: SEMPRE credentials: 'include' | high | regex |
| 3 | Response paginada: Array.isArray check | medium | ast |
| 4 | Turbopack cache: rm -rf .next após edições | low | llm_judge |
| 5 | Dark mode: SEMPRE dark: variants | medium | regex |
| 6 | FastAPI routes: fixas ANTES de parametrizadas | high | ast |
| 7 | DB local: CREATE TABLE IF NOT EXISTS | medium | regex |
| 8 | Billing routes: prefix /api/v1 | high | regex |
| 9 | cd correto antes de pnpm/uv | medium | llm_judge |
| 10 | provider_action = slug do adapter | high | llm_judge |
| 11 | Nunca hardcodar dados de negócio | critical | llm_judge |
| 12 | user.role é VARCHAR, nunca .role.value | critical | regex |
| 13 | JWT: custom:roles, NÃO role | critical | regex |
| 14 | BFF portas: conferir SERVICES.md | high | llm_judge |
| 15 | Middleware: excluir /api/* de redirect | high | regex |
| 16 | Nunca declarar feature pronta sem curl | medium | llm_judge |
| 17 | Secrets: rodar trufflehog/gitleaks | high | llm_judge |
| 18 | Verificar endpoint existe antes de UI | high | llm_judge |

---

### Módulo 6: Run Dashboard

**Prioridade: MÉDIA — útil após ter tasks e golden sets**

Visualização de resultados de eval runs.

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| Run list | Tabela com ID, layer, tier, score, pass/fail, timestamp | 3 |
| Run detail | Drill-down: tasks → graders → details | 3 |
| Severity grouping | Agrupar falhas por severity (critical/high/medium/low) | 3 |
| Regression delta view | Comparar run atual vs baseline: newly failing, newly passing, score deltas | 3 |
| Trend charts | Score ao longo do tempo por skill/category | 3 |
| Trend degradation alerts | Detectar score em declínio por N runs consecutivos mesmo acima do threshold | 3 |
| Diff runs | Comparar dois runs lado a lado | 3 |
| Import results | Upload de JSON output do CLI | 3 |
| Gate matrix result | Exibir resultado em 4 níveis: GO / CONDITIONAL GO / NO-GO / NO-GO ABSOLUTO | 3 |
| CI integration | Webhook para receber resultados automaticamente | 4 |
| Filtros | Por layer, tier, category, component, skill, severity | 3 |
| Alertas | Notificar quando score cai abaixo de threshold | 4 |
| Post-mortem tracking | Registrar post-mortem (5 linhas: what/cause/impact/fix/prevention) vinculado a run | 4 |

#### Gate Matrix

O resultado de cada run é classificado em 4 níveis (inspirado no OODA-EVAL):

| Resultado | Condição | Ação |
|-----------|----------|------|
| **GO** | Todas as dimensões >= pass_threshold | Avança |
| **CONDITIONAL GO** | Required graders passam, optional abaixo do threshold | Avança com flag + issue criado |
| **NO-GO** | Qualquer required grader falha | Retorna para iteração |
| **NO-GO ABSOLUTO** | Regressão em dimensão que passava antes | Prioridade máxima |

#### Data Model

```
eval_runs
├── id (UUID)
├── run_id (string — do CLI)
├── layer (engineering | product | operational | compliance)
├── tier (gate | regression | canary | null)
├── tasks_total (int)
├── tasks_passed (int)
├── tasks_failed (int)
├── overall_score (float)
├── gate_result (go | conditional_go | no_go | no_go_absolute)
├── baseline_run_id (FK → eval_runs | null — run de referência)
├── started_at (datetime)
├── finished_at (datetime)
├── metadata (JSON — git sha, branch, CI job ID)
├── source (cli | ci | manual)
└── imported_at (datetime)

eval_task_results
├── id (UUID)
├── run_id (FK → eval_runs)
├── task_id (string)
├── passed (boolean)
├── score (float)
├── severity (critical | high | medium | low)
├── duration_ms (float)
├── error (text | null)
├── regression_status (new_failure | new_pass | stable_pass | stable_fail | null)
└── grader_results (JSON — array de GraderResult)

eval_postmortems
├── id (UUID)
├── run_id (FK → eval_runs)
├── task_id (string | null — se específico de uma task)
├── what (text)
├── root_cause (text)
├── impact (text)
├── fix (text)
├── prevention (text)
├── created_by (string)
└── created_at (datetime)
```

---

### Módulo 7: Calibration Panel

**Prioridade: BAIXA para Gate Fase 1 — essencial para product blocking**

Interface para calibração inter-anotador e promoção de graders.

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| Annotation queue | Fila de cases para anotação dupla | 4 |
| Blind review | Anotador 2 não vê output do anotador 1 | 4 |
| Cohen's kappa | Cálculo automático por skill/campo | 4 |
| Concordance dashboard | Visualizar kappa ao longo do tempo | 4 |
| Disagreement resolution | Interface para resolver discordâncias | 4 |
| LLM auto-concordance | 3x mesmo input → medir consistência do LLM-judge | 4 |
| Promotion workflow | Informative → blocking quando kappa >= 0.75 | 4 |

#### Data Model

```
calibration_sessions
├── id (UUID)
├── skill_id (FK → skills)
├── golden_set_id (FK → golden_sets)
├── annotator_1 (string)
├── annotator_2 (string)
├── status (in_progress | completed)
├── cohens_kappa (float | null)
├── started_at (datetime)
└── completed_at (datetime | null)

calibration_annotations
├── id (UUID)
├── session_id (FK → calibration_sessions)
├── case_id (FK → golden_set_cases)
├── annotator (string)
├── annotations (JSON — output do anotador)
├── created_at (datetime)
└── is_blind (boolean)

calibration_disagreements
├── id (UUID)
├── session_id (FK → calibration_sessions)
├── case_id (FK → golden_set_cases)
├── field_name (string)
├── annotator_1_value (text)
├── annotator_2_value (text)
├── resolution (text | null)
├── resolved_by (string | null)
└── resolved_at (datetime | null)
```

---

### Módulo 8: Contract Registry

**Prioridade: MÉDIA — necessário para schema drift detection**

Gerencia snapshots de schemas de API dos repos alvo.

#### Funcionalidades

| Feature | Descrição | Sprint |
|---------|-----------|--------|
| Schema list | Todos os contratos registrados | 3 |
| Schema viewer | JSON Schema renderizado com syntax highlighting | 3 |
| Diff viewer | Comparar versões de um schema | 3 |
| Import from OpenAPI | Parse automático de specs dos serviços | 3 |
| Drift alerts | Notificar quando schema do repo alvo mudou | 4 |
| Validation rules | Configurar quais campos são required/optional | 3 |

#### Data Model

```
contracts
├── id (UUID)
├── service_name (string — e.g., "ai-engine")
├── endpoint (string — e.g., "/api/v1/extract")
├── method (GET | POST | PUT | DELETE)
├── schema_snapshot (JSON — JSON Schema do response)
├── version (int)
├── source_commit (string — git SHA de onde extraiu)
├── status (active | deprecated)
├── created_at (datetime)
└── updated_at (datetime)

contract_versions
├── id (UUID)
├── contract_id (FK → contracts)
├── version (int)
├── schema_snapshot (JSON)
├── diff_from_previous (JSON | null)
├── imported_at (datetime)
└── imported_by (string)
```

---

## 5. Plano de Sprints

### Diagrama de Dependências

```
                        ┌──────────────┐
                        │ Skill Manager│ ← Pré-requisito de tudo
                        └──────┬───────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
          ┌──────▼──────┐ ┌───▼────┐ ┌──────▼──────┐
          │  Annotation │ │  Task  │ │  Convention │
          │   Studio    │ │Builder │ │   Manager   │
          └──────┬──────┘ └───┬────┘ └──────┬──────┘
                 │            │             │
          ┌──────▼──────┐    │       ┌──────▼──────┐
          │   Rubric    │    │       │  (gera tasks│
          │   Editor    │    │       │engineering) │
          └──────┬──────┘    │       └─────────────┘
                 │            │
          ┌──────▼────────────▼──────┐
          │     Run Dashboard        │
          └──────────┬───────────────┘
                     │
          ┌──────────▼───────────────┐
          │   Calibration Panel      │
          └──────────────────────────┘
          
          ┌──────────────────────────┐
          │   Contract Registry      │  ← Independente
          └──────────────────────────┘
```

---

### Sprint 1 — Foundation + Annotation (Semanas 1-2)
**Meta: Anotar golden sets para Gate Fase 1**
**Deadline: 02/Mai/2026**

| # | Task | Módulo | Estimativa | Bloqueio? |
|---|------|--------|------------|-----------|
| 1.1 | Setup Next.js 15 + shadcn/ui + SQLite + Drizzle ORM | Infra | 4h | — |
| 1.2 | Schema DB completo (todas as tabelas acima) | Infra | 4h | — |
| 1.3 | Seed dos 5 P0 skills com field schemas | Skill Manager | 3h | — |
| 1.4 | CRUD de skills (list, create, edit, view) | Skill Manager | 6h | — |
| 1.5 | Field schema editor por skill | Skill Manager | 4h | 1.4 |
| 1.6 | Golden set CRUD | Annotation Studio | 6h | 1.4 |
| 1.7 | Case annotation form (schema-driven) | Annotation Studio | 8h | 1.5, 1.6 |
| 1.8 | Document viewer (PDF.js) side-by-side | Annotation Studio | 6h | 1.7 |
| 1.9 | Auto-PII redaction (CPF, CNPJ, nomes) | Annotation Studio | 3h | 1.7 |
| 1.10 | Export golden set como JSON (CLI-compatible) | Annotation Studio | 3h | 1.6 |
| 1.11 | Status workflow (draft→annotated→reviewed→approved) | Annotation Studio | 3h | 1.6 |
| 1.12 | Version history per case | Annotation Studio | 4h | 1.6 |
| 1.13 | Tag management UI (CRUD provenance tags per case) | Annotation Studio | 3h | 1.6 |
| 1.14 | Filter/search cases by tags | Annotation Studio | 2h | 1.13 |
| | **Total Sprint 1** | | **59h** | |

**Entregável:** Anotar os 5 P0 golden sets (~26 cases total) usando o frontend.

> **Esforço de anotação (CLO):** As 59h acima cobrem desenvolvimento do tooling. A anotação dos 26+ cases pelo CLO (Diogo) é trabalho adicional: ~1h/case (prep documento + anotação + auto-revisão) = ~26-30h, parcialmente sobreposto com o desenvolvimento.

---

### Sprint 2 — Tasks + Rubrics (Semanas 3-4)
**Meta: Configurar todas as tasks para Gate Fase 1**
**Deadline: 10/Mai/2026 (Gate)**

| # | Task | Módulo | Estimativa | Bloqueio? |
|---|------|--------|------------|-----------|
| 2.1 | Task wizard (step-by-step com EVAL First checklist) | Task Builder | 8h | — |
| 2.2 | EVAL First checklist gate (7 perguntas obrigatórias para ativar task) | Task Builder | 3h | 2.1 |
| 2.3 | Grader picker com config contextual | Task Builder | 6h | 2.1 |
| 2.4 | YAML preview em tempo real | Task Builder | 3h | 2.1 |
| 2.5 | Import/export YAML | Task Builder | 4h | 2.1 |
| 2.6 | Bulk task generation from golden set | Task Builder | 4h | 2.1 |
| 2.7 | Rubric editor (markdown + preview) | Rubric Editor | 6h | — |
| 2.8 | Rubric criteria list com pesos | Rubric Editor | 4h | 2.7 |
| 2.9 | Rubric examples (few-shot pairs) | Rubric Editor | 3h | 2.7 |
| 2.10 | Rubric versioning | Rubric Editor | 3h | 2.7 |
| 2.11 | Bulk import golden sets existentes (JSON) | Annotation Studio | 3h | — |
| | **Total Sprint 2** | | **47h** | |

**Entregável:** Todas as tasks Gate Fase 1 criadas e exportadas, rubrics do LLM-judge configuradas.

---

### Sprint 3 — Dashboard + Contracts + Conventions (Semanas 5-6)
**Meta: Visualizar resultados, detectar schema drift, e gerenciar convention rules engineering**

| # | Task | Módulo | Estimativa | Bloqueio? |
|---|------|--------|------------|-----------|
| 3.1 | Run list view com filtros (incl. severity) | Run Dashboard | 6h | — |
| 3.2 | Run detail: tasks → graders drill-down com severity grouping | Run Dashboard | 6h | 3.1 |
| 3.3 | Import JSON results do CLI (incl. regression delta; derive `regression_status` per task — ver nota¹) | Run Dashboard | 4h | 3.1 |
| 3.4 | Regression delta view (newly failing/passing, score deltas) | Run Dashboard | 6h | 3.3 |
| 3.5 | Trend charts (score over time por skill) | Run Dashboard | 6h | 3.1 |
| 3.6 | Trend degradation alerts (N runs consecutivos em declínio) | Run Dashboard | 4h | 3.5 |
| 3.7 | Gate matrix result display (GO/CONDITIONAL/NO-GO) | Run Dashboard | 3h | 3.1 |
| 3.8 | Run diff (side-by-side comparison) | Run Dashboard | 4h | 3.1 |
| 3.9 | Contract CRUD | Contract Registry | 4h | — |
| 3.10 | Schema viewer (JSON Schema rendering) | Contract Registry | 4h | 3.9 |
| 3.11 | Schema diff viewer | Contract Registry | 4h | 3.9 |
| 3.12 | Import from OpenAPI spec | Contract Registry | 4h | 3.9 |
| 3.13 | Convention rule CRUD | Convention Manager | 4h | — |
| 3.14 | Import rules from CLAUDE.md parser | Convention Manager | 4h | 3.13 |
| 3.15 | Anti-pattern / positive-pattern editor | Convention Manager | 3h | 3.13 |
| 3.16 | Generate engineering tasks from convention rules | Convention Manager | 4h | 3.13 |
| 3.17 | Coverage matrix (rules × tasks) | Convention Manager | 4h | 3.13 |
| 3.18 | Skill dependency graph visualization | Skill Manager | 4h | — |
| 3.19 | Task dry-run (execute via API → CLI) | Task Builder | 6h | — |
| | **Total Sprint 3** | | **84h** | |

**Entregável:** Dashboard funcional com regression delta e trend alerts, contratos de API dos 5 P0 services registrados, Convention Manager completo (engineering rules CRUD + import + export).

> ¹ **Import transform `regression_status`:** O backend retorna `newly_failing`, `newly_passing`, `stable_pass`, `stable_fail` como listas de `task_id`. O frontend deriva `regression_status` per-task no import: `task_id ∈ newly_failing → "new_failure"`, `∈ newly_passing → "new_pass"`, `∈ stable_pass → "stable_pass"`, `∈ stable_fail → "stable_fail"`.

---

### Sprint 4 — Calibration + Hardening (Semanas 7-8)
**Meta: Calibração inter-anotador e promoção de LLM-judge**

| # | Task | Módulo | Estimativa | Bloqueio? |
|---|------|--------|------------|-----------|
| 4.1 | Annotation queue (blind review) | Calibration Panel | 6h | — |
| 4.2 | Cohen's kappa calculation per field | Calibration Panel | 4h | 4.1 |
| 4.3 | Concordance dashboard | Calibration Panel | 6h | 4.2 |
| 4.4 | Disagreement resolution interface | Calibration Panel | 4h | 4.1 |
| 4.5 | LLM auto-concordance (3x test) | Calibration Panel | 4h | — |
| 4.6 | Rubric A/B testing | Rubric Editor | 6h | — |
| 4.7 | Promotion workflow (informative → blocking) | Calibration Panel | 4h | 4.2 |
| 4.8 | CI webhook receiver | Run Dashboard | 4h | — |
| 4.9 | Alert system (score drop notifications) | Run Dashboard | 4h | — |
| 4.10 | Post-mortem editor (5-line format) | Run Dashboard | 3h | — |
| 4.11 | Contract drift detection | Contract Registry | 4h | — |
| 4.12 | Global search across all modules | Infra | 4h | — |
| 4.13 | Keyboard shortcuts (power user UX) | Infra | 3h | — |
| | **Total Sprint 4** | | **56h** | |

**Entregável:** Pipeline completo de calibração, LLM-judge com promoção baseada em dados.

---

## 6. Cobertura Completa por Serviço gbr-engines

Mapeamento de cada serviço para módulos do frontend:

| Serviço | Skills | Tasks | Golden Sets | Contracts | Conventions |
|---------|--------|-------|-------------|-----------|-------------|
| ai-engine | 141 doc types | extraction, classification | 5 P0 + expansão | extract, classify, score | prompt handling |
| demeter | pipeline skills | orchestration sequence | pipeline golden sets | /pipeline/* endpoints | error handling |
| athena | decision rules | decision correctness | rule test cases | /rules/* endpoints | JSONLogic format |
| integrations | 33 adapters | availability, schema | adapter responses | per-adapter schemas | retry logic |
| billing | 5 pricing models | event recording, pricing | billing scenarios | /billing/* endpoints | event naming |
| iam | roles, permissions | tenant isolation | access control cases | /iam/* endpoints | role handling |
| document-vault | storage | upload/download | — | /documents/* | presigned URL |
| frontend | 25 pages | — | — | BFF routes | component naming |
| admin-panel | 104 pages | — | — | BFF routes | section structure |
| _outros 10 serviços_ | conforme demanda | conforme demanda | — | por endpoint | por padrão |

---

## 7. Integração com gbr-eval CLI

### 7.1 Export Pipeline

```
Frontend (SQLite) → Export → File System → CLI (runner.py)

1. Golden sets → golden/{skill}/ (JSON files)
2. Tasks → tasks/{layer}/{category}/ (YAML files)
3. Rubrics → rubrics/ (JSON files, referenciados por tasks)
4. Convention rules → tasks/engineering/convention/ (YAML files)
5. Contracts → contracts/schemas/ (JSON Schema files)
```

### 7.2 Import Pipeline

```
CLI output → Import → Frontend (SQLite)

1. CLI --output-format json → Upload no Run Dashboard
2. CI webhook → POST /api/runs → Armazena automaticamente
3. CLI --output-file result.json → Import manual
```

### 7.3 API Routes

```
/api/skills                    GET, POST
/api/skills/:id                GET, PUT, DELETE
/api/skills/:id/fields         GET, POST, PUT, DELETE

/api/golden-sets               GET, POST
/api/golden-sets/:id           GET, PUT, DELETE
/api/golden-sets/:id/cases     GET, POST
/api/golden-sets/:id/cases/:caseId  GET, PUT, DELETE
/api/golden-sets/:id/export    GET (download JSON)
/api/golden-sets/:id/import    POST (bulk upload)

/api/tasks                     GET, POST
/api/tasks/:id                 GET, PUT, DELETE
/api/tasks/:id/export          GET (download YAML)
/api/tasks/import              POST (upload YAML)
/api/tasks/bulk-generate       POST (from golden set)

/api/rubrics                   GET, POST
/api/rubrics/:id               GET, PUT, DELETE
/api/rubrics/:id/versions      GET
/api/rubrics/:id/test          POST (run against sample)

/api/conventions               GET, POST
/api/conventions/:id           GET, PUT, DELETE
/api/conventions/import-claude-md  POST (parse CLAUDE.md)
/api/conventions/:id/generate-task POST (create engineering task)

/api/runs                      GET, POST (import)
/api/runs/:id                  GET
/api/runs/:id/regression       GET (delta vs baseline)
/api/runs/:id/postmortem       GET, POST (5-line format)
/api/runs/compare              POST (diff two runs)
/api/runs/trends               GET (score trends with degradation alerts)
/api/runs/webhook              POST (CI callback)

/api/calibration/sessions      GET, POST
/api/calibration/sessions/:id  GET
/api/calibration/sessions/:id/annotate  POST
/api/calibration/sessions/:id/resolve   POST
/api/calibration/kappa         GET (metrics)

/api/contracts                 GET, POST
/api/contracts/:id             GET, PUT, DELETE
/api/contracts/:id/versions    GET
/api/contracts/import-openapi  POST
/api/contracts/check-drift     POST
```

---

## 8. 4 Loops de Avaliação

O frontend suporta 4 loops distintos, cada um com ciclo próprio:

### Loop 1: Golden Set Lifecycle (Annotation Studio)
```
Criar skill → Definir campos → Upload documento → Anotar →
Revisar (CLO) → Aprovar → Exportar → Usar no CLI →
Feedback do resultado → Refinar anotação → Nova versão
```

### Loop 2: Task Design (Task Builder + Convention Manager)
```
Identificar critério → Selecionar graders → Configurar thresholds →
Associar golden set → Preview YAML → Export → Rodar no CLI →
Analisar resultado → Ajustar config → Iterar
```

### Loop 3: LLM-Judge Maturation (Rubric Editor + Calibration)
```
Escrever rubric → Adicionar exemplos → Rodar como informative →
Medir auto-concordância → Calibrar com humano (kappa) →
Se kappa >= 0.75 → Promover a blocking → Monitorar drift
```

### Loop 4: Schema Governance (Contract Registry)
```
Registrar schema snapshot → Monitorar repo alvo →
Detectar drift → Alertar → Atualizar snapshot ou corrigir repo →
Validar que eval tasks ainda passam
```

---

## 9. Páginas do Frontend

```
/                                   → Dashboard home (summary de todos os módulos)
/skills                             → Lista de skills
/skills/new                         → Criar skill
/skills/:id                         → Detalhe do skill (campos, golden sets, tasks)
/skills/:id/fields                  → Editor de field schema

/golden-sets                        → Lista de golden sets
/golden-sets/new                    → Criar golden set
/golden-sets/:id                    → Detalhe (cases list)
/golden-sets/:id/cases/new          → Anotação de novo case
/golden-sets/:id/cases/:caseId      → View/edit case (side-by-side)
/golden-sets/:id/cases/:caseId/history → Versão history

/tasks                              → Lista de tasks
/tasks/new                          → Task wizard
/tasks/:id                          → Detalhe da task
/tasks/:id/preview                  → YAML preview

/rubrics                            → Lista de rubrics
/rubrics/new                        → Criar rubric
/rubrics/:id                        → Editor de rubric
/rubrics/:id/versions               → Version history
/rubrics/:id/test                   → Testar rubric contra sample

/conventions                        → Lista de convention rules
/conventions/new                    → Criar rule
/conventions/:id                    → Detalhe da rule
/conventions/coverage               → Coverage matrix

/runs                               → Lista de eval runs
/runs/:id                           → Detalhe do run
/runs/compare                       → Comparar runs
/runs/trends                        → Trend charts

/calibration                        → Calibration dashboard
/calibration/sessions/new           → Nova sessão
/calibration/sessions/:id           → Sessão de calibração
/calibration/sessions/:id/annotate  → Interface de anotação blind

/contracts                          → Lista de contratos
/contracts/new                      → Registrar contrato
/contracts/:id                      → Schema viewer
/contracts/:id/versions             → Diff viewer

/settings                           → Configurações gerais (DB path, export dir, defaults)
```

**Total: ~35 páginas**

---

## 10. Mapeamento de Camadas — gbr-eval vs OODA-EVAL

O documento organizacional OODA-EVAL (Bicalho/Rafa) usa numeração de camadas diferente em relação ao gbr-eval. Esta tabela é a referência canônica para tradução:

| Conceito | gbr-eval (tooling) | OODA-EVAL (organizacional) | Notas |
|----------|-------------------|---------------------------|-------|
| Static quality (lint, types, tests) | **engineering** | Implícito em L2 | CI dos repos alvo |
| Dev agent behavior (Claude Code) | **engineering** | **Sem equivalente** | OODA-EVAL não cobre LLM-as-developer |
| Product AI (extração, scoring) | **product** | **L3** | Mesmo escopo, nomenclatura diferente |
| Engenharia/Infra (SLA, uptime) | **operational** (futuro) | **L2** | Planejado no gbr-eval |
| Operação/HITL | `calibration/` | **L1** | gbr-eval cobre via Calibration Panel |
| Produto/Jornadas | Não é layer | **L4** | Fora do escopo gbr-eval |
| Estratégia/Negócio | Não é layer | **L5** | Fora do escopo gbr-eval |

**Regra:** A enum `Layer` em `src/gbr_eval/harness/models.py` é autoritativa para o tooling. Valores: `engineering`, `product`, `operational`, `compliance`.

---

## 11. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Sprint 1 atrasa → Gate Fase 1 sem golden sets | CRÍTICO | Fallback: anotar em JSON manualmente, importar depois |
| SQLite limita concorrência multi-user | MÉDIO | Fase 1 é single-user; migrar para PostgreSQL se necessário |
| 141 doc types = scope creep na Annotation Studio | ALTO | Focar nos 5 P0, depois 10 P1; long tail sob demanda |
| LLM-judge inconsistente | MÉDIO | Calibration Panel (Sprint 4) + auto-concordância |
| Schema drift dos 33 adapters | MÉDIO | Contract Registry + CI alerts (Sprint 3-4) |
| Complexidade do billing eval | BAIXO | Pricing é determinístico — graders puros suficientes |
| LGPD: golden sets com PII | CRÍTICO | Auto-redaction no upload + review obrigatório |
| Frontend toma tempo demais vs CLI | MÉDIO | Sprint 1 (59h) + Sprint 2 (47h) são mínimos para Gate; Sprint 3-4 são pós-Gate |
| Sprint 3 = 84h (Convention Manager migrado do Sprint 2) | MÉDIO | Pós-Gate; pode ser dividido em Sprint 3a (Dashboard+Contracts) / 3b (Conventions) se necessário |
| Confusão de nomenclatura com OODA-EVAL | BAIXO | Mapeamento documentado na Seção 10; gbr-eval usa nomes semânticos desde a migração |
| "1 caso novo no baseline/semana" (OODA-EVAL) vs CLO bottleneck | MÉDIO | Diogo é único validador até Sprint 4 (Calibration Panel); cadência realista: 2-3 por sprint |

---

## 12. Métricas de Sucesso

### Gate Fase 1 (10/Mai/2026)

- [ ] 5 P0 skills com golden sets anotados e aprovados
- [ ] >= 26 cases anotados (meta: ~5 por skill)
- [ ] Extraction field_f1 >= 95% nos 5 P0
- [ ] Classification accuracy >= 90%
- [ ] Citation linking = 100%
- [ ] Cost per journey <= R$50
- [ ] Zero PII em golden sets commitados
- [ ] Todas as 13 tasks Gate Fase 1 passando no CLI

### Post-Gate (Jun-Jul/2026)

- [ ] 10 P1 skills com golden sets
- [ ] LLM-judge com auto-concordância >= 0.90
- [ ] Cohen's kappa >= 0.75 em pelo menos 3 skills
- [ ] Contract schemas dos 5 core services registrados
- [ ] CI webhook ativo no gbr-engines
- [ ] >= 50 eval runs com trend data

### Longo Prazo (H2/2026)

- [ ] 50+ skills com golden sets
- [ ] 18/18 convention rules com tasks engineering
- [ ] 33 adapter contracts registrados
- [ ] Calibration panel com 2+ anotadores
- [ ] LLM-judge blocking em >= 3 rubrics

---

## 13. Decisões Pendentes

| Decisão | Opções | Quem decide | Quando |
|---------|--------|-------------|--------|
| Auth strategy | Sem auth / Cognito SSO / Basic auth | Diogo | Sprint 1 |
| SQLite location | No repo (.gitignore) / External path / Cloud | Diogo | Sprint 1 |
| Golden set storage | Inline DB / File system refs / Hybrid | Diogo | Sprint 1 |
| Multi-user calibration | Solo + Claude / Especialista externo / QA team | Diogo | Sprint 4 |
| Deploy | Local-only / Vercel / Docker / ECS | Diogo | Pós-Gate |
| Langfuse integration | Substitute LLM-judge tracking / Complement / Skip | Diogo | Sprint 4 |

---

## 14. Definition of Done (por item)

- [ ] Funcionalidade implementada e testável no browser
- [ ] API route com validação de input (Zod)
- [ ] DB migration aplicada
- [ ] Testes mínimos (happy path + edge case) — tempo de teste incluído na estimativa de cada task
- [ ] Dark mode funcional
- [ ] Keyboard accessible
- [ ] PII auto-redaction onde aplicável
- [ ] Export/import compatível com formato CLI
