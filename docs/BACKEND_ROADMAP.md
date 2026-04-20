# gbr-eval Backend (CLI/Harness) — Roadmap Completo

> **Owner:** Diogo Dantas (CAIO)
> **Criado:** 2026-04-18
> **Status:** Draft — aguardando aprovação
> **Deadline externa:** Gate Fase 1 (Pine) ~10/Mai/2026
> **Referências:** [FRONTEND_ROADMAP.md](FRONTEND_ROADMAP.md) | [OODA-EVAL analysis]

---

## 1. Propósito

Este roadmap cobre todo o trabalho no **CLI e harness Python** do gbr-eval — o motor que executa tarefas de avaliação, compara resultados, e produz relatórios. O frontend consome e produz artefatos para este backend; este documento é o complemento do `FRONTEND_ROADMAP.md`.

### O que já existe (baseline)

```
src/gbr_eval/
├── graders/
│   ├── base.py           ✅ Registry + interface Grader
│   ├── deterministic.py   ✅ exact_match, numeric_range, regex_match, field_not_empty,
│   │                         set_membership, string_contains
│   ├── field_f1.py        ✅ F1 por campo com fuzzy matching + list comparison
│   └── model_judge.py     ✅ LLM-as-judge com PII sanitization + prompt injection defense
├── harness/
│   ├── models.py          ✅ Task, GraderResult, EvalRun, Layer, Tier, Category, ScoringMode
│   ├── runner.py          ✅ load_task, run_task, run_suite, _compute_score, CLI (Click)
│   └── reporter.py        ✅ console_report, json_report, junit_xml_report, ci_summary
├── calibration/
│   └── iaa.py             ✅ Cohen's kappa
└── contracts/
    └── validator.py       ✅ JSON Schema validation (ContractResult)
```

**Quality gates atuais:** 160 tests, 93% coverage, ruff clean, mypy clean.

---

## 2. Adições do OODA-EVAL — Mapeamento para Backend

| Conceito OODA-EVAL | Impacto no Backend | Prioridade | Sprint |
|---------------------|--------------------|------------|--------|
| Regression Delta Analysis | `compare_runs()` + CLI `--baseline-run` | **MUST-HAVE** | B1 |
| Signal Severity | `severity` field em `GraderResult` | ALTA | B1 |
| Gate Matrix (4 níveis) | `gate_result` em `EvalRun` + lógica de classificação | ALTA | B1 |
| Golden Set Tags | Tags no formato de export JSON | MÉDIA | B1 |
| EVAL First Validation | Validar campos obrigatórios antes de ativar task | MÉDIA | B2 |
| Trend Detection | `detect_trends()` utility | MÉDIA | B2 |
| Post-mortem Format | Schema no JSON report | BAIXA | B2 |
| Layer Mapping Doc | Documentação, não código | BAIXA | B1 |

---

## 3. Módulos do Backend

### Módulo B1: Regression Delta Analysis

**Prioridade: MUST-HAVE para Gate Fase 1**

Sem regression delta, iterações em prompts/skills são cegas — um ajuste que melhora matrícula pode quebrar contrato_social sem que ninguém perceba até comparar JSONs manualmente.

#### Novo arquivo: `src/gbr_eval/harness/regression.py`

```python
@dataclass
class RegressionDelta:
    baseline_run_id: str
    current_run_id: str
    newly_failing: list[str]      # task_ids que passavam e agora falham
    newly_passing: list[str]      # task_ids que falhavam e agora passam
    score_deltas: dict[str, float] # task_id → (current_score - baseline_score)
    stable_pass: list[str]        # task_ids que continuam passando
    stable_fail: list[str]        # task_ids que continuam falhando
    overall_delta: float          # current_overall - baseline_overall
    has_regressions: bool         # len(newly_failing) > 0
    gate_result: GateResult       # GO | CONDITIONAL_GO | NO_GO | NO_GO_ABSOLUTE
```

#### Funções

| Função | Assinatura | Descrição |
|--------|-----------|-----------|
| `compare_runs` | `(baseline: EvalRun, current: EvalRun) -> RegressionDelta` | Compara dois runs task-a-task |
| `load_baseline` | `(path: Path) -> EvalRun` | Carrega run anterior de JSON |
| `classify_gate` | `(run: EvalRun, delta: RegressionDelta \| None) -> GateResult` | Determina GO/NO-GO (canônico em regression.py; runner.py importa) |

#### Lógica do Gate Matrix

```
if delta.has_regressions:
    return NO_GO_ABSOLUTE  # Regressão = prioridade máxima

if all required graders pass AND overall >= pass_threshold:
    if all optional graders pass:
        return GO
    else:
        return CONDITIONAL_GO  # Optional abaixo, flag + issue

if any required grader fails:
    return NO_GO
```

