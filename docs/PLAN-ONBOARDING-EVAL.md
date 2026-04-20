# Plano: Eval do Onboarding PJ — Validação em Paralelo

**Data:** 2026-04-20
**Autor:** Diogo Dantas (CAIO)
**Aprovação necessária:** Bernardo Bicalho (CTO)
**Prazo proposto:** 21-24 de abril (4 dias úteis)
**Contexto:** Daily de 20/abr — time precisa de 1-2 dias para security state no onboarding. Queremos rodar eval em paralelo e comparar resultados.

---

## 1. Objetivo

Validar se o gbr-eval consegue identificar automaticamente os mesmos problemas (ou mais) que o time encontraria manualmente no fluxo de onboarding PJ, rodando **em paralelo** sem interferir no trabalho deles.

### Critérios de Sucesso
- [ ] Eval identifica >= 70% dos bugs que o time reporta manualmente
- [ ] Tempo total de setup + execução < 1 dia (vs. 2 dias manuais)
- [ ] Zero intervenção necessária do time de desenvolvimento
- [ ] Resultado reprodutível (rodar 2x = mesmo output)

### Resultado Esperado
Se funcionar: apresentar ao time como ferramenta complementar (rollout lateral).
Se não funcionar: iterar — identificar gaps, melhorar graders, repetir.

---

## 2. O que é o Fluxo de Onboarding PJ

Baseado na daily e no protótipo navegável do Atom:

```
1. Cadastro de Empresa (PJ)
   POST /api/v1/companies
   └─ CNPJ, razão social, nome fantasia, endereço, regime tributário

2. Cadastro de Filial (opcional)
   POST /api/v1/companies/{id}/branches
   └─ CNPJ filial, endereço, gerente responsável

3. Cadastro de Departamento
   POST /api/v1/departments
   └─ nome, empresa_id, filial_id (opcional), gestor

4. Cadastro de Centro de Custo
   POST /api/v1/cost-centers
   └─ código, nome, departamento_id, budget_limit

5. Cadastro de Usuário
   POST /api/v1/users
   └─ email, nome, empresa_id, departamento_id, role

6. Atribuição de Permissões
   POST /api/v1/users/{id}/permissions
   └─ role_slug, group_id, custom_overrides

7. Integração SERPRO (enriquecimento)
   POST /api/v1/integrations/serpro/cnpj-lookup
   └─ CNPJ → dados cadastrais completos

8. Audit Log (transversal)
   Toda mutação acima gera log em audit_logs
```

---

## 3. Duas Camadas de Avaliação

### 3.1 Camada Engineering (Qualidade do Código)

**Pergunta:** "O código do onboarding segue os padrões de engenharia da GarantiaBR?"

| Regra | O que verifica | Grader | Severidade |
|-------|----------------|--------|-----------|
| `tenant_isolation` | Toda query filtra por `tenant_id` | `pattern_required` + `pattern_forbidden` | CRITICAL |
| `audit_trail` | Toda mutação gera audit log | `convention_check` | CRITICAL |
| `input_validation` | Todo endpoint valida input (Pydantic/schema) | `pattern_required` | HIGH |
| `error_handling` | Nenhum `except Exception` genérico | `pattern_forbidden` | HIGH |
| `auth_enforcement` | Todo endpoint usa dependency de autenticação | `pattern_required` | CRITICAL |
| `rbac_check` | Endpoints protegidos verificam permissão | `pattern_required` | HIGH |
| `no_hardcoded_config` | Sem magic numbers ou config inline | `pattern_forbidden` | MEDIUM |
| `response_schema` | Endpoints retornam schema tipado | `pattern_required` | MEDIUM |
| `idempotency` | Operações de criação são idempotentes | `convention_check` | MEDIUM |
| `no_secrets_in_code` | Sem tokens/senhas hardcoded | `pattern_forbidden` | CRITICAL |

**Total: 10 tasks de engineering focadas no onboarding**

**Scan targets específicos:**
```yaml
# Focado nos arquivos do onboarding, não no repo inteiro
scan_target: "app/api/v1/companies/**/*.py"      # Empresa
scan_target: "app/api/v1/users/**/*.py"          # Usuários
scan_target: "app/api/v1/departments/**/*.py"    # Departamentos
scan_target: "app/api/v1/cost_centers/**/*.py"   # Centros de custo
scan_target: "app/api/v1/permissions/**/*.py"    # Permissões
```

### 3.2 Camada Product (Qualidade dos Outputs)

