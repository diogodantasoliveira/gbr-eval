# PLAN: Engineering Quality Layer — Gaps & Implementation

> Status: **Pronto para execução**
> Criado: 2026-04-20
> Owner: Diogo Dantas (CAIO)

## Diagnóstico

A camada de Engineering Quality existe no esqueleto mas está incompleta. O framework (graders, code_loader, CI pipeline) está sólido. O que falta é **cobertura**, **integração frontend ↔ YAML**, e **contract testing real**.

### Estado Atual

| Dimensão | Status | Detalhe |
|----------|--------|---------|
| Graders Engineering | ✅ Completo | 3 tipos (pattern_required, pattern_forbidden, convention_check) com ReDoS guard |
| Code Loader | ✅ Completo | Path traversal protection, glob matching, size limits |
| CI Pipeline | ✅ Completo | 2 stages (quality + eval-gate), coverage ≥ 80% |
| Convention Rules DB | ✅ 18 regras | 6 categorias, 4 severidades, mix regex/llm_judge/ast |
| Frontend Conventions | ✅ 5 páginas | List, detail, edit, new, coverage matrix |
| Task YAMLs | ⚠️ Parcial | 8 tasks em 3 repos; **2 repos vazios** (garantia_ia, notifier) |
| Tasks no Frontend DB | ❌ Zero | `sync_frontend.py` só sincroniza `tasks/product/`, não `tasks/engineering/` |
| Contract Schemas | ❌ Mínimo | 1 schema sample; 5 repos alvo sem snapshots reais |
| Convention → Task Pipeline | ❌ Ausente | Regras existem no DB mas não geram tasks automaticamente |
| `/conventions/[id]` | ✅ Corrigido | Era 500 — `PatternEditor` passava event handlers de server → client component |

### Repos sem Tasks

| Repo | Regras esperadas (CLAUDE.md) | Tasks existentes |
|------|------------------------------|------------------|
| **garantia_ia** | prompt versionado, PII sanitizada, output schema, cost tracking | 0 |
| **notifier** | template aprovado, idempotência, LGPD opt-out, rate limiting | 0 |

### Repos com cobertura parcial

| Repo | Tasks existentes | Regras faltando |
|------|-----------------|-----------------|
| **atom-back-end** | 3 (audit_log, rbac, tenant_id) | sensitive data filtering |
| **engine-billing** | 2 (decimal, idempotency) | audit trail, reconciliation |
| **engine-integracao** | 3 (timeout, credentials, retry) | circuit breaker, credential vault |

---

## Implementação — 6 Sprints

### Sprint 1: Cobertura de Tasks — Repos Vazios
**Prioridade:** CRÍTICA | **Esforço:** 2h | **Dependências:** nenhuma

#### 1.1 — garantia_ia (4 tasks)

| Task ID | Grader Type | Pattern/Config | Descrição |
|---------|------------|----------------|-----------|
| `eng.ia.prompt_versioned` | pattern_required | `prompt_version\|@versioned_prompt\|PROMPT_V\d+` | Todo prompt deve ter versão explícita |
| `eng.ia.pii_sanitized` | pattern_required | `sanitize_pii\|redact_pii\|mask_pii\|_sanitize_pii_str` | Sanitização de PII antes de enviar ao modelo |
| `eng.ia.output_schema` | pattern_required | `BaseModel\|TypedDict\|@validate_output\|response_model=` | Output deve ter schema Pydantic/TypedDict |
| `eng.ia.cost_tracking` | pattern_required | `usage\|token_count\|cost_usd\|track_cost\|log_cost` | Tracking de custo por chamada |

#### 1.2 — notifier (4 tasks)

| Task ID | Grader Type | Pattern/Config | Descrição |
|---------|------------|----------------|-----------|
| `eng.notifier.template_approved` | pattern_required | `template_id\|approved_template\|get_template` | Usar templates aprovados, não texto inline |
| `eng.notifier.idempotent_send` | pattern_required | `idempotency_key\|dedup_key\|message_id.*unique` | Envio idempotente |
| `eng.notifier.lgpd_optout` | pattern_required | `opt_out\|consent_check\|notification_preference\|unsubscribe` | Respeitar opt-out LGPD |
| `eng.notifier.rate_limit` | pattern_required | `rate_limit\|throttle\|RateLimiter\|cooldown` | Rate limiting em envios |

**Entregáveis:**
- [ ] 4 YAMLs em `tasks/engineering/garantia-ia/`
- [ ] 4 YAMLs em `tasks/engineering/notifier/`
- [ ] Rodar `uv run pytest` — todos passam

---

### Sprint 2: Expandir Cobertura — Repos Existentes
**Prioridade:** ALTA | **Esforço:** 1.5h | **Dependências:** nenhuma

#### 2.1 — atom-back-end (+1 task)