#### CLI Enhancement

```bash
# Comparar contra baseline
gbr-eval run --suite tasks/ --baseline-run results/last_run.json

# Output inclui seção de regression delta
# Exit codes canônicos (ver Seção 7):
#   0 = GO ou CONDITIONAL_GO (CI pipeline continua)
#   1 = NO_GO (CI pipeline falha)
#   2 = NO_GO_ABSOLUTE (regressão detectada)
```

#### Testes necessários

| Test | Cenário |
|------|---------|
| `test_no_regressions_returns_go` | Baseline e current idênticos |
| `test_newly_failing_detected` | Task que passava agora falha |
| `test_newly_passing_detected` | Task que falhava agora passa |
| `test_score_delta_computed` | Scores diferentes entre runs |
| `test_no_go_absolute_on_regression` | Qualquer newly_failing → NO_GO_ABSOLUTE |
| `test_conditional_go_optional_failure` | Required passam, optional falham |
| `test_empty_baseline_no_regressions` | Primeiro run sem baseline |
| `test_mismatched_tasks_handled` | Tasks adicionadas/removidas entre runs |
| `test_renamed_task_not_false_regression` | Task renomeada aparece como nova, não como regressão |

#### Constraint: `task_id` estabilidade

`compare_runs()` usa `task_id` como chave de matching. Se uma task é **renomeada** entre runs, ela aparece como 1 "newly failing" + 1 "newly passing" — falso NO_GO_ABSOLUTE. 

**Regras:**
- Tasks presentes no current mas ausentes no baseline são classificadas como `new_task` (NÃO `newly_passing`)
- Tasks presentes no baseline mas ausentes no current são classificadas como `removed_task` (NÃO `newly_failing`)
- Apenas tasks presentes em **ambos** os runs participam da regression delta
- Task_id renames exigem novo baseline (`--baseline-run` com o run mais recente)

Adicionar campos ao `RegressionDelta`:
```python
    new_tasks: list[str]       # task_ids no current mas não no baseline
    removed_tasks: list[str]   # task_ids no baseline mas não no current
```

---

### Módulo B2: Signal Severity

**Prioridade: ALTA**

Nem toda falha tem o mesmo peso. Um CPF errado em matrícula (CRITICAL) é diferente de um campo informativo ausente (LOW).

#### Mudança em `src/gbr_eval/harness/models.py`

```python
class Severity(StrEnum):
    CRITICAL = "critical"   # Impacto em decisão do cliente
    HIGH = "high"           # Erro material, mas sem decisão tomada
    MEDIUM = "medium"       # Abaixo do alvo mas acima do mínimo
    LOW = "low"             # Informativo, não bloqueia
```

Adicionar `severity` como campo **opcional** em `GraderResult`:

```python
class GraderResult(BaseModel):
    # ... campos existentes ...
    severity: Severity | None = None  # derivado de skill_fields.criticality quando disponível
```

#### Derivação de severity — duas fontes

**Fonte 1 (CLI standalone):** `severity` especificado diretamente no `config` do grader no YAML da task:

```yaml
graders:
  - type: exact_match
    field: cpf_proprietario
    weight: 3.0
    required: true
    config:
      severity: critical  # ← fallback direto no YAML
```

O CLI lê `spec.config.get("severity")` e aplica ao `GraderResult`. Isso mantém o CLI **self-contained** — sem dependência do frontend DB.

**Fonte 2 (Frontend export):** Quando o frontend exporta tasks via Task Builder, ele injeta `severity` no `config` de cada grader baseado em `skill_fields.criticality`:

| Field Criticality | Grader Severity injetado |
|-------------------|--------------------------|
| CRITICAL (w:3) | `critical` |
| IMPORTANT (w:2) | `high` |
| INFORMATIVE (w:1) | `medium` |
| Sem mapeamento | Não injeta (fica `None`) |

**Prioridade:** `config.severity` > derivação automática > `None`.

#### Mudança no reporter

`console_report` e `ci_summary` agrupam falhas por severity quando disponível:

```
CRITICAL (2 failures):
  ✗ [cpf_proprietario] exact_match: expected "123" got "456"
  ✗ [cnpj] exact_match: field missing

HIGH (1 failure):
  ✗ [area] numeric_range: 150.0 outside [100, 140]

MEDIUM (1 failure):
  ✗ [observacoes] string_contains: keyword not found
```

#### Testes necessários

