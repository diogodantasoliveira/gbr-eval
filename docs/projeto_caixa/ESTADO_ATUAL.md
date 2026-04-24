# Estado Atual — Projeto Caixa Econômica Federal (BPO Eval)

> **Data:** 2026-04-24 | **Owner:** Diogo Dantas (CAIO)
> **Repo:** gbr-eval | **Projeto:** `caixa` (multi-projeto)

---

## 1. Resumo Executivo

O gbr-eval agora suporta **múltiplos projetos** com isolamento de diretórios. O projeto `caixa` tem **106 task YAMLs** cobrindo os 7 serviços do BPO, **8 graders novos** especializados, e **zero golden sets** — aguardando anotação humana (CLO).

A Fase 0 (Fundação) está **100% completa**. A Fase 1 (Classificação Documental) está pronta para iniciar assim que os primeiros golden sets forem anotados.

---

## 2. O Que Está Pronto

### 2.1 Infraestrutura Multi-Projeto

| Item | Status |
|------|--------|
| Campo `project` em Task e EvalRun (default="default") | Implementado |
| CLI `--project caixa` nos comandos `run`, `trends`, `analyze` | Implementado |
| Auto-resolve de paths: `projects/caixa/tasks`, `projects/caixa/golden` | Implementado |
| Filtro por projeto em `load_tasks_from_dir()` | Implementado |
| Reporter: exibe projeto no console e CI summary | Implementado |
| Tools (`sync_frontend.py`, `generate_all_synthetic.py`): `--project` | Implementado |
| Backwards-compatible: tasks existentes (project=default) inalteradas | Verificado |
| 14 testes multi-projeto | Passando |

### 2.2 Graders (25 total)

**17 existentes (inalterados):**

| Grader | Tipo | Categoria |
|--------|------|-----------|
| `exact_match` | Determinístico | Geral |
| `numeric_range` | Determinístico | Geral |
| `numeric_tolerance` | Determinístico | Geral |
| `regex_match` | Determinístico | Geral |
| `field_not_empty` | Determinístico | Geral |
| `set_membership` | Determinístico | Geral |
| `string_contains` | Determinístico | Geral |
| `field_f1` | Determinístico | Geral |
| `pattern_required` | Determinístico | Engineering |
| `pattern_forbidden` | Determinístico | Engineering |
| `convention_check` | Determinístico | Engineering |
| `decimal_usage` | Determinístico | Engineering |
| `scope_check` | Determinístico | Engineering |
| `subprocess` | Subprocess | Engineering |
| `haiku_triage` | LLM (Haiku) | Triage |
| `llm_judge` | LLM (Sonnet) | Product |
| `engineering_judge` | LLM (Opus) | Engineering |

**8 novos (Fase 0 Caixa):**

| Grader | Tipo | Arquivo | Propósito |
|--------|------|---------|-----------|
| `checklist_completeness` | Determinístico | `caixa.py` | 100% itens do checklist avaliados |
| `multi_step_calculation` | Determinístico | `caixa.py` | Valida cada etapa de cálculo composto |
| `cross_document_match` | Determinístico | `caixa.py` | Campo doc A == campo doc B |
| `array_sum_match` | Determinístico | `caixa.py` | Soma de array == total esperado |
| `fuzzy_name_match` | Determinístico | `caixa.py` | Jaro-Winkler >= threshold (sem deps externas) |
| `workflow_steps` | Determinístico | `workflow.py` | Etapas executadas na ordem correta |
| `classification_accuracy` | Agregado | `workflow.py` | Acurácia global sobre predictions |
| `semantic_interpretation` | LLM (Sonnet) | `semantic_judge.py` | Interpretação semântica de texto jurídico |

### 2.3 Tasks Caixa (106 total)

| Serviço | Tasks | Categorias |
|---------|-------|------------|
| **Classificação Documental** | 47 | 32 tipos documentais + 15 confusers |
| **Regras Negociais** | 15 | 7 simples + 5 compostas + 3 consolidação |
| **Tratamento de Arquivo** | 10 | 10 operações (deskew, rotação, mosaico...) |
| **Extração de Dados** | 10 | 10 doc types (RG, CNH, matrícula...) |
| **Validação de Autenticidade** | 10 | score, biometria, red team |
| **Jornadas Automatizadas** | 8 | 4 jornadas + 4 SLA/disponibilidade |
| **Consulta a Bases Externas** | 6 | CPF, CNPJ, NF-e, RI, Junta, DNF |

Todas com `project: caixa`, `layer: product`, `tier: gate`.

### 2.4 Testes

| Métrica | Valor |
|---------|-------|
| Testes totais | 827 |
| Passando | 826 |
| Skipped | 1 (semantic_interpretation — requer API key) |
| Falhando | 0 |
| Testes dos novos graders | 55 |
| Testes multi-projeto | 14 |

