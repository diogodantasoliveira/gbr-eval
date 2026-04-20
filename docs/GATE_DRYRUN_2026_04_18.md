# Gate Fase 1 — Dry-Run Scorecard

> **Data:** 2026-04-18 (atualizado final da sessao)
> **Run IDs:** baseline (runs/baseline_2026_04_18.json), self-eval (runs/self_eval_2026_04_18.json)
> **Resultado:** Framework PRONTO — self-eval 17/23 pass (todos com golden data = 1.000), aguardando outputs reais do ai-engine

---

## 1. Scorecard por Criterio

| # | Criterio Gate | Tasks | Graders | Status | Self-Eval | Nota |
|---|---|---|---|---|---|---|
| 1 | Classification >= 90% | 8 classification YAMLs (6 skills + 2 confusers) | exact_match on document_type | READY | 7/7 PASS (1.000) | Aguarda output de `/api/v1/classify` |
| 2 | Extraction >= 95% (P0) | 6 extraction YAMLs (5 skills + balanco placeholder) | field_f1, exact_match, numeric_range | READY | 5/5 PASS (1.000) | 25 golden sets como referencia |
| 3 | Citation linking = 100% | 6 citation YAMLs | field_not_empty on citation.* | READY | 5/5 PASS (1.000) | Valida presenca de citations por campo |
| 4 | Evaluator detection >= 80% | 0 (red_team estrutura apenas) | — | NOT EVALUABLE | — | ai-engine nao implementa deteccao de autenticidade |
| 5 | Cost <= R$50/journey | 1 cost YAML | numeric_range on cost_brl | READY | FAIL (sem dados) | Aguarda metricas de custo reais |
| 6 | Audit trail = 100% | — | Schema completeness (futuro engineering) | PARTIAL | — | Precisa de graders engineering especificos |
| 7 | Security P0 = Zero | — | SAST (fora do eval) | FORA DO ESCOPO | — | Coberto por ferramentas externas |
| 8 | SLA P95 < 10 min | 1 latency YAML | numeric_range on p95_ms <= 600000 | READY | FAIL (sem dados) | Aguarda metricas de latencia reais |
| 9-13 | Business/UX | — | — | FORA DO ESCOPO | — | Criterios manuais |

## 2. Inventario de Tasks

```
23 task YAMLs em tasks/product/:
  extraction/     6 (matricula, contrato_social, cnd, procuracao, certidao_trabalhista, balanco)
  citation/       6 (idem)
  classification/ 8 (6 skills + 2 confusers)
  cost/           1 (journey cost limit)
  latency/        1 (SLA P95)
  decision/       1 (score aprovado)
  red_team/       0 (estrutura existe, sem tasks — criterion 4 NOT EVALUABLE)
```

## 3. Inventario de Golden Sets

```
25 cases anotados (seed), 5 por skill:
  matricula/              5 cases  (seed_complete)
  contrato_social/        5 cases  (seed_complete)
  cnd/                    5 cases  (seed_complete)
  procuracao/             5 cases  (seed_complete)
  certidao_trabalhista/   5 cases  (seed_complete)
  balanco/                0 cases  (blocked_no_documents)
```

## 4. Self-Eval Completo (golden-set-aware runner)

Self-eval mode: golden set `expected_output` usado como output E referencia. Valida que o framework produz score perfeito quando output == expected.

### 4.1 Resultados por task (23 tasks)

| Task | Score | Resultado |
|------|-------|-----------|
| extraction.certidao_trabalhista.fields | 1.000 | PASS |
| extraction.cnd.fields | 1.000 | PASS |
| extraction.contrato_social.fields | 1.000 | PASS |
| extraction.procuracao.fields | 1.000 | PASS |
| extraction.matricula.cpf_proprietario | 1.000 | PASS |
| citation.certidao_trabalhista.linking | 1.000 | PASS |
| citation.cnd.linking | 1.000 | PASS |
| citation.contrato_social.linking | 1.000 | PASS |
| citation.procuracao.linking | 1.000 | PASS |
| citation.matricula.linking | 1.000 | PASS |
| classification.certidao_trabalhista | 1.000 | PASS |
| classification.cnd | 1.000 | PASS |
| classification.contrato_social | 1.000 | PASS |
| classification.procuracao | 1.000 | PASS |
| classification.matricula | 1.000 | PASS |
| classification.confuser.certidao_not_cnd | 1.000 | PASS |
| classification.confuser.iptu_not_matricula | 1.000 | PASS |
| extraction.balanco.fields | 0.000 | FAIL (no golden data) |
| citation.balanco.linking | 0.000 | FAIL (no golden data) |
| classification.balanco | 0.000 | FAIL (no golden data) |
| cost.journey.limit | 0.000 | FAIL (no real metrics) |
| decision.score.aprovado | 0.000 | FAIL (no real metrics) |
| latency.sla.p95 | 0.000 | FAIL (no real metrics) |

**Resumo: 17/23 PASS — todos os 17 tasks com golden data = score 1.000**

### 4.2 Validacao com erros injetados (pytest)

- Wrong resultado: FAIL detectado (exact_match catch)
- Missing critical field: FAIL detectado (field not found)
- Null value matching: PASS (null == null)

## 5. Bugs Corrigidos Nesta Sessao

| Bug | Impacto | Fix |
|-----|---------|-----|
| `_get_field` retornava `None` para campo ausente E campo null | exact_match falhava em `validade: null` | Sentinel `_MISSING` distingue ausencia de null |
| `numeric_range` falhava em `capital_social: null` | contrato_social case_002 falhava | null vs null = pass |
| `_MISSING` vazava para JSON details | `<object at 0x...>` no report | String "field missing" |
| Field names em extraction task YAMLs nao batiam com golden sets | cnd, procuracao, matricula falhavam | `numero_certidao`->`numero`, `data_validade`->`validade` |
| Field names em citation task YAMLs nao batiam com golden sets | cnd, contrato_social, matricula citations falhavam | `citation.numero_certidao`->`citation.numero`, `citation.data_validade`->`citation.validade`, `citation.socios_percentual`->`citation.socios`, `citation.area`->`citation.area_total` |

## 6. O que Falta para Gate Real

### Bloqueadores
1. **Outputs reais do ai-engine**: O runner precisa receber extraccoes reais (de producao ou replay) como `output` dict
2. ~~**Runner golden-set-aware**~~: COMPLETO — CLI flags `--golden-dir` e `--self-eval`, suporte a extraction, classification e citation
3. **Document hashes**: Todos os golden sets usam `sha256:PENDING_COMPUTE_FROM_PDF_doc_id_XXXXX`

### Importantes
4. **Expand golden sets**: 25 seed (5/skill) vs 100 target (20/skill)
5. **Clean-machine test**: Nenhum colega rodou ainda
6. **Regression baseline com dados reais**: Baselines atuais sao empty-output (todos FAIL) e self-eval (17/23 PASS) — baseline real requer outputs do ai-engine

### Observacoes
- O framework esta **funcionalmente completo** para Gate: graders, runner, reporter, regression, trends todos funcionam
- Golden-set-aware runner implementado: `gbr-eval run --suite tasks/product --golden-dir golden --self-eval`
- Self-eval confirma framework correto: 17/17 tasks com golden data = score 1.000
- A integracao com ai-engine e o gargalo — o eval framework avalia, mas precisa de algo para avaliar
- Criterion 4 (evaluator detection) permanece NOT EVALUABLE ate ai-engine implementar deteccao