| Test | Cenário |
|------|---------|
| `test_severity_defaults_to_none` | GraderResult sem severity |
| `test_severity_in_json_report` | JSON output inclui severity |
| `test_console_groups_by_severity` | Console agrupa falhas por nível |
| `test_severity_enum_values` | 4 valores válidos |
| `test_critical_failure_in_ci_summary` | ci_summary destaca CRITICAL |

---

### Módulo B3: Gate Result Classification

**Prioridade: ALTA**

Adicionar classificação de 4 níveis ao `EvalRun`.

#### Mudança em `src/gbr_eval/harness/models.py`

```python
class GateResult(StrEnum):
    GO = "go"
    CONDITIONAL_GO = "conditional_go"
    NO_GO = "no_go"
    NO_GO_ABSOLUTE = "no_go_absolute"
```

Adicionar a `EvalRun`:

```python
class EvalRun(BaseModel):
    # ... campos existentes ...
    gate_result: GateResult | None = None
    baseline_run_id: str | None = None
```

#### Localização canônica: `src/gbr_eval/harness/regression.py`

`classify_gate` vive em `regression.py` (depende de `RegressionDelta`). O `runner.py` importa e chama.

#### Distinção `overall_score` vs `suite_pass_threshold`

**ATENÇÃO:** `run_suite()` em `runner.py:141` calcula `overall_score = tasks_passed / tasks_total` — é uma **taxa de aprovação** (pass rate), NÃO um score ponderado. O `pass_threshold` das tasks individuais (default 0.95) é um conceito diferente.

O gate classification opera em **duas camadas**:
1. **Per-task:** cada `TaskResult.passed` já incorpora o `pass_threshold` da task
2. **Suite-level:** `classify_gate` inspeciona `TaskResult.passed` e `GraderResult.required/passed`, NÃO compara `overall_score` com um threshold

```python
def classify_gate(
    run: EvalRun,
    delta: RegressionDelta | None = None,
) -> GateResult:
    """Classifica o resultado do run em 4 níveis de gate.

    NÃO usa overall_score (que é pass rate). Inspeciona resultados
    individuais de tasks e graders para determinar o gate result.
    """
    if delta and delta.has_regressions:
        return GateResult.NO_GO_ABSOLUTE

    any_required_failed = any(
        r.required and not r.passed
        for tr in run.task_results
        for r in tr.grader_results
    )
    if any_required_failed:
        return GateResult.NO_GO

    all_tasks_passed = all(tr.passed for tr in run.task_results)
    if all_tasks_passed:
        all_optional_pass = all(
            r.passed
            for tr in run.task_results
            for r in tr.grader_results
            if not r.required
        )
        return GateResult.GO if all_optional_pass else GateResult.CONDITIONAL_GO

    # Algumas tasks falharam (score abaixo do pass_threshold individual)
    # mas nenhum required grader falhou → CONDITIONAL_GO se apenas optional
    any_task_has_required_failure = any(
        any(r.required and not r.passed for r in tr.grader_results)
        for tr in run.task_results
        if not tr.passed
    )
    if any_task_has_required_failure:
        return GateResult.NO_GO

    return GateResult.CONDITIONAL_GO
```

#### Mudança no reporter

`ci_summary` inclui gate result:

```
gbr-eval | product gate | CONDITIONAL GO | 4/5 passed | Score: 85.0%
  ⚠ Optional graders failed: [field_f1:observacoes]
```

#### CLI exit codes

| Gate Result | Exit Code | Significado CI |
|-------------|-----------|----------------|
| GO | 0 | Pipeline continua |
| CONDITIONAL_GO | 0 | Pipeline continua (warning no log) |
| NO_GO | 1 | Pipeline falha |
| NO_GO_ABSOLUTE | 2 | Pipeline falha (regressão detectada) |

#### Testes necessários

| Test | Cenário |
|------|---------|
| `test_go_when_all_pass` | Todos graders passam |
| `test_conditional_go_optional_fail` | Required ok, optional falham |
| `test_no_go_required_fail` | Required grader falha |
| `test_no_go_absolute_regression` | Newly failing detectado |
| `test_exit_code_matches_gate` | CLI retorna exit code correto |
| `test_ci_summary_includes_gate` | Gate result no ci_summary |

---

### Módulo B4: Golden Set Tags

**Prioridade: MÉDIA**

Tags de provenance nos golden set cases para rastrear como o baseline evolui.

#### Formato do JSON file (`golden/{skill}/case_NNN.json`)

```json
{
  "case_number": 1,
  "document_hash": "sha256:abc123...",
  "tags": ["seed"],
  "expected_output": { ... },
  "annotator": "diogo",
  "created_at": "2026-04-18T10:00:00Z"
}
```

#### Tags padronizadas

