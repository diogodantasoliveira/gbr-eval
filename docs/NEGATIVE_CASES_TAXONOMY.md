# Negative Golden Set Cases Taxonomy

## Overview

gbr-eval evaluates 5 P0 skills (matricula, contrato_social, cnd, procuracao, certidao_trabalhista) against positive seed cases and 15 negative cases spanning two categories: confusers (wrong document type) and edge cases (missing/incomplete fields).

## Case Numbering Convention

| Range | Category | Purpose |
|-------|----------|---------|
| 001–099 | Positive (seed) | Known-good cases; baseline extraction/classification |
| 100–199 | Confusers | Wrong document type; tests classifier rejection |
| 200–299 | Edge cases | Missing/null fields, partial data; tests robustness |
| 300–399 | Degraded | OCR quality, low resolution; *planned* |
| 400–499 | Adversarial | Tampered documents; *planned* |

## Confuser Cases (5 current)

**Purpose:** Verify classifier correctly identifies and rejects documents of similar but incorrect type.

| Case ID | Document Type | Expected System Response | CLO Status |
|---------|---------------|-------------------------|------------|
| 101 | IPTU → Matrícula | Reject as IPTU | pending |
| 102 | Certidão Casamento → CND | Reject as Certidão Casamento | pending |
| 103 | Alteração Contratual → Contrato Social | Reject as Alteração Contratual | pending |
| 104 | Substabelecimento → Procuração | Reject as Substabelecimento | pending |
| 105 | Certidão Cível → Certidão Trabalhista | Reject as Certidão Cível | pending |

**Tag filtering:** `golden_set_tags: ["confuser"]` (classification confuser tasks only)

## Edge Cases (10 current)

**Purpose:** Validate extraction handles missing/null fields and partial data gracefully.

| Skill | Case ID | Scenario | Key Missing Fields | CLO Status |
|-------|---------|----------|-------------------|------------|
| Matrícula | 201 | Onus absent | Onus, informative fields | pending |
| Matrícula | 202 | Incomplete | Multiple optional fields | pending |
| CND | 203 | Validade null | Validade, CPF/CNPJ | pending |
| CND | 204 | Partial | Critical dates absent | pending |
| Contrato Social | 205 | Capital null | Capital social, sócios | pending |
| Contrato Social | 206 | Incomplete sócios | CNPJ/CPF absent | pending |
| Procuração | 207 | Validade indefinite | Expiry, partial fields | pending |
| Procuração | 208 | Minimal | Poders absent | pending |
| Certidão Trabalhista | 209 | Positiva with processos | Partial process data | pending |
| Certidão Trabalhista | 210 | Incomplete | Critical dates absent | pending |

**Tag filtering:** `golden_set_tags: ["seed", "edge_case"]` (classification tasks); extraction tasks use `["seed"]` only until grader hardening complete.

## Tag-Based Filtering

Tasks control case inclusion via `golden_set_tags` in YAML:

| Task Type | Tags | Includes | Excludes |
|-----------|------|----------|----------|
| Citation | `["seed"]` | Positive cases only | Confusers, edge cases (incomplete citations) |
| Classification (target) | `["seed", "edge_case"]` | Positive + edge cases | Confusers |
| Classification (confuser) | `["confuser"]` | Confuser cases only | Positive, edge cases |
| Extraction | `["seed"]` | Positive cases only | Edge cases (post-grader hardening: expand to `["seed", "edge_case"]`) |

## Current vs. Target Coverage

| Category | Current | Target | Gap |
|----------|---------|--------|-----|
| Seed (positive) | 25 | 25 | — |
| Confuser | 5 | 20+ | +15 |
| Edge case | 10 | 30+ | +20 |
| Degraded | 0 | 20+ | +20 |
| Adversarial | 0 | 20+ | +20 |
| **Total** | **40** | **100+** | **+60** |

## Next Steps

1. **Phase 2 validation:** CLO reviews all 15 new cases; update `reviewed_by: "diogo.dantas"` (currently `null`)
2. **Phase 3 expansion:** Synthetic generation for confuser and edge case categories
3. **Future phases:** Degraded (OCR/resolution) and adversarial (tampering) when staging environment ready