**Pergunta:** "Dado um input correto, o onboarding produz o output esperado?"

Esta camada requer acesso ao ambiente rodando (`atom.dev.garantiabr.com`) ou outputs gravados.

| Golden Set | Casos | O que valida |
|------------|-------|-------------|
| `onboarding_empresa_standard` | 5 | Cadastro PJ completo com dados válidos |
| `onboarding_empresa_edge` | 3 | MEI, empresa estrangeira, CNPJ inativo |
| `onboarding_empresa_confuser` | 2 | CNPJ duplicado, dados conflitantes |
| `onboarding_usuario_standard` | 5 | Criação com role válido e grupo |
| `onboarding_usuario_edge` | 3 | Email duplicado, role inexistente, sem grupo |
| `onboarding_permissao_standard` | 5 | Atribuição e verificação de acesso |
| `onboarding_permissao_edge` | 3 | Escalação de privilégio, permissão circular |
| `onboarding_fluxo_e2e` | 3 | Jornada completa ponta-a-ponta |

**Total: 29 golden cases para o onboarding**

**Graders aplicados:**
- `exact_match` — campos obrigatórios retornam valor correto
- `field_not_empty` — campos obrigatórios não são null/empty
- `numeric_range` — IDs, timestamps dentro de ranges válidos
- `field_f1` — F1 score quando há múltiplos campos retornados
- `llm_judge` (informative) — qualidade semântica da resposta de erro

---

## 4. Pré-Requisitos (o que preciso do Bicalho)

### 4.1 Acesso ao Código (BLOCKER)

| Item | Descrição | Quem resolve |
|------|-----------|-------------|
| **Git clone** | Acesso read ao repositório do Atom (onde vive o onboarding) | Bicalho → Lucas Soares |
| **Estrutura de pastas** | Confirmar paths dos endpoints de onboarding no repo | Bicalho/Israel |
| **Branch correta** | Qual branch tem o código mais recente do onboarding | Israel |

**Comando que preciso rodar:**
```bash
git clone git@github.com:GarantiaBR/<repo-atom>.git /tmp/atom-eval
uv run python -m gbr_eval.harness.runner run \
  --suite tasks/engineering/onboarding/ \
  --code-dir /tmp/atom-eval \
  --layer engineering
```

### 4.2 Acesso ao Ambiente (NICE-TO-HAVE para Camada Product)

| Item | Descrição | Quem resolve |
|------|-----------|-------------|
| **URL do ambiente** | `atom.dev.garantiabr.com` — precisa de acesso | Bicalho/Lucas |
| **Token de API** | Bearer token para chamar endpoints | Israel/Bicalho |
| **Usuário de teste** | Com permissões de admin para o tenant de teste | Israel |

> **Nota:** A Camada Product pode rodar sem acesso ao ambiente se tivermos outputs gravados (replay mode). Podemos pedir ao Israel que grave 5-10 responses e usamos como fixture.

### 4.3 Informação Estrutural

Preciso confirmar com Bicalho/Israel:

1. **Framework do backend**: FastAPI? (presumo que sim, como os outros serviços)
2. **ORM**: SQLAlchemy? Tortoise? (afeta patterns de `tenant_id`)
3. **Autenticação**: JWT via middleware? Dependency injection?
4. **Audit log**: Lib própria? Decorator? Middleware?
5. **Validação**: Pydantic models nos endpoints?
6. **Testes existentes**: Têm testes unitários? Qual cobertura?

---

## 5. Cronograma de Execução

### Dia 1 — Segunda 21/abr: Setup e Engineering Tasks

| Hora | Atividade | Dependência |
|------|-----------|-------------|
| Manhã | Clone do repo + exploração da estrutura | Acesso git |
| Manhã | Mapear endpoints do onboarding (paths, handlers) | — |
| Tarde | Criar 10 task YAMLs de engineering | Estrutura mapeada |
| Tarde | Primeira execução do eval contra o código | Tasks criadas |
| EOD | Report parcial: % de conformidade por regra | — |

**Entregável D1:** Relatório "Engineering Quality — Onboarding" com score por arquivo e regra violada.

### Dia 2 — Terça 22/abr: Refinamento e Golden Sets

| Hora | Atividade | Dependência |
|------|-----------|-------------|
| Manhã | Ajustar patterns com base nos false positives do D1 | Report D1 |
| Manhã | Criar golden sets para Product (5 standard cases) | Spec dos endpoints |
| Tarde | Gravar outputs do ambiente dev (se disponível) | Acesso HTTP |
| Tarde | Criar tasks de Product com graders determinísticos | Golden sets prontos |
| EOD | Segunda execução — comparar engineering + product | — |