| Tag | Significado | Quando usar |
|-----|-----------|-------------|
| `seed` | Case inicial do golden set | Primeira anotação |
| `regression` | Adicionado após regressão detectada | P4 do OODA-EVAL |
| `incident` | Adicionado após incidente em produção | P5 do OODA-EVAL |
| `edge_case` | Caso limite identificado em operação | Feedback do HITL |
| `hitl` | Correção humana que o eval automatizado não detectaria | Feedback da Anne (operação) |

#### Validação no runner

`load_task` não valida tags (são metadata). O runner ignora tags — elas existem para rastreabilidade e filtragem no frontend/reporting.

#### Reporter enhancement

`json_report` inclui tags quando disponíveis no golden set metadata:

```json
{
  "task_results": [
    {
      "task_id": "extraction.matricula.cpf",
      "golden_set_tags": ["seed", "regression"],
      ...
    }
  ]
}
```

---

### Módulo B5: EVAL First Validation

**Prioridade: MÉDIA**

Validar que tasks tenham os campos mínimos do EVAL First checklist antes de serem consideradas `active`.

#### Novos campos opcionais em `Task` (`src/gbr_eval/harness/models.py`)

```python
class Task(BaseModel):
    # ... campos existentes ...
    target_threshold: float | None = None      # north star (acima do pass_threshold)
    baseline_run_id: str | None = None         # run de referência para regression
    regression_signal: str | None = None       # descrição do que indica regressão
    eval_owner: str | None = None              # quem é responsável por este eval
    eval_cadence: str | None = None            # por deploy / nightly / semanal / sprint
```

#### EVAL First Checklist (7 perguntas)

Quando o CLI carrega uma task com `tier: gate`, valida:

| # | Pergunta | Campo obrigatório | Validação |
|---|----------|-------------------|-----------|
| 1 | O que significa sucesso? | `description` | Não vazio |
| 2 | Como medir? | `graders` | >= 1 grader |
| 3 | Qual é o baseline? | `expected` | Não vazio |
| 4 | Threshold mínimo? | `pass_threshold` | > 0.0 |
| 5 | Threshold alvo? | `target_threshold` | Opcional (warning se ausente) |
| 6 | Sinal de regressão? | `regression_signal` | Opcional (warning se ausente) |
| 7 | Quem valida? | `eval_owner` | Opcional (warning se ausente) |

**Comportamento:** Campos 1-4 são obrigatórios (task não carrega sem eles — já é o caso hoje). Campos 5-7 geram **warning** no console se ausentes, mas não bloqueiam execução. Isso incentiva completar o checklist sem quebrar tasks existentes.

#### Testes necessários

| Test | Cenário |
|------|---------|
| `test_new_fields_optional_in_yaml` | Tasks antigas sem novos campos carregam normalmente |
| `test_target_threshold_in_json_report` | JSON output inclui target_threshold |
| `test_warning_when_eval_owner_missing` | Warning no console, não erro |

---

### Módulo B6: Trend Detection

**Prioridade: MÉDIA**

Detectar degradação progressiva mesmo quando scores estão acima do threshold.

#### Novo arquivo: `src/gbr_eval/harness/trends.py`

```python
@dataclass
class TrendAlert:
    task_id: str
    metric: str                    # "score" | "duration_ms"
    direction: str                 # "declining" | "improving"
    consecutive_runs: int          # quantos runs consecutivos nesta direção
    current_value: float
    threshold: float               # pass_threshold da task
    distance_to_threshold: float   # current - threshold (positivo = acima)

def detect_trends(
    runs: list[EvalRun],
    min_consecutive: int = 3,
) -> list[TrendAlert]:
    """Analisa N runs ordenados cronologicamente e detecta tendências."""
```

#### Lógica

```
Para cada task_id presente em todos os runs:
  scores = [run.get_task_score(task_id) for run in sorted_runs]
  
  Se os últimos `min_consecutive` scores são estritamente decrescentes:
    → TrendAlert(direction="declining", ...)
  
  Se declining E distance_to_threshold < 0.05 (5%):
    → Adicionar flag "approaching_threshold"
```

#### CLI flag

```bash
# Detectar tendências em histórico de runs
gbr-eval trends --runs-dir results/ --min-consecutive 3
```

#### Testes necessários

| Test | Cenário |
|------|---------|
| `test_no_trend_stable_scores` | Scores iguais → sem alerta |
| `test_declining_trend_detected` | 3 scores decrescentes → alerta |
| `test_improving_trend_detected` | 3 scores crescentes → alerta positivo |
| `test_insufficient_runs_no_alert` | Menos de min_consecutive runs → sem alerta |
| `test_approaching_threshold_flag` | Score a 5% do threshold → flag extra |
| `test_mixed_tasks_independent` | Tendência por task, não global |

