# Layer Mapping — gbr-eval ↔ OODA-EVAL

Reference table mapping gbr-eval layers to the OODA-EVAL framework used in GarantiaBR architecture.

## Layers

| gbr-eval Layer | OODA-EVAL Equivalent | Scope | Runner | When |
|---|---|---|---|---|
| **engineering** | Observe + Orient | Lint, type-check, unit tests; Claude Code generates correct code? | `pytest` / `ruff` / `mypy` in CI; `gbr-eval run --suite tasks/engineering/` | Every commit / PR gate |
| **product** | Decide | ai-engine produces correct outputs? | `gbr-eval run --suite tasks/product/` | Pre-deploy gate |
| **operational** | — | SLAs, costs, availability (future) | `gbr-eval run --suite tasks/operational/` | Continuous (future) |
| **compliance** | — | LGPD, BACEN, audit trail, ISO 27001 (future) | `gbr-eval run --suite tasks/compliance/` | Periodic (future) |

## Migration Note

The old L0/L1/L2 numeric naming was replaced with semantic names:
- Old **L0** (static quality, lint/tests) → **engineering** layer
- Old **L1** (dev agent, Claude Code behavior) → **engineering** layer
- Old **L2** (product AI, extraction/classification) → **product** layer
- New **operational** and **compliance** layers added (future)

## Gate Criteria Mapping

| Gate Criterion | Layer | Grader(s) | Status |
|---|---|---|---|
| 1. Classification >= 90% | product | `exact_match` on `document_type` | 7 tasks defined |
| 2. Extraction >= 95% (P0) | product | `field_f1` per field | Schema ready |
| 3. Citation linking = 100% | product | `field_not_empty` on citation | Schema ready |
| 4. Evaluator detection >= 80% | product | Red team suite | NOT EVALUABLE (ai-engine lacks authenticity_flag) |
| 5. Cost <= R$50/journey | product | `numeric_range` on cost metric | Schema ready |
| 6. Audit trail = 100% | engineering/product | Schema completeness check | Schema ready |
| 7. Security P0 = Zero | engineering | SAST + manual (external) | Out of eval scope |
| 8. SLA P95 < 10 min | product | `numeric_range` on duration | Schema ready |
| 9-13 | — | Business/UX criteria | Out of eval scope |

## Tier Definitions

| Tier | Purpose | Blocking? |
|---|---|---|
| `gate` | Must pass before merge/deploy | Yes — blocks pipeline |
| `regression` | Detect score degradation vs baseline | Yes — triggers NO_GO_ABSOLUTE |
| `canary` | Early warning on new code paths | No — informative only |

## Gate Result Matrix

| Result | Meaning | Exit Code |
|---|---|---|
| `GO` | All graders pass (required + optional) | 0 |
| `CONDITIONAL_GO` | Required pass, some optional fail | 0 |
| `NO_GO` | Required grader(s) failed | 1 |
| `NO_GO_ABSOLUTE` | Regression detected vs baseline | 2 |

## Severity Levels

| Severity | Used For | Gate Impact |
|---|---|---|
| `critical` | Fields that invalidate the document (CPF, CNPJ, registration number) | Required grader failure → NO_GO |
| `high` | Fields with significant business impact (area, value, dates) | Weighted in score |
| `medium` | Supporting fields (address details, secondary names) | Weighted in score |
| `low` | Informational fields (format, encoding, metadata) | Weighted in score |