**Entregável D2:** Golden sets anotados + primeira execução da camada Product.

### Dia 3 — Quarta 23/abr: Execução Completa + Edge Cases

| Hora | Atividade | Dependência |
|------|-----------|-------------|
| Manhã | Adicionar edge cases e confusers ao golden set | D2 feedback |
| Manhã | Executar eval completo (engineering + product) | — |
| Tarde | Comparar achados do eval com bugs do Israel | Lista de bugs do time |
| Tarde | Documentar discrepâncias (eval achou / não achou) | — |
| EOD | Report final: comparação eval vs. manual | — |

**Entregável D3:** Report comparativo quantificado.

### Dia 4 — Quinta 24/abr: Apresentação e Decisão

| Hora | Atividade | Dependência |
|------|-----------|-------------|
| Manhã | Preparar apresentação executiva (5 slides) | Report D3 |
| Manhã | Sessão com Bicalho — review dos resultados | — |
| Tarde | Go/No-Go: integrar no CI do repo-alvo? | Decisão C-level |
| Tarde | Se Go: configurar GitHub Action no repo | Aprovação |

**Entregável D4:** Decisão documentada + (se Go) CI configurado.

---

## 6. Exemplos Concretos de Tasks

### 6.1 Engineering Task — Tenant Isolation no Onboarding

```yaml
task_id: eng.onboarding.tenant_isolation
category: classification
component: atom-back-end
layer: engineering
tier: gate
description: "Endpoints de onboarding devem filtrar por tenant_id em toda query"

input:
  payload:
    repo: atom-back-end
    scan_target: "app/api/v1/{companies,users,departments,cost_centers}/**/*.py"

expected:
  convention: tenant_isolation_onboarding

graders:
  - type: pattern_required
    field: tenant_id_filter
    weight: 1.0
    required: true
    config:
      pattern: 'tenant_id|current_tenant|get_tenant'
      file_key: content

  - type: pattern_forbidden
    field: no_global_queries
    weight: 1.0
    required: true
    config:
      pattern: '\.all\(\)\s*$|select\(\w+\)\.where\(\s*\)'
      file_key: content

scoring_mode: binary
pass_threshold: 1.0
eval_owner: diogo.dantas
eval_cadence: per-pr
```

### 6.2 Engineering Task — Audit Trail no Onboarding

```yaml
task_id: eng.onboarding.audit_trail
category: classification
component: atom-back-end
layer: engineering
tier: gate
description: "Toda mutação em entidades de onboarding gera audit log"

input:
  payload:
    repo: atom-back-end
    scan_target: "app/api/v1/{companies,users,departments}/**/*.py"

expected:
  convention: audit_trail_onboarding

graders:
  - type: convention_check
    field: audit_conventions
    weight: 1.0
    required: true
    config:
      file_key: content
      rules:
        - pattern: "audit_log|create_audit|log_action|AuditLog|emit_audit"
          type: required
          description: "Chamada a função de audit logging"
        - pattern: "def (create|update|delete|patch).*:\\n[^}]*return.*(?!audit)"
          type: forbidden
          description: "Mutação sem audit log associado"
        - pattern: "print\\(|logging\\.debug\\(.*password|.*secret|.*token"
          type: forbidden
          description: "Dados sensíveis em logs genéricos"

scoring_mode: binary
pass_threshold: 1.0
eval_owner: diogo.dantas
eval_cadence: per-pr
```

### 6.3 Engineering Task — Input Validation

```yaml
task_id: eng.onboarding.input_validation
category: classification
component: atom-back-end
layer: engineering
tier: gate
description: "Todo endpoint de onboarding valida input com schema tipado"

input:
  payload:
    repo: atom-back-end
    scan_target: "app/api/v1/{companies,users,departments,cost_centers}/**/*.py"

expected:
  convention: input_validation_required

graders:
  - type: convention_check
    field: validation_patterns
    weight: 1.0
    required: true
    config:
      file_key: content
      rules:
        - pattern: "BaseModel|Schema|Depends\\(|Body\\(|Query\\("
          type: required
          description: "Uso de schema/validation (Pydantic ou FastAPI Depends)"
        - pattern: "request\\.json\\(\\)|request\\.body|request\\.form"
          type: forbidden
          description: "Acesso raw ao body sem validação de schema"

scoring_mode: binary
pass_threshold: 0.9
eval_owner: diogo.dantas
eval_cadence: per-pr
```