---

### Módulo B7: Post-mortem Schema

**Prioridade: BAIXA**

Formato padronizado de post-mortem vinculado a eval runs.

#### Schema (para JSON report e frontend)

```python
class PostMortem(BaseModel):
    what: str           # 1 frase: o que aconteceu
    root_cause: str     # causa raiz (não sintoma)
    impact: str         # quantos afetados, qual banco
    fix: str            # o que foi mudado
    prevention: str     # o que o EVAL agora detectaria
    created_by: str
    created_at: datetime
```

Não é um campo em `EvalRun` — é metadata separada, linkada por `run_id`. O CLI não produz post-mortems; o frontend cria e armazena. O JSON report pode incluir se fornecido.

#### Testes necessários

| Test | Cenário |
|------|---------|
| `test_postmortem_serialization_roundtrip` | Serialize → deserialize preserva todos os campos |
| `test_postmortem_required_fields` | `what`, `root_cause`, `impact`, `fix`, `prevention`, `created_by` são obrigatórios |
| `test_postmortem_created_at_default` | `created_at` tem default datetime.now(UTC) |

---

### Módulo B8: Accuracy Grader (Classification)

**Prioridade: MUST-HAVE para Gate Fase 1 — criterion 1**

Gate Fase 1 exige "Classification >= 90%". Nenhum grader existente computa acurácia de classificação. Os graders atuais operam em pares individuais (input/output), não em agregados batch.

#### Design Decision: accuracy = suite-level pass rate

A classificação é avaliada assim:
1. Cada golden set case tem um `document_type` esperado
2. Cada case gera uma task com `exact_match` no campo `document_type`
3. `run_suite()` executa todas as tasks → `tasks_passed / tasks_total` = accuracy

**Portanto, accuracy NÃO é um grader novo — é a interpretação de `overall_score` de um suite de classification tasks.** O que falta é:

1. **Tasks YAML de classificação** para os 5 P0 doc types (+ negativos/confusores)
2. **Documentação explícita** de que `overall_score` de um suite de classification tasks = accuracy

#### O que precisa ser criado

```
tasks/product/classification/
├── matricula_correctly_classified.yaml      # exact_match no document_type
├── contrato_social_correctly_classified.yaml
├── cnd_correctly_classified.yaml
├── procuracao_correctly_classified.yaml
├── balanco_correctly_classified.yaml
├── confuser_iptu_not_matricula.yaml         # documento similar, deve NÃO classificar como matrícula
└── confuser_certidao_not_cnd.yaml           # certidão genérica, deve NÃO classificar como CND
```

Cada task YAML:
```yaml
task_id: classification.matricula
category: classification
layer: product
tier: gate
graders:
  - type: exact_match
    field: document_type
    weight: 1.0
    required: true
    config:
      severity: critical
```

#### Accuracy threshold

Gate criterion: `accuracy >= 0.90`. Com suite de N classification tasks, isso significa `tasks_passed / tasks_total >= 0.90`.

O runner já computa isso em `run_suite()` → `overall_score`. O gate classification (`classify_gate`) opera sobre os resultados individuais. **Nenhum código novo necessário** — apenas tasks e documentação.

---

### Módulo B9: Evaluator Detection (Red Team)

**Prioridade: ALTA para Gate Fase 1 — criterion 4**

Gate Fase 1 exige "Evaluator detection >= 80%". Isso mede se o sistema detecta documentos adulterados, fraudulentos, ou injetados.

#### Design: adversarial golden set + detection grader

```
golden/red_team/
├── metadata.yaml
├── case_001_matricula_adulterada.json    # campos alterados intencionalmente
├── case_002_cnd_vencida_editada.json     # validade editada para parecer válida
├── case_003_contrato_social_fake.json    # documento completamente fabricado
├── case_004_procuracao_revogada.json     # procuração revogada apresentada como válida
└── case_005_balanco_inflado.json         # números alterados
```

Cada case tem:
```json
{
  "case_number": 1,
  "tags": ["red_team", "adversarial"],
  "injection_type": "field_alteration",
  "expected_output": {
    "authenticity_flag": "suspicious",
    "detected_anomalies": ["campo_alterado: area"]
  }
}
```

#### Tasks YAML

```yaml
task_id: red_team.matricula_adulterada
category: classification
layer: product
tier: gate
graders:
  - type: exact_match
    field: authenticity_flag
    weight: 1.0
    required: true
    config:
      severity: critical
  - type: field_not_empty
    field: detected_anomalies
    weight: 0.5
```

#### Escopo para Gate Fase 1