| Task ID | Grader Type | Config | Descrição |
|---------|------------|--------|-----------|
| `eng.atom.sensitive_data_filter` | pattern_forbidden | `\.password\b\|\.secret\b\|\.api_key\b` em responses | Dados sensíveis não podem vazar em responses |

#### 2.2 — engine-billing (+2 tasks)

| Task ID | Grader Type | Config | Descrição |
|---------|------------|--------|-----------|
| `eng.billing.audit_trail` | convention_check | required: `audit_log\|create_audit`, forbidden: `\.commit\(\)(?!.*audit)` | Toda operação financeira com audit trail |
| `eng.billing.reconciliation_pair` | pattern_required | `reconcile\|reconciliation\|ReconciliationService` | Todo débito deve ter reconciliação par |

#### 2.3 — engine-integracao (+2 tasks)

| Task ID | Grader Type | Config | Descrição |
|---------|------------|--------|-----------|
| `eng.integracao.circuit_breaker` | pattern_required | `CircuitBreaker\|circuit_breaker\|@circuit\|pybreaker` | Circuit breaker em chamadas externas |
| `eng.integracao.credential_vault` | pattern_forbidden | `(api_key\|password\|secret\|token)\s*=\s*["'][^"']{8,}` em config files | Credenciais devem vir de vault, não de configs |

**Entregáveis:**
- [ ] 5 novos YAMLs distribuídos nos 3 repos existentes
- [ ] Total após sprint: 13 tasks (de 8 → 13)

---

### Sprint 3: Sync Frontend ↔ Engineering Tasks
**Prioridade:** ALTA | **Esforço:** 3h | **Dependências:** Sprint 1-2

O `sync_frontend.py` atual só sincroniza `tasks/product/`. As 13+ engineering tasks existem como YAML mas o frontend DB tem 0 engineering tasks. A coverage matrix fica vazia.

#### 3.1 — Estender `sync_frontend.py`

```
sync_engineering_tasks():
    para cada YAML em tasks/engineering/**/*.yaml:
        parse YAML → POST /api/tasks (upsert por task_id)
        para cada grader no YAML → POST /api/tasks/{id}/graders
```

#### 3.2 — API upsert para tasks

A API `POST /api/tasks` atual cria novo com UUID. Precisa de lógica de upsert:
- Se `task_id` já existe → UPDATE campos
- Se não existe → INSERT
- Retorna `{ id, created: boolean }`

#### 3.3 — Coverage matrix linkage

A coverage matrix faz match por `task.task_id.includes(rule.name)`. Verificar que os task_ids dos YAMLs contêm os nomes das convention rules correspondentes, ou criar linkage explícito via `convention_rule_id` no task.

**Entregáveis:**
- [ ] `sync_frontend.py` estendido com `sync_engineering_tasks()`
- [ ] Upsert endpoint em `/api/tasks`
- [ ] 13+ tasks visíveis no frontend após sync
- [ ] Coverage matrix mostra links corretos

---

### Sprint 4: Convention Rules → Task Generation Pipeline
**Prioridade:** MÉDIA | **Esforço:** 4h | **Dependências:** Sprint 3

Hoje: convention rules vivem no DB, tasks são YAMLs manuais. A coverage matrix mostra o gap mas não resolve.

#### 4.1 — Gerador de task YAML a partir de convention rule

Para cada convention rule com `detection_type=regex`:
```python
def rule_to_task(rule, repo, scan_target) -> TaskYAML:
    grader_type = "pattern_required" if rule implica presença else "pattern_forbidden"
    return TaskYAML(
        task_id=f"eng.{repo_slug}.{rule.name}",
        category="classification",
        component=repo,
        layer="engineering",
        tier="gate",
        graders=[{
            type: grader_type,
            config: { pattern: rule.detection_pattern, file_key: "content" }
        }],
        ...
    )
```

#### 4.2 — Frontend: "Generate Task" button no `/conventions/[id]`

Já existe o botão placeholder ("Generate Task" no Linked Tasks vazio). Implementar:
1. Click → abre modal com repo selector + scan_target input
2. Preview do YAML gerado
3. "Create" → POST /api/tasks + link convention_rule_id

#### 4.3 — Batch generation na coverage matrix

Na página `/conventions/coverage`:
- Checkbox em regras sem task
- "Generate Selected" → gera todas de uma vez
- Download como ZIP de YAMLs ou criação direta no DB

**Entregáveis:**
- [ ] `tools/generate_task_from_rule.py` (CLI)
- [ ] Frontend modal em `/conventions/[id]`
- [ ] Batch generation em `/conventions/coverage`

---

### Sprint 5: Contract Schema Capture
**Prioridade:** MÉDIA | **Esforço:** 3h | **Dependências:** nenhuma (parallelizable)