### 6.4 Product Task — Cadastro de Empresa

```yaml
task_id: prod.onboarding.company_create
category: extraction
component: onboarding
layer: product
tier: gate
description: "POST /companies cria empresa com todos os campos obrigatórios"

input:
  endpoint: /api/v1/companies
  payload:
    cnpj: "00.000.000/0001-91"
    razao_social: "EMPRESA TESTE EVAL LTDA"
    nome_fantasia: "Teste Eval"
    endereco:
      logradouro: "Rua Exemplo"
      numero: "100"
      cidade: "São Paulo"
      uf: "SP"
      cep: "01000-000"

expected:
  id_present: true
  cnpj: "00.000.000/0001-91"
  razao_social: "EMPRESA TESTE EVAL LTDA"
  status: "active"
  tenant_id_present: true
  created_at_present: true

graders:
  - type: field_not_empty
    field: id
    weight: 1.0
    required: true
    config:
      field_path: "id"

  - type: exact_match
    field: cnpj
    weight: 1.0
    required: true
    config:
      field_path: "cnpj"
      expected_value: "00.000.000/0001-91"

  - type: exact_match
    field: razao_social
    weight: 1.0
    required: true
    config:
      field_path: "razao_social"
      expected_value: "EMPRESA TESTE EVAL LTDA"

  - type: exact_match
    field: status
    weight: 0.8
    required: false
    config:
      field_path: "status"
      expected_value: "active"

  - type: field_not_empty
    field: tenant_id
    weight: 1.0
    required: true
    config:
      field_path: "tenant_id"

  - type: field_not_empty
    field: created_at
    weight: 0.5
    required: false
    config:
      field_path: "created_at"

scoring_mode: weighted
pass_threshold: 0.95
eval_owner: diogo.dantas
eval_cadence: per-pr
```

### 6.5 Product Task — Fluxo E2E (Jornada Completa)

```yaml
task_id: prod.onboarding.e2e_flow
category: decision
component: onboarding
layer: product
tier: gate
description: "Jornada completa: empresa → departamento → centro custo → usuário → permissão"

input:
  endpoint: /api/v1/onboarding/complete
  payload:
    company:
      cnpj: "00.000.000/0001-91"
      razao_social: "EMPRESA E2E EVAL LTDA"
    department:
      name: "Operações"
    cost_center:
      code: "CC-001"
      name: "Operacional"
    user:
      email: "eval-test@garantiabr.com"
      name: "Usuário Eval"
      role: "analyst"
    permissions:
      groups: ["operacoes"]

expected:
  company_created: true
  department_created: true
  cost_center_created: true
  user_created: true
  permissions_assigned: true
  audit_entries_count_min: 5
  all_entities_same_tenant: true

graders:
  - type: exact_match
    field: company_created
    weight: 1.0
    required: true
    config:
      field_path: "company_created"
      expected_value: true

  - type: exact_match
    field: all_same_tenant
    weight: 1.0
    required: true
    config:
      field_path: "all_entities_same_tenant"
      expected_value: true

  - type: numeric_range
    field: audit_count
    weight: 0.8
    required: false
    config:
      field_path: "audit_entries_count"
      min_value: 5

scoring_mode: weighted
pass_threshold: 1.0
eval_owner: diogo.dantas
eval_cadence: per-release
```

---

## 7. Comparação: Eval vs. Manual

### Como vamos medir o sucesso

| Métrica | Manual (time) | Eval (nós) |
|---------|---------------|------------|
| **Tempo** | 1-2 dias | < 4 horas (após setup) |
| **Reprodutibilidade** | Depende de quem testa | 100% determinístico |
| **Cobertura** | O que o testador lembra de testar | Todos os files/endpoints definidos |
| **Regressão** | Retesta tudo do zero | Baseline automático (delta) |
| **Rastreabilidade** | Thread no Slack / MD no repo | JSON report com run_id, timestamp, detalhes |
| **Custo marginal** | 1-2 dias por release | 0 (roda no CI em 2 min) |

### Metodologia da comparação

1. **Israel produz a lista de bugs** durante o security state (21-23/abr)
2. **Nós rodamos o eval** no mesmo código, mesmo período
3. **Na quinta-feira (24/abr):** cruzamos as duas listas