- Mínimo 5 cases adversariais (1 por P0 skill)
- Detection rate = tasks passando / total red team tasks >= 0.80
- Os cases adversariais são criados pelo CLO (Diogo) — NÃO auto-gerados

#### Decisão pendente

Se o ai-engine do gbr-engines ainda não implementa detecção de adulteração (`authenticity_flag`), este critério pode ser marcado como **blocked** até que a capability exista no target system. Documentar explicitamente:

- Se o ai-engine TEM detecção → criar tasks + golden set red team
- Se o ai-engine NÃO TEM detecção → marcar criterion 4 como "NOT EVALUABLE — capability not implemented in target system" e comunicar ao Gate review

---

## 4. Plano de Sprints (Backend)

### Diagrama de Dependências

```
┌────────────────────┐     ┌────────────────────┐
│ B2: Severity       │     │ B4: Golden Set Tags│
│ (models.py change) │     │ (file format)      │
└────────┬───────────┘     └────────────────────┘
         │
┌────────▼───────────┐     ┌────────────────────┐
│ B3: Gate Matrix    │────►│ B1: Regression     │
│ (models + runner)  │     │ Delta Analysis     │
└────────────────────┘     └────────┬───────────┘
                                    │
                           ┌────────▼───────────┐
                           │ B5: EVAL First     │
                           │ Validation         │
                           └────────────────────┘
                           
                           ┌────────────────────┐
                           │ B6: Trend Detection│  ← Depende de B1 (múltiplos runs)
                           └────────────────────┘
                           
                           ┌────────────────────┐
                           │ B7: Post-mortem    │  ← Independente
                           └────────────────────┘
```

---

### Sprint B1 — Regression + Severity + Gate (Semana 1)
**Meta: Detecção de regressão funcional no CLI para iterações Gate Fase 1**
**Deadline: 25/Abr/2026**

| # | Task | Módulo | Estimativa | Bloqueio? |
|---|------|--------|------------|-----------|
| B1.1 | Adicionar `Severity` e `GateResult` enums a `models.py` | B2, B3 | 1h | — |
| B1.2 | Adicionar `severity` a `GraderResult`, `gate_result` e `baseline_run_id` a `EvalRun` | B2, B3 | 1h | B1.1 |
| B1.3 | Implementar `regression.py` com `compare_runs()`, `load_baseline()`, `classify_gate()` | B1 | 4h | B1.2 |
| B1.4 | Integrar gate classification em `run_task()` / `run_suite()` | B3 | 2h | B1.3 |
| B1.5 | CLI: adicionar `--baseline-run` flag | B1 | 2h | B1.3 |
| B1.6 | CLI: exit codes baseados em `GateResult` | B3 | 1h | B1.4 |
| B1.7 | Reporter: severity grouping em `console_report` e `ci_summary` | B2 | 2h | B1.2 |
| B1.8 | Reporter: regression delta section em console e JSON | B1 | 2h | B1.3 |
| B1.9 | Testes: `test_regression.py` (8 testes) | B1 | 3h | B1.3 |
| B1.10 | Testes: `test_severity.py` e `test_gate_result.py` (11 testes) | B2, B3 | 2h | B1.2 |
| B1.11 | Atualizar testes existentes para novos campos opcionais | — | 1h | B1.2 |
| B1.12 | Criar 5+ classification task YAMLs (1 por P0 skill + confusores) | B8 | 2h | — |
| B1.13 | Documentar que classification accuracy = suite-level pass rate | B8 | 1h | B1.12 |
| B1.14 | Criar estrutura red team (`golden/red_team/`, 5 cases adversariais placeholder) | B9 | 2h | — |
| B1.15 | Criar 5 red team task YAMLs (1 por P0 skill) | B9 | 1h | B1.14 |
| | **Total Sprint B1** | | **27h** | |

**Entregável:** `gbr-eval run --suite tasks/ --baseline-run prev.json` → mostra regression delta, gate result, severity grouping.

---

### Sprint B2 — Tags + EVAL First + Trends (Semana 2-3)
**Meta: Rastreabilidade e monitoramento contínuo**