### 2.5 Documentação

| Documento | Conteúdo |
|-----------|----------|
| `ANALISE_EDITAL_BPO_CAIXA.md` | Análise completa do edital |
| `PLANO_DESENVOLVIMENTO_EVAL_FIRST.md` | Plano de 17 semanas, 9 fases |
| `PLANO_MULTI_PROJETO.md` | Arquitetura multi-projeto |
| 7× `SERVICO_*.md` | Requisitos detalhados por serviço |
| `ESTADO_ATUAL.md` | Este documento |

---

## 3. O Que Falta (por fase)

### Fase 0 — Fundação (COMPLETA)

- [x] 8 graders novos implementados e testados
- [x] Estrutura `projects/caixa/` criada
- [x] 106 tasks YAML escritas
- [x] Multi-projeto no harness (CLI, runner, reporter)
- [ ] ~~Schemas JSON de contrato por serviço~~ (adiado — schemas dependem da API real)

### Fase 1 — Classificação Documental (PRÓXIMA)

| Item | Status | Bloqueador |
|------|--------|-----------|
| 47 tasks (32 tipos + 15 confusers) | Pronto | — |
| Golden sets P0 (RG, CNH, Selfie, Residência) — ~36 cases | **Pendente** | Documentos reais anonimizados |
| Golden sets P1 (Holerite, Extrato, Certidão EC, IRPF, Contrato Hab.) — ~35 cases | **Pendente** | Documentos reais anonimizados |
| Golden sets P2 (23 tipos restantes) — ~90 cases | **Pendente** | Documentos reais anonimizados |
| Golden sets confusers — ~30 cases | **Pendente** | Documentos reais anonimizados |
| Gate: `classification_accuracy` >= 90% sobre golden set completo | **Pendente** | Golden sets |
| Baseline run (score 0%) | **Pendente** | Golden sets |

### Fase 2 — Extração de Dados

| Item | Status | Bloqueador |
|------|--------|-----------|
| 10 tasks de extração | Pronto | — |
| Golden sets novos — ~40 cases (RG, CNH, Holerite, IRPF, Residência) | **Pendente** | Documentos reais |
| Expandir golden sets existentes (matrícula +cadeia dominial, contrato social +NIRE) | **Pendente** | CLO |
| Gate: field-level accuracy >= 95% | **Pendente** | Golden sets |

### Fase 3 — Validação de Autenticidade

| Item | Status | Bloqueador |
|------|--------|-----------|
| 10 tasks de autenticidade | Pronto | — |
| Golden sets adversariais — 25 cases | **Pendente** | Documentos + fraudes fabricadas |
| Desbloquear `golden/red_team/` | **Pendente** | Implementar `authenticity_flag` no ai-engine |
| Gate: detection rate >= 80% | **Pendente** | Golden sets + red team |

### Fase 4 — Regras Negociais

| Item | Status | Bloqueador |
|------|--------|-----------|
| 15 tasks (7 simples + 5 compostas + 3 consolidação) | Pronto | — |
| Golden sets regras simples — ~15 cases | **Pendente** | Casos de teste |
| Golden sets regras compostas — ~25 cases | **Pendente** | **Especialista jurídico** (ônus, poderes) |
| Gate: simples >= 99%, compostas >= 95% | **Pendente** | Golden sets |

### Fase 5 — Consulta a Bases Externas

| Item | Status | Bloqueador |
|------|--------|-----------|
| 6 tasks | Pronto | — |
| Golden sets — ~20 cases | **Pendente** | Respostas de API anonimizadas |
| Gate: taxa de sucesso >= 95% | **Pendente** | Golden sets |

### Fase 6 — Tratamento de Arquivo Digital

| Item | Status | Bloqueador |
|------|--------|-----------|
| 10 tasks | Pronto | — |
| Golden sets — ~14 cenários | **Pendente** | Metadados de resultado (JSON) |
| Gate: acerto >= 95% (deskew, mosaico, orientação) | **Pendente** | Golden sets |

### Fase 7 — Jornadas End-to-End

| Item | Status | Bloqueador |
|------|--------|-----------|
| 8 tasks (4 jornadas + 4 SLA) | Pronto | — |
| Golden sets de jornada completa — ~8 cases multi-documento | **Pendente** | Todas as fases anteriores |
| Gate: SLA 1h/18h/24h, disponibilidade 99,5% | **Pendente** | Pipeline funcional |

### Fase 8 — Operational + Compliance

| Item | Status | Bloqueador |
|------|--------|-----------|
| Tasks operational (latência, throughput, custo) — ~15 | **Pendente** | Definição de métricas |
| Tasks compliance (LGPD, BACEN, audit) — ~10 | **Pendente** | Requisitos de compliance |