Hoje: 1 schema sample em `contracts/schemas/`. O CLAUDE.md define contract testing como invariante (#3) mas a implementação está vazia.

#### 5.1 — Schema snapshots para os 5 repos alvo

| Repo | Schema Source | Snapshot |
|------|-------------|----------|
| engine-integracao | OpenAPI spec (`/docs`) | `contracts/schemas/engine_integracao_openapi.json` |
| garantia_ia | Pydantic export | `contracts/schemas/garantia_ia_models.json` |
| notifier | Event schemas | `contracts/schemas/notifier_events.json` |
| engine-billing | OpenAPI spec | `contracts/schemas/engine_billing_openapi.json` |
| atom-back-end | OpenAPI spec | `contracts/schemas/atom_backend_openapi.json` |

#### 5.2 — Import via Frontend

Frontend já tem `/contracts` module. Precisamos:
- [ ] OpenAPI import endpoint: `POST /api/contracts/import-openapi` (aceita JSON, extrai schemas)
- [ ] Diff viewer entre versão anterior e nova (drift detection)
- [ ] `tools/capture_schemas.py` — script que faz GET no `/openapi.json` de cada serviço e salva snapshot

#### 5.3 — CI drift detection

No `ci.yml`, adicionar step:
```yaml
- name: Contract drift check
  run: uv run python tools/check_contract_drift.py
```
Compara schemas em `contracts/schemas/` com os endpoints reais (se disponíveis) ou com a versão commitada anterior.

**Entregáveis:**
- [ ] 5 schema snapshots reais (ou templates se repos não acessíveis)
- [ ] `tools/capture_schemas.py`
- [ ] `tools/check_contract_drift.py`
- [ ] Frontend import/diff funcional

---

### Sprint 6: Documentação & Polish
**Prioridade:** BAIXA | **Esforço:** 1.5h | **Dependências:** Sprints 1-5

#### 6.1 — Engineering Eval Guide

`docs/ENGINEERING-EVAL-GUIDE.md`:
- Como adicionar uma convention rule
- Como gerar tasks a partir de regras
- Como rodar engineering eval localmente
- Como interpretar resultados no frontend

#### 6.2 — Fix tenant_id_filter regex

O task `eng.atom.tenant_id_filter` usa pattern `tenant_id` simples — vai dar match em qualquer mention, não verifica se está em WHERE clause. Refinar:
```yaml
pattern: "\.filter\(.*tenant_id|\.where\(.*tenant_id|tenant_id\s*="
```

#### 6.3 — Convention rules para detection_type=llm_judge

7 das 18 regras usam `llm_judge` como detection_type mas os engineering graders são todos regex-based. Duas opções:
- **Opção A:** Converter para regex onde possível (curl_before_done, correct_cd_before_command)
- **Opção B:** Criar pipeline que usa `llm_judge` grader para avaliar essas regras (mais preciso, mais caro)

Recomendação: **A** para regras simples, **B** apenas para `no_hardcoded_business_data` e `provider_action_slug` que realmente precisam de semântica.

#### 6.4 — Atualizar CLAUDE.md

- Seção "5 repos alvo" → atualizar com status real de tasks
- Seção "Code Safety" → middleware agora fail-open sem ADMIN_API_TOKEN (documentar)

**Entregáveis:**
- [ ] `docs/ENGINEERING-EVAL-GUIDE.md`
- [ ] tenant_id_filter regex refinado
- [ ] 2-3 llm_judge rules convertidas para regex
- [ ] CLAUDE.md atualizado

---

## Métricas de Sucesso

| Métrica | Antes | Depois | Meta |
|---------|-------|--------|------|
| Engineering tasks | 8 | 21+ | ≥ 20 |
| Repos cobertos | 3/5 | 5/5 | 100% |
| Tasks no frontend DB | 0 | 21+ | Sync completo |
| Contract schemas | 1 sample | 5+ reais | 1 por repo |
| Convention rules com task | ~4/18 | 18/18 | 100% |
| Coverage matrix preenchida | ❌ | ✅ | Funcional |

## Ordem de Execução Recomendada

```
Sprint 1 ─── Sprint 2 ───┐
                          ├── Sprint 3 ── Sprint 4
Sprint 5 ────────────────┘
                Sprint 6 (qualquer momento após Sprint 1-2)
```

Sprints 1, 2 e 5 são independentes e podem ser executados em paralelo.
Sprint 3 depende de 1+2 (precisa das tasks criadas).
Sprint 4 depende de 3 (precisa do sync funcionando).
Sprint 6 pode começar assim que 1+2 estiverem prontos.

## Bugs Corrigidos nesta análise

| Bug | Causa | Fix |
|-----|-------|-----|
| `/conventions/[id]` retornava 500 | `PatternEditor` (client component) recebia arrow functions de server component — proibido no Next.js 16 | `onPositiveChange`/`onNegativeChange` agora opcionais com default no-op interno |