| # | Task | Módulo | Estimativa | Bloqueio? |
|---|------|--------|------------|-----------|
| B2.1 | Golden set JSON format: adicionar `tags` field com documentação | B4 | 2h | — |
| B2.2 | Reporter: incluir `golden_set_tags` no JSON report quando disponível | B4 | 1h | B2.1 |
| B2.3 | Adicionar campos opcionais a `Task` model (`target_threshold`, `baseline_run_id`, `regression_signal`, `eval_owner`, `eval_cadence`) | B5 | 2h | — |
| B2.4 | **Atualizar `load_task()` em `runner.py`** para ler os 5 novos campos do YAML com `.get()` defaults (sem isso, campos são ignorados silenciosamente) | B5 | 1h | B2.3 |
| B2.5a | EVAL First warnings em `load_task()` para campos 5-7 ausentes quando `tier: gate` | B5 | 1h | B2.4 |
| B2.6 | Implementar `trends.py` com `detect_trends()` | B6 | 3h | — |
| B2.7 | CLI: comando `gbr-eval trends --runs-dir <path>` (output separado do `run`, ver Seção 6.1) | B6 | 2h | B2.6 |
| B2.8 | Post-mortem schema (`PostMortem` Pydantic model) | B7 | 1h | — |
| B2.9 | Testes: `test_trends.py` (6 testes) | B6 | 2h | B2.6 |
| B2.10 | Testes: `test_eval_first_validation.py` (3+ testes) | B5 | 1h | B2.5a |
| B2.11 | Testes: `test_golden_set_tags.py` (3 testes) | B4 | 1h | B2.1 |
| B2.12 | Testes: `test_postmortem.py` (3 testes: serialização, required fields, datetime default) | B7 | 1h | B2.8 |
| B2.13 | Documentação: `docs/LAYER_MAPPING.md` (referência canônica gbr-eval ↔ OODA-EVAL) | Docs | 1h | — |
| | **Total Sprint B2** | | **24h** | |

**Entregável:** Tags em golden sets, warnings para EVAL First checklist, `gbr-eval trends` funcional.

---

## 5. Arquitetura Após Adições

```
src/gbr_eval/
├── graders/
│   ├── base.py              ✅ (sem mudança)
│   ├── deterministic.py      ✅ (sem mudança)
│   ├── field_f1.py           ✅ (sem mudança)
│   └── model_judge.py        ✅ (sem mudança)
├── harness/
│   ├── models.py             🔄 + Severity, GateResult, novos campos em Task/GraderResult/EvalRun
│   ├── runner.py             🔄 + EVAL First warnings, load_task() update, exit codes (importa classify_gate de regression.py)
│   ├── reporter.py           🔄 + severity grouping, regression delta section, gate result
│   ├── regression.py         🆕 compare_runs(), load_baseline(), RegressionDelta
│   └── trends.py             🆕 detect_trends(), TrendAlert
├── calibration/
│   └── iaa.py                ✅ (sem mudança)
└── contracts/
    └── validator.py           ✅ (sem mudança)
```

---

## 6. Formato de Saída Atualizado

### 6.1 Dois formatos de saída separados

O CLI produz **dois formatos distintos** de JSON, de **dois comandos diferentes**:

| Comando | Formato | Contém |
|---------|---------|--------|
| `gbr-eval run` | Run Report | `gate_result`, `regression_delta`, `task_results` com `severity` |
| `gbr-eval trends` | Trend Report | `trend_alerts` array |

O frontend importa ambos separadamente. **NÃO misturar** `trend_alerts` no output do `run`.

### JSON Run Report (`gbr-eval run` output)

```json
{
  "run_id": "abc123",
  "layer": "product",
  "tier": "gate",
  "gate_result": "conditional_go",
  "baseline_run_id": "xyz789",
  "tasks_total": 5,
  "tasks_passed": 4,
  "tasks_failed": 1,
  "overall_score": 0.85,
  "started_at": "2026-04-18T10:00:00Z",
  "finished_at": "2026-04-18T10:02:30Z",
  "task_results": [
    {
      "task_id": "extraction.matricula.cpf",
      "passed": true,
      "score": 1.0,
      "grader_results": [
        {
          "grader_type": "exact_match",
          "field": "cpf_proprietario",
          "passed": true,
          "score": 1.0,
          "severity": "critical",
          "details": "exact match"
        }
      ],
      "golden_set_tags": ["seed"]
    }
  ],
  "regression_delta": {
    "baseline_run_id": "xyz789",
    "newly_failing": [],
    "newly_passing": ["extraction.matricula.area"],
    "new_tasks": [],
    "removed_tasks": [],
    "score_deltas": {
      "extraction.matricula.cpf": 0.0,
      "extraction.matricula.area": 0.4
    },
    "has_regressions": false
  }
}
```

### JSON Trend Report (`gbr-eval trends` output — separado)

```json
{
  "analyzed_runs": 5,
  "min_consecutive": 3,
  "trend_alerts": [
    {
      "task_id": "extraction.contrato.cnpj",
      "metric": "score",
      "direction": "declining",
      "consecutive_runs": 3,
      "current_value": 0.88,
      "threshold": 0.85,
      "distance_to_threshold": 0.03
    }
  ]
}
```

### Console Report (após todas as adições)