---

## 4. Golden Sets — Situação

| Projeto | Golden Cases | Status |
|---------|-------------|--------|
| default (gbr-engines) | 40 | 5 doc types seed, anotados |
| caixa | **0** | Aguardando documentos reais anonimizados |

### Próximos golden sets a anotar (prioridade)

1. **RG** — 8-10 cases (53% do volume, alta frequência)
2. **CNH** — 8-10 cases (alta frequência)
3. **Selfie** — 5 cases (biometria)
4. **Comprovante Residência** — 5 cases (alta frequência)
5. **Holerite** — 6-8 cases (confusão com extrato)
6. **Matrícula** — expandir 8 existentes com campos Caixa
7. **Contrato Social** — expandir 8 existentes com NIRE/cláusulas

**Total estimado:** ~247 golden cases para cobertura completa do edital.

---

## 5. Dependências Bloqueantes

| # | Dependência | O que bloqueia | Severidade | Responsável |
|---|-----------|---------------|-----------|------------|
| 1 | **Documentos reais anonimizados** (27 tipos sem cobertura) | Fases 1-2 | CRÍTICA | Operações GBR |
| 2 | **Schemas de API** dos 7 serviços (request/response JSON) | Contracts + endpoint tests | CRÍTICA | Engineering |
| 3 | **Authenticity flag no ai-engine** | Fase 3 (red_team) | ALTA | Engineering |
| 4 | **Especialista jurídico** para anotação matrícula/contrato | Fase 4 (regras compostas) | ALTA | Jurídico GBR |
| 5 | **Thresholds confirmados pela CAIXA** (fuzzy match, score faixas) | Config final | ALTA | Produto |
| 6 | **Tipologia final** (32 tipos? subtipos? frente/verso?) | Fase 1 (classificação) | MÉDIA | Produto |

---

## 6. Comandos Úteis

```bash
# Rodar todas as tasks do projeto Caixa
uv run gbr-eval run --project caixa --suite projects/caixa/tasks/product/

# Rodar com golden sets (quando existirem)
uv run gbr-eval run --project caixa --golden-dir projects/caixa/golden/ --self-eval

# Rodar apenas classificação
uv run gbr-eval run --project caixa --suite projects/caixa/tasks/product/classificacao/

# Trends do projeto Caixa
uv run gbr-eval trends --project caixa

# Análise do projeto Caixa
uv run gbr-eval analyze --project caixa

# Testes
uv run pytest                          # todos (827)
uv run pytest tests/graders/test_caixa_graders.py  # graders novos (55)
uv run pytest tests/harness/test_multi_project.py  # multi-projeto (14)
```

---

## 7. Estrutura de Diretórios

```
projects/caixa/
├── project.yaml                    # Metadata: 7 serviços, 32 doc types
├── tasks/
│   └── product/
│       ├── tratamento/             # 10 tasks
│       ├── classificacao/          # 32 tasks + confusers/15 tasks
│       ├── extracao/               # 10 tasks
│       ├── autenticidade/          # 10 tasks
│       ├── regras/                 # 15 tasks
│       ├── consulta/               # 6 tasks
│       └── jornada/                # 8 tasks
├── golden/                         # VAZIO — aguardando anotação CLO
└── runs/                           # VAZIO — aguardando execuções
```

---

## 8. Cronograma Estimado

```
██████████ Fase 0 — Fundação                    COMPLETA (2026-04-24)
░░░░░░░░░░ Fase 1 — Classificação               Bloqueada (golden sets)
░░░░░░░░░░ Fase 2 — Extração                    Bloqueada (golden sets)
░░░░░░░░░░ Fase 3 — Autenticidade               Bloqueada (authenticity_flag)
░░░░░░░░░░ Fase 4 — Regras Negociais            Bloqueada (especialista jurídico)
░░░░░░░░░░ Fase 5 — Consulta Bases              Bloqueada (golden sets)
░░░░░░░░░░ Fase 6 — Tratamento Arquivo          Bloqueada (golden sets)
░░░░░░░░░░ Fase 7 — Jornadas E2E                Bloqueada (fases anteriores)
░░░░░░░░░░ Fase 8 — Operational + Compliance    Futuro
```

**Desbloqueador principal:** documentos reais anonimizados para criação de golden sets.

---

## 9. Métricas do Framework

| Métrica | Valor |
|---------|-------|
| Tasks totais (todos os projetos) | 354 (248 default + 106 caixa) |
| Graders registrados | 25 |
| Golden cases (default) | 40 |
| Golden cases (caixa) | 0 |
| Testes do framework | 827 |
| Cobertura de serviços Caixa | 7/7 (100%) |
| Cobertura de doc types Caixa | 32/32 (100%) |
| Confusers definidos | 15 pares |