Classificação dos resultados:
- **True Positive (TP):** Eval encontrou E time encontrou → validação mútua
- **Eval-Only (EO):** Eval encontrou, time não → valor adicional do eval
- **Manual-Only (MO):** Time encontrou, eval não → gap no eval (precisamos melhorar)
- **False Positive (FP):** Eval reportou como bug, mas não é → ajustar threshold/pattern

**Meta:** TP + EO >= 70% do total de issues identificadas

---

## 8. Integração Futura no CI (se aprovado)

```yaml
# .github/workflows/onboarding-eval.yml
name: Onboarding Eval Gate

on:
  pull_request:
    paths:
      - 'app/api/v1/companies/**'
      - 'app/api/v1/users/**'
      - 'app/api/v1/departments/**'
      - 'app/api/v1/cost_centers/**'
      - 'app/api/v1/permissions/**'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install gbr-eval
        run: pip install gbr-eval  # ou git clone + uv sync
      - name: Run engineering eval
        run: |
          gbr-eval run \
            --suite tasks/engineering/onboarding/ \
            --code-dir . \
            --tier gate \
            --output-format json \
            --output-file eval-report.json
      - name: Post results on PR
        if: always()
        uses: dorny/test-reporter@v1
        with:
          name: Onboarding Eval
          path: eval-report.json
          reporter: java-junit
```

**Benefício:** Todo PR que toca código de onboarding passa pelo eval automaticamente. Sem revisão manual para padrões mecânicos. O revisor humano foca em lógica de negócio.

---

## 9. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Acesso ao repo demora | Alta | Blocker D1 | Pedir ao Bicalho hoje (domingo/segunda cedo) |
| Estrutura do repo diferente do esperado | Média | Atrasa D1 | Explorar antes de criar tasks |
| False positives excessivos | Média | Descrédito | Threshold conservador (0.8), ajuste iterativo |
| Time corrige bugs antes de compararmos | Baixa | Perde baseline | Clonar estado atual antes do security state |
| Ambiente dev indisponível | Média | Bloqueia Product layer | Priorizar Engineering (não depende de env) |

---

## 10. Decisão Necessária do Bicalho

### Resposta binária:

> "Bicalho, preciso de 3 coisas para rodar o eval no onboarding esta semana:
> 1. **Acesso read** ao repo onde vive o código de onboarding (qual repo? qual branch?)
> 2. **30 min de papo** para entender a estrutura (paths, ORM, auth pattern)
> 3. **Compromisso de não avisar o time** até termos resultado — é rollout lateral"

### Nice-to-have (pode vir depois):
- Token de API para o ambiente dev
- Acesso à lista de bugs que o Israel está montando (para comparação)

---

## 11. Artefatos Produzidos

Ao final dos 4 dias, teremos no gbr-eval:

```
tasks/engineering/onboarding/
├── tenant_isolation.yaml
├── audit_trail.yaml
├── input_validation.yaml
├── error_handling.yaml
├── auth_enforcement.yaml
├── rbac_check.yaml
├── no_hardcoded_config.yaml
├── response_schema.yaml
├── idempotency.yaml
└── no_secrets.yaml

tasks/product/onboarding/
├── company_create.yaml
├── company_edge_cases.yaml
├── user_create.yaml
├── user_edge_cases.yaml
├── permission_assign.yaml
├── permission_edge_cases.yaml
└── e2e_flow.yaml

golden/onboarding/
├── metadata.yaml
├── company_standard/
│   ├── case_001.json ... case_005.json
├── company_edge/
│   ├── case_101.json ... case_103.json
├── user_standard/
│   ├── case_001.json ... case_005.json
└── e2e/
    ├── case_001.json ... case_003.json

docs/
└── REPORT-ONBOARDING-EVAL-2026-04-24.md
```

---

## 12. Resumo Executivo (para Bicalho)

**O que:** Rodar o framework gbr-eval contra o código do onboarding PJ em paralelo ao security state do time.

**Por que:** O time precisa de 2 dias para achar bugs manualmente. Se o eval acha os mesmos bugs em 4 horas, provamos valor e podemos integrar no CI — todo PR futuro passa por validação automática.

**Como:** 10 tasks de engineering (regex patterns contra o código) + 29 golden cases de product (se tivermos acesso ao ambiente). Sem interferência no time.

**Quando:** 21-24 de abril (esta semana).

**Custo:** Zero financeiro. Meu tempo + 30 min do Bicalho + acesso read ao repo.

**Risco:** Se não funcionar, perdemos 4 dias meus (não do time). Se funcionar, ganhamos uma camada permanente de qualidade automatizada.