```
╔══════════════════════════════════════════════════════╗
║  Eval Run abc123 | product gate | CONDITIONAL GO      ║
╚══════════════════════════════════════════════════════╝

  CRITICAL (0 failures)

  HIGH (1 failure):
    ✗ extraction.matricula.area [area] numeric_range: 160.0 outside [100, 150]

  ── Regression Delta (vs xyz789) ──
  ✓ No regressions detected
  ↑ Newly passing: extraction.matricula.area (+0.4)

  ── Trend Alerts ──
  ⚠ extraction.contrato.cnpj declining for 3 runs (0.88, threshold 0.85)

  Total: 5 | Pass: 4 | Fail: 1 | Score: 85.0%
```

### CI Summary (1 linha)

```
gbr-eval | product gate | CONDITIONAL GO | 4/5 passed | 85.0% | ⚠ 1 trend alert
```

---

## 7. CLI Completo (após todas as adições)

```bash
# Comandos existentes
gbr-eval --version
gbr-eval --help
gbr-eval run --suite <dir>
gbr-eval run --task <yaml>
gbr-eval run --suite <dir> --layer engineering
gbr-eval run --suite <dir> --tier gate
gbr-eval run --suite <dir> --output-format json
gbr-eval run --suite <dir> --output-file result.json

# Novos flags (Sprint B1)
gbr-eval run --suite <dir> --baseline-run <json>   # regression delta vs baseline

# Novo comando (Sprint B2)
gbr-eval trends --runs-dir <dir>                    # detectar tendências em histórico
gbr-eval trends --runs-dir <dir> --min-consecutive 3
gbr-eval trends --runs-dir <dir> --output-format json
```

### Exit Codes

| Code | Significado | Gate Result |
|------|-------------|-------------|
| 0 | Sucesso | GO ou CONDITIONAL_GO |
| 1 | Falha | NO_GO |
| 2 | Regressão detectada | NO_GO_ABSOLUTE |

---

## 8. Compatibilidade

### Backwards Compatibility

Todas as adições são **aditivas e opcionais**:

- `severity` em `GraderResult`: default `None`, campos existentes não quebram
- `gate_result` em `EvalRun`: default `None`, runs sem baseline continuam funcionando
- `target_threshold`, `baseline_run_id`, etc. em `Task`: opcionais no YAML, ignorados se ausentes
- `tags` em golden set JSON: campo opcional, runner ignora se ausente
- Exit codes: `0` para GO e CONDITIONAL_GO mantém compatibilidade com CI existente

### Formato de Arquivo

| Arquivo | Mudança | Compat |
|---------|---------|--------|
| Task YAML | 5 novos campos opcionais | 100% retrocompat |
| Golden set JSON | Novo campo `tags` | 100% retrocompat |
| CLI JSON output | Novos campos `gate_result`, `regression_delta`, `trend_alerts`, `severity` | 100% aditivo |
| JUnit XML | `<properties>` com gate result | 100% aditivo |

---

## 9. Métricas de Sucesso (Backend)

### Sprint B1 (25/Abr/2026)

- [ ] `compare_runs()` funcional com 8+ testes
- [ ] `--baseline-run` flag no CLI
- [ ] Gate matrix (4 níveis) integrado
- [ ] Severity em GraderResult com console grouping
- [ ] Exit codes diferenciados por gate result
- [ ] Todos os 160+ testes existentes continuam passando
- [ ] Coverage >= 80%

### Sprint B2 (02/Mai/2026)

- [ ] Golden set tags no formato JSON
- [ ] EVAL First warnings no load_task
- [ ] `gbr-eval trends` funcional
- [ ] Post-mortem schema definido
- [ ] Layer mapping documentado
- [ ] Coverage >= 80%

### Integração com Frontend (Sprints 3-4 do frontend)

- [ ] Frontend importa JSON com regression_delta e trend_alerts
- [ ] Run Dashboard exibe gate matrix
- [ ] Trend charts usam dados do `gbr-eval trends`
- [ ] Post-mortem editor salva no formato do backend schema

---

## 10. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Regression delta adiciona overhead ao CI | BAIXO | `--baseline-run` é opt-in; sem flag, comportamento inalterado |
| Severity derivada de skill fields requer integração com frontend DB | MÉDIO | Severity é opcional; pode ser setada manualmente no YAML config |
| EVAL First warnings irritam em tasks existentes | BAIXO | Warnings só para `tier: gate`; regression/canary sem warnings |
| Trend detection requer histórico de runs | MÉDIO | Sem histórico suficiente → sem alertas (graceful degradation) |
| Novos campos quebram testes existentes | BAIXO | Todos opcionais com defaults; testes existentes não precisam mudar |
