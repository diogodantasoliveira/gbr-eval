# gbr-eval — Manual do Engenheiro

> Ultima atualizacao: 2026-04-20
> Autor: Diogo Dantas (CLO/CAIO) + Claude (co-processador)
> Status: Framework operacional, 533 testes, 40 golden cases (8/skill), 6 auditorias independentes

---

## 1. O que e o gbr-eval

gbr-eval e o **backbone centralizado de qualidade** da GarantiaBR. Ele define e verifica criterios mensuraveis em quatro camadas:

| Camada | Nome | O que avalia |
|--------|------|-------------|
| **E** | Engineering Quality | Codigo segue padroes de engenharia e regras de dominio por repo |
| **P** | Product Quality | Outputs de IA corretos contra golden sets anotados por humano |
| **O** | Operational | SLAs, custos, disponibilidade (futuro) |
| **C** | Compliance | LGPD, BACEN, audit trail, ISO 27001 (futuro) |

**Principio fundacional:** Qualidade > Velocidade. Todas as regras vivem centralizadas no gbr-eval — nunca distribuidas nos repos alvo. Consumidas por cada repo via GitHub Action.

O projeto e **separado** dos repos que avalia. Ele consome schemas de API via snapshots (contract testing), nunca importa codigo diretamente. gbr-eval define os criterios de qualidade que toda construcao deve atender desde o dia 1 — o eval existe ANTES dos sistemas que avalia.

### 5 repos prioritarios (Camada E)

| Repo | Dominio | Risco principal |
|------|---------|----------------|
| engine-integracao | Integracoes externas (SERPRO, ONR, TRTs) | Retry infinito, timeout global |
| garantia_ia | IA/prompts, extracao | PII em prompt, custo descontrolado |
| notifier | Notificacoes para clientes bancarios | Notificacao duplicada, LGPD |
| engine-billing | Billing (novo) | Float em financeiro, sem idempotency |
| atom-back-end | Backoffice multi-tenant (novo) | Vazamento tenant, sem audit log |

### Por que existe

A GarantiaBR processa documentos financeiros para instituicoes como Itau, Bradesco e Banco Pine. Cada campo extraido incorretamente pode gerar um parecer errado, uma garantia nao identificada, ou uma decisao de credito comprometida. O eval garante que a qualidade e mensuravel, rastreavel e auditavel (ISO 27001, SOC 2, BACEN).

---

## 2. Setup — maquina limpa em 3 comandos

```bash
git clone git@github.com:garantiabr/gbr-eval.git && cd gbr-eval
uv sync --all-extras
uv run pytest
```

Dependencias principais (pyproject.toml):

| Pacote | Versao | Uso |
|--------|--------|-----|
| pydantic | >= 2.7, < 3 | Modelos de dados tipados |
| pyyaml | >= 6.0, < 7 | Leitura de task YAMLs |
| click | >= 8.1, < 9 | CLI do runner |
| anthropic | >= 0.49, < 1 | LLM-judge (Claude Sonnet) |

Dev: pytest >= 8.2, pytest-cov >= 5.0, ruff >= 0.4, mypy >= 1.10, types-PyYAML >= 6.0.

### Quality gates (rodar TODOS antes de qualquer PR)

```bash
uv run pytest                                              # testes (533 tests)
uv run pytest --cov=src/gbr_eval --cov-report=term-missing # cobertura >= 80%
uv run ruff check .                                        # lint zero errors
uv run mypy src/                                           # type check zero errors
```

Se qualquer um falhar, o PR nao fecha.

---

## 3. Arquitetura do sistema

```
gbr-eval/
├── src/gbr_eval/                   # 28 modulos Python
│   ├── graders/                    # 12 graders + dispatcher context-aware
│   │   ├── base.py                 # Grader + ContextAwareGrader Protocols, _CONTEXT_AWARE registry, grade() dispatcher
│   │   ├── deterministic.py        # 7 graders puros
│   │   ├── field_f1.py             # F1 com fuzzy matching, spec.field priority
│   │   ├── engineering.py          # 3 graders de engenharia + ReDoS guard
│   │   └── model_judge.py          # LLM-as-judge (nao-deterministico), PII recursivo, context_aware=True
│   ├── solvers/                    # Solver Protocol (async) + AgentTrace models
│   │   ├── base.py                 # Solver Protocol, registry (@register_solver)
│   │   ├── models.py               # ToolCall, Message, AgentTrace (Pydantic)
│   │   └── passthrough.py          # PassthroughSolver (returns trace unchanged)
│   ├── harness/                    # Motor de execucao
│   │   ├── models.py               # Pydantic: Task, GraderResult, EvalRun, GateResult, GraderContext, ScoreReducer
│   │   ├── runner.py               # Load tasks, run graders, compute scores, CLI
│   │   ├── async_runner.py         # Async runner para solver-based tasks (usa _run_single_epoch)
│   │   ├── task_helpers.py         # task_with() — copia tasks com overrides
│   │   ├── code_loader.py          # Code Loader: loads target repo files for engineering eval
│   │   ├── reporter.py             # Console, JSON, JUnit XML, CI summary
│   │   ├── regression.py           # Comparacao baseline vs current + degraded_scores
│   │   ├── trends.py               # Deteccao de tendencias (monotonica + slope-based)
│   │   ├── analyzer.py             # Utilitarios de analise
│   │   └── client.py               # EvalClient, OutputRecorder
│   ├── contracts/                  # Schema snapshots dos repos alvo
│   │   └── validator.py            # JSON Schema validation
│   └── calibration/                # Inter-annotator agreement (Cohen's kappa)
│       └── iaa.py
├── tasks/                          # 48 task YAMLs
│   ├── product/                    # classification(11), extraction(6), citation(6), cost(1), latency(1), decision(1)
│   └── engineering/                # atom-back-end(5), engine-billing(4), engine-integracao(5), garantia-ia(4), notifier(4)
├── golden/                         # Golden sets — ground truth anotado por humano
│   ├── matricula/                  # 8 cases (5 standard + 2 edge + 1 confuser)
│   ├── contrato_social/            # 8 cases
│   ├── cnd/                        # 8 cases
│   ├── procuracao/                 # 8 cases
│   ├── certidao_trabalhista/       # 8 cases
│   ├── balanco/                    # metadata only (blocked — 0 docs)
│   └── red_team/                   # metadata only (blocked — capability pending)
├── frontend/                       # Admin panel — Next.js 16 + SQLite
│   ├── src/app/                    # 39 paginas, 57 API routes
│   ├── src/db/                     # Drizzle ORM, 23 tabelas
│   ├── src/lib/                    # PII redaction, validations, scoring
│   └── src/components/             # UI components (shadcn/ui)
├── tools/                          # Scripts auxiliares
│   ├── generate_synthetic.py       # Gerador de golden sets sinteticos (Claude)
│   ├── generate_all_synthetic.py   # Batch generation com env allowlist
│   ├── compute_hashes.py           # SHA-256 dos PDFs originais
│   └── sync_frontend.py            # Sincronizacao frontend com auth token
├── tests/                          # 533 testes (pytest)
│   ├── graders/                    # test_deterministic, test_field_f1, test_engineering, test_model_judge
│   ├── harness/                    # test_runner, test_epochs, test_model_roles, test_grader_context, test_async_runner, test_task_helpers, test_reporter, test_analyzer, test_regression, test_trends, test_cli, test_client, test_eval_first_validation, test_golden_set_tags, test_postmortem, test_code_loader
│   ├── solvers/                    # test_models, test_base
│   ├── contracts/                  # test_contracts
│   ├── integration/                # test_golden_set_smoke
│   └── test_calibration.py
├── runs/                           # Resultados de eval runs
│   ├── baseline_2026_04_18.json
│   ├── self_eval_2026_04_18.json
│   └── self_eval_2026_04_19.json
├── docs/                           # 20 documentos
├── .github/                        # CI/CD
│   ├── workflows/ci.yml            # pytest + ruff + mypy + eval-gate
│   └── actions/gbr-eval-gate/      # GitHub Action reutilizavel
└── contracts/schemas/              # Schema snapshots
```

### Tres runners — papeis diferentes

| Runner | O que faz | Quando roda |
|--------|-----------|-------------|
| **pytest** | Testa o framework (graders, models, runner) | CI do gbr-eval |
| **CLI (runner.py)** | Executa suites de eval contra outputs reais | CI dos repos alvo + avaliacoes manuais |
| **async_runner.py** | Executa tasks via Solver Protocol (async, captura AgentTrace) | Eval de trajetoria de agentes |

pytest testa SE os graders funcionam. O CLI testa O QUE os graders avaliam. O async_runner testa COMO o agente chegou no resultado.

Ambos os runners (sync e async) delegam grading para `_run_single_epoch()` — funcao compartilhada que garante logica identica. Suportam multi-epoch com short-circuit para graders deterministicos e score reducers (MEAN, MEDIAN, AT_LEAST_ONE, ALL_PASS, MAJORITY).

### Code Loader — avaliacao de codigo real

Para tasks de Camada E (Engineering), o CLI aceita `--code-dir` apontando para o diretorio raiz do repo alvo. O Code Loader carrega os arquivos do repo e os disponibiliza para os graders de engenharia:

```bash
# Avaliar engenharia apontando para um repo local
gbr-eval run --suite tasks/engineering/ --code-dir /caminho/para/engine-billing/

# Avaliar repo especifico em modo local-first (antes do PR)
gbr-eval run --suite tasks/engineering/billing/ --code-dir ~/repos/engine-billing/
```

O `--code-dir` e um parametro hibrido: funciona tanto localmente (engenheiro roda na maquina antes do PR) quanto no CI (workflow clona o repo alvo e passa o path). Os graders recebem o conteudo de cada arquivo individualmente — **nao uma concatenacao de todos os arquivos**.

---

## 4. Modelos de dados (models.py)

Todos os modelos sao Pydantic BaseModel com tipagem estrita.

### Enums

```python
class Layer(StrEnum):    ENGINEERING, PRODUCT, OPERATIONAL, COMPLIANCE
class Tier(StrEnum):     GATE, REGRESSION, CANARY
class Category(StrEnum): CLASSIFICATION, EXTRACTION, DECISION, CITATION,
                         COST, LATENCY, CODE_QUALITY, TENANT_ISOLATION, CONVENTION
class ScoringMode(StrEnum): WEIGHTED, BINARY, HYBRID
class Severity(StrEnum):    CRITICAL, HIGH, MEDIUM, LOW
class GateResult(StrEnum):  GO, CONDITIONAL_GO, NO_GO, NO_GO_ABSOLUTE
class ScoreReducer(StrEnum): MEAN, AT_LEAST_ONE, ALL_PASS, MAJORITY, MEDIAN
```

### Task — definicao de uma avaliacao

```python
class Task(BaseModel):
    task_id: str                    # ex: "extraction.certidao_trabalhista.fields"
    category: Category
    component: str                  # ex: "ai-engine"
    layer: Layer                    # engineering, product, operational, compliance
    tier: Tier                      # gate (bloqueia), regression (compara), canary (observa)
    tenant_profile: str             # "global" ou tenant especifico
    description: str                # descricao da task (default "")
    input: TaskInput                # endpoint + payload
    expected: dict[str, Any]        # valores esperados (ou PLACEHOLDERs)
    graders: list[GraderSpec]       # lista de graders a aplicar
    scoring_mode: ScoringMode       # como calcular score final
    pass_threshold: float           # minimo para passar (default 0.95)
    target_threshold: float | None  # meta ideal — DEVE ser >= pass_threshold (validado)
    baseline_run_id: str | None
    regression_signal: str | None
    eval_owner: str | None
    eval_cadence: str | None
    golden_set_tags: list[str] | None = None
    epochs: int = 1                 # repeticoes (>1 util para graders nao-deterministicos)
    reducers: list[ScoreReducer] = [MEAN]  # como agregar epoch scores
    primary_reducer: ScoreReducer = MEAN   # reducer que determina passed/failed
```

**Validacao:** `primary_reducer` deve estar na lista de reducers (validado por model_validator).

**Validacao target_threshold:** Pydantic `model_validator(mode="after")` garante que `target_threshold >= pass_threshold`. Tambem valida `0.0 <= target_threshold <= 1.0` via `Field(ge=0.0, le=1.0)`.

### GraderContext — contexto acumulado entre graders

```python
class GraderContext(BaseModel):
    metadata: dict[str, Any] = {}      # task_id, tenant_profile, model_roles, has_trace
    previous_results: list[GraderResult] = []  # resultados dos graders anteriores
```

Passado a cada grader via `grade()`. Graders context-aware (registrados com `context_aware=True`) recebem o contexto como keyword argument. Graders deterministicos o ignoram.

### GraderSpec — configuracao de um grader

```python
class GraderSpec(BaseModel):
    type: str                           # nome do grader (ex: "exact_match")
    field: str | None                   # campo a avaliar (suporta dotted paths: "citation.cpf")
    weight: float = 1.0                 # peso no scoring
    required: bool = False              # se True, falha e NO_GO
    config: dict[str, Any] = {}         # config especifica do grader
    model_role: str | None = None       # role para resolucao de modelo via --model-role
```

### GraderResult — resultado de um grader

```python
class GraderResult(BaseModel):
    grader_type: str
    field: str | None
    passed: bool
    score: float           # 0.0 a 1.0
    weight: float = 1.0
    required: bool = False
    details: str = ""
    error: str | None = None
    severity: Severity | None = None
    file_path: str | None = None   # caminho do arquivo avaliado (engineering tasks)
```

### EvalRun — resultado consolidado de uma suite

```python
class EvalRun(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime | None
    layer: Layer
    tier: Tier | None
    tasks_total: int
    tasks_passed: int
    tasks_failed: int
    task_results: list[TaskResult]
    overall_score: float            # MEDIA dos task scores (nao pass-rate)
    metadata: dict[str, Any]
    gate_result: GateResult | None
    baseline_run_id: str | None
```

**overall_score e a media dos task scores**, nao `tasks_passed / tasks_total`. Isso captura degradacao silenciosa (task caindo de 1.0 para 0.6 ainda "passando" com threshold 0.5).

### TaskResult — resultado de uma task individual

```python
class TaskResult(BaseModel):
    task_id: str
    passed: bool
    score: float                   # 0.0 a 1.0
    grader_results: list[GraderResult]
    duration_ms: float = 0.0
    pass_threshold: float = 0.95
    error: str | None = None
    golden_set_tags: list[str] | None = None
    reducer_scores: dict[str, float] = {}  # score por reducer
    epoch_scores: list[float] = []         # scores de cada epoch
```

### PostMortem — analise pos-falha

```python
class PostMortem(BaseModel):
    what: str                      # o que aconteceu
    root_cause: str                # causa raiz
    impact: str                    # impacto
    fix: str                       # correcao aplicada
    prevention: str                # como prevenir
    created_by: str
    created_at: datetime
```

---

## 5. Graders — os avaliadores

### Interface e registro (base.py)

Dois Protocols:

```python
class Grader(Protocol):
    def grade(self, output: dict, expected: dict, spec: GraderSpec) -> GraderResult: ...

class ContextAwareGrader(Protocol):
    def grade(self, output: dict, expected: dict, spec: GraderSpec, *, context: GraderContext | None = None) -> GraderResult: ...
```

**Dois Protocols:** `Grader` para graders deterministicos, `ContextAwareGrader` para graders que recebem resultados de graders anteriores (atualmente apenas LLM-judge). `ContextAwareGrader` NAO e `@runtime_checkable` — o dispatch em tempo de execucao usa o set `_CONTEXT_AWARE` populado via `register_grader(name, context_aware=True)`.

Registro via decorator:

```python
@register_grader("exact_match")      # grader deterministico
class ExactMatch:
    def grade(self, output, expected, spec):
        ...

@register_grader("llm_judge", context_aware=True)  # grader context-aware
class LLMJudge:
    def grade(self, output, expected, spec, *, context: GraderContext | None = None):
        ...
```

Lookup dinamico:

```python
grader = get_grader("exact_match")  # retorna instancia
result = grader.grade(output, expected, spec)
```

A funcao `grade()` em base.py encapsula try/except para KeyError, ValueError, TypeError e AttributeError — nunca propaga excecoes ao runner.

### 7 graders deterministicos (deterministic.py)

| Grader | O que faz | Config |
|--------|-----------|--------|
| `exact_match` | Compara valores exatamente | `case_sensitive` (default True) |
| `numeric_range` | Valor dentro de min/max | `min`, `max` |
| `numeric_tolerance` | Float com tolerancia % | `tolerance` (default 0.01), `allow_null` (default false) |
| `regex_match` | Match contra padrao regex | `pattern` |
| `field_not_empty` | Campo existe e nao e vazio | — |
| `set_membership` | Valor esta no conjunto permitido | `valid_values` |
| `string_contains` | String contem substring | `substring`, `case_sensitive` |

Todos usam `_get_field(data, path)` para navegar dotted paths (ex: `citation.cpf` -> `data["citation"]["cpf"]`).

### 3 graders de engenharia (engineering.py)

| Grader | O que faz | Config |
|--------|-----------|--------|
| `pattern_required` | Padrao regex DEVE estar presente no codigo | `pattern`, `file_key` (default "content") |
| `pattern_forbidden` | Padrao regex NAO DEVE estar presente | `pattern`, `file_key` |
| `convention_check` | Conjunto de regras (required + forbidden) | `rules` (array de {pattern, type, description}) |

**Protecoes:**
- **ReDoS guard:** `_is_catastrophic_pattern()` rejeita padroes com quantificadores aninhados (`(a+)+$`, `(x+)+y`). Retorna fail com "catastrophic" em details.
- **Truncamento:** conteudo > 100.000 chars e truncado antes da busca (`_MAX_INPUT_LEN`).
- **Pattern max length:** padroes > 1.000 chars sao rejeitados.
- **Invalid regex:** regex invalido retorna fail com "Invalid regex" em details.

`convention_check` retorna score parcial: `max(0, 1 - violations/total_rules)`. Regras com regex invalido contam como violacao com "ERROR" em details.

### F1 por campo (field_f1.py)

Calcula precision, recall e F1 comparando campos extraidos vs esperados:

- **Fuzzy matching** para strings (threshold 0.85 via difflib)
- **Numeric matching** para numeros (tolerance 0.01)
- **Bool/int handling:** `isinstance(actual, bool)` verificado antes de `isinstance(actual, int)` — evita confusao `True == 1`
- **Dict matching** — recursao por chaves (compara cada campo internamente, sem stringificar)
- **Comparacao de listas** order-agnostic com bipartite matching
- Config: `critical_fields` (lista de campos a avaliar), `f1_threshold` (default 0.90)

**Resolucao de escopo (prioridade):**
1. `spec.field` se definido -> avalia apenas esse campo
2. `scope=critical_only` com `critical_fields` -> avalia campos criticos
3. Senao -> avalia todos os campos em `expected`

Se `scope=critical_only` sem `critical_fields` e sem `spec.field`, retorna fail com "scope=critical_only but no critical_fields configured".

Retorna: `score = F1`, `details = "TP=X FP=Y FN=Z precision=P recall=R f1=F"`

### LLM-judge (model_judge.py)

Grader nao-deterministico que chama Claude Sonnet via API:

- **Sanitizacao PII recursiva** antes de enviar — funcao `_redact()` percorre dicts/lists/strings recursivamente
- Rubric de 1-5 (-> normalizado para 0.0-1.0, clamped)
- Escape hatch: se responde "cannot evaluate", retorna score 0.0
- Requer `ANTHROPIC_API_KEY` env var; retorna 0.0 + warning se ausente
- Config: `rubric`, `min_score`, `model` (default "claude-sonnet-4-5-20250929")

**Padroes PII redactados:**

| Padrao | Substituicao |
|--------|-------------|
| CPF formatado (`123.456.789-09`) | `000.000.000-XX` |
| CNPJ formatado (`12.345.678/0001-90`) | `00.000.000/0000-XX` |
| Email | `redacted@example.com` |
| Telefone (`(11) 99999-1234`) | `(00) 00000-0000` |
| CPF sem formatacao (11 digitos) | `00000000000` |
| CNPJ sem formatacao (14 digitos) | `00000000000000` |
| CEP (`01310-100`) | `00000-000` |
| RG formatado (`1.234.567-X`) | `0.000.000-X` |
| PIS/PASEP (`123.45678.90-1`) | `000.00000.00-0` |

**Sanitizacao de erros:** Mensagens de erro de excecoes tambem sao sanitizadas via _sanitize_pii_str() antes de serem incluidas no GraderResult.

**Resolucao de modelo (model_role):**
1. Se `spec.model_role` esta definido E `context.metadata["model_roles"]` contem essa role → usa o modelo mapeado
2. Senao, usa `spec.config["model"]`
3. Senao, usa `_DEFAULT_MODEL` (claude-sonnet-4-5-20250929)

Ativado via CLI: `--model-role grader=claude-haiku-3-5-20241022`

**GraderContext:** quando disponivel, LLM-judge inclui resultados de graders anteriores no prompt (ex: "CPF deu FAIL, avalie com isso em mente"). Isso permite que o juiz IA considere falhas de graders deterministicos na sua avaliacao.

**Regra operacional:** LLM-judge comeca como INFORMATIVE. Apos 50+ runs com auto-concordancia >= 0.90, promove a BLOCKING.

---

## 6. O Runner — fluxo de execucao

### Helpers de carga

- `load_task(yaml_path) -> Task` — carrega um YAML e valida contra o schema Pydantic
- `load_tasks_from_dir(tasks_dir, layer, tier) -> list[Task]` — carrega todos os YAMLs do diretorio, filtra por layer/tier

### Fluxo principal

```
load_task(yaml_path) -> Task
    |
    | (load_task filtra chaves privadas (_*) do config de graders)
    |
run_task(task, output, model_roles=None) -> TaskResult
    |
    effective_epochs = 1 se deterministico (short-circuit), senao task.epochs
    |
    Para cada epoch:
        _run_single_epoch(task, output, model_roles, extra_metadata)
            | Cria GraderContext com metadata (task_id, tenant_profile, model_roles)
            | Para cada grader em task.graders:
                grade(spec.type, output, task.expected, spec, context=ctx) -> GraderResult
                ctx acumula previous_results
            | _compute_score(grader_results, scoring_mode) -> float
        epoch_scores.append(score)
    |
    reducer_scores = {reducer: _reduce_scores(epoch_scores, reducer, threshold)}
    primary_score = reducer_scores[primary_reducer]
    passed = primary_score >= pass_threshold AND no required grader failed
```

### Modos de scoring (_compute_score)

**WEIGHTED:** media ponderada de todos os graders.
```
score = SUM(result.score * result.weight) / SUM(result.weight)
```

**BINARY:** todos passam ou nenhum passa.
```
score = 1.0 if ALL passed else 0.0
```

**HYBRID:** graders `required` sao binarios (se algum falha -> score 0.0); os opcionais sao weighted.
```
if any required failed -> 0.0
else -> weighted average of optional graders only
```

### Epochs e Score Reducers

Quando uma task define `epochs > 1`, o runner executa os graders N vezes e agrega os scores:

| Reducer | O que faz | Caso de uso |
|---------|-----------|-------------|
| MEAN | Media dos epoch scores | Default, melhor para estimativa geral |
| AT_LEAST_ONE (pass@k) | 1.0 se qualquer epoch passou, senao max | "Pelo menos uma vez conseguiu" |
| ALL_PASS (pass^k) | 1.0 se todos passaram, senao min | "Sempre consistente" |
| MAJORITY | 1.0 se maioria passou, senao mean | "Na maioria das vezes funciona" |
| MEDIAN | Mediana dos scores | Robusto a outliers |

**Short-circuit deterministico:** se todos os graders da task sao deterministicos (nao inclui `llm_judge`), `effective_epochs = 1` independente do configurado — nao faz sentido repetir funcoes puras.

**`primary_reducer`:** determina o score usado para decisao de passed/failed. Os demais reducers sao calculados para observabilidade (aparecem em `result.reducer_scores`).

### overall_score — media dos task scores

O overall_score do EvalRun e calculado como **media aritmetica** dos scores individuais das tasks:

```python
if run.task_results:
    run.overall_score = sum(tr.score for tr in run.task_results) / len(run.task_results)
```

Isso captura degradacao silenciosa que pass-rate (`tasks_passed / tasks_total`) esconderia.

### Tags union

Tags dos golden set cases sao coletadas como **uniao** de todos os cases:

```python
all_tags = sorted({t for c in cases for t in c.get("tags", [])})
```

### Protecoes do runner

- **KeyError em expected_output:** se um golden case nao tem `expected_output`, gera `GraderResult(grader_type="system", passed=False)` com mensagem descritiva em vez de crashar
- **Self-eval deepcopy:** `output = copy.deepcopy(case["expected_output"])` evita mutacao acidental
- **Reviewed_by warning:** emite warning para cases com `reviewed_by: null`
- **PLACEHOLDER detection:** fields com valor "PLACEHOLDER" sao sinalizados

### Gate classification (regression.py)

```python
def classify_gate(run, delta=None) -> GateResult:
    if delta and delta.has_regressions:
        return NO_GO_ABSOLUTE      # regressao detectada -> exit code 2
    if any required grader failed:
        return NO_GO                # grader obrigatorio falhou -> exit code 1
    if all passed:
        return GO                   # tudo ok -> exit code 0
    else:
        return CONDITIONAL_GO       # graders opcionais falharam -> exit code 0
```

### run_suite — execucao de suite completa

```python
def run_suite(
    tasks_dir: Path,
    outputs: dict[str, dict[str, Any]],
    layer: Layer | None = None,
    tier: Tier | None = None,
) -> EvalRun:
```

Carrega todas as tasks do diretorio (filtradas por layer/tier), roda cada task contra o output correspondente, computa score geral e gate_result. Retorna um `EvalRun` completo.

### Integracao com golden sets

O runner tem suporte nativo para golden sets via `run_suite_with_golden`:

```
run_suite_with_golden(tasks_dir, golden_dir, self_eval, layer, tier)
    |
    Para cada task:
        1. Extrai document_type do task (payload.document_type ou payload.skill)
        2. Carrega cases de golden/{document_type}/case_[0-9]*.json
        3. run_task_against_golden_set(task, cases, self_eval)
            | Para cada case:
                - expected = case["expected_output"]
                - output = deepcopy(expected) (se self_eval) ou {} (se real)
                - Roda graders contra output vs expected
            | Agrega scores
                - avg_score = media dos scores de todos os cases
                - all_passed = todos acima do threshold
```

**Self-eval mode (`--self-eval`):** usa o expected_output do golden set como output E como referencia. Sanity check — se os graders estao corretos, self-eval deve retornar score ~1.0 para todos os cases.

### CLI

Entry point: `gbr-eval` (registrado em pyproject.toml -> `gbr_eval.harness.runner:cli`)

```bash
# Rodar suite completa
gbr-eval run --suite tasks/product/

# Rodar task unica
gbr-eval run --task tasks/product/extraction/matricula_cpf.yaml

# Rodar com golden sets
gbr-eval run --suite tasks/product/ --golden-dir golden/

# Self-eval (sanity check)
gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval

# Filtrar por layer/tier
gbr-eval run --suite tasks/product/ --layer product --tier gate

# Comparar com baseline (regressao)
gbr-eval run --suite tasks/product/ --baseline-run runs/baseline.json

# Output JSON para arquivo
gbr-eval run --suite tasks/product/ --output-format json --output-file report.json

# Detectar tendencias
gbr-eval trends --runs-dir runs/ --min-consecutive 3

# Mapear modelo para role (ex: usar Haiku como grader em vez de Sonnet)
gbr-eval run --suite tasks/product/ --model-role grader=claude-haiku-3-5-20241022

# Multiplos roles
gbr-eval run --suite tasks/product/ --model-role grader=claude-haiku-3-5-20241022 --model-role reviewer=claude-sonnet-4-5-20250929

# Permitir endpoint interno (dev local)
gbr-eval run --task tasks/product/extraction/matricula_cpf.yaml --endpoint http://localhost:8000 --allow-internal

# Analisar runs historicos
gbr-eval analyze --runs-dir runs/ --top 10

# [ENGINEERING] Avaliar codigo de um repo local (local-first, antes do PR)
gbr-eval run --suite tasks/engineering/ --code-dir /caminho/para/repo-alvo/
```

**Protecao SSRF:** `--endpoint` resolve o hostname e bloqueia IPs internos (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16). Para desenvolvimento local, usar `--allow-internal`.

**Warning de roles nao utilizados:** se `--model-role` mapeia uma role que nenhum grader referencia via `model_role`, o CLI emite um warning.

Exit codes: 0 = GO/CONDITIONAL_GO, 1 = NO_GO, 2 = NO_GO_ABSOLUTE.

### Code Loader e avaliacao arquivo por arquivo (Engineering)

Para tasks de Camada E, o runner usa o `--code-dir` para carregar arquivos do repo alvo e passa cada arquivo individualmente para os graders. **Nao ha concatenacao** — cada arquivo e avaliado separadamente.

**Por que arquivo por arquivo, nao concatenado?**

Se o runner concatenasse todos os arquivos em uma string gigante e rodasse os graders sobre ela, perderia a informacao de origem: "qual arquivo violou qual regra?" A avaliacao por arquivo responde exatamente isso.

**Fluxo de uma task de Engineering com `--code-dir`:**

```
gbr-eval run --suite tasks/engineering/atom/ --code-dir ~/repos/atom-back-end/
    |
    Para cada task YAML em tasks/engineering/atom/:
        1. Le input.payload.repo ("atom-back-end") e scan_target ("**/*.py")
        2. Code Loader lista arquivos que batem com scan_target dentro de code-dir/
        3. Para cada arquivo encontrado:
            - Le o conteudo do arquivo
            - Roda os graders (pattern_required, pattern_forbidden, convention_check)
              com o conteudo do arquivo como input
            - Grava: arquivo X -> grader Y -> passed/failed com details
        4. Agrega: score do task = media dos scores por arquivo
           (cada arquivo com score individual no relatorio)
```

**O que o engenheiro ve no output:**

```
FAIL  engineering.atom.tenant_isolation
  app/api/endpoints/documents.py   score=0.0  [pattern_required: tenant_id MISSING]
  app/api/endpoints/users.py       score=1.0  OK
  app/services/document.py         score=0.0  [pattern_required: tenant_id MISSING]
  ...
  Aggregate: 2/3 files failing — score=0.33 (threshold=0.95)
```

Isso diz exatamente quais arquivos precisam de correcao, sem o engenheiro ter que procurar manualmente.

---

## 7. Golden sets — ground truth

### Estrutura de diretorio

```
golden/
├── {document_type}/
│   ├── metadata.yaml       # Definicao do skill, campos, pesos, status
│   ├── case_001.json       # Positivo padrao
│   ├── case_002.json       # ...
│   ├── case_005.json       # Ultimo positivo padrao
│   ├── case_101.json       # Confuser (documento errado)
│   ├── case_201.json       # Edge case (campos ausentes/incomuns)
│   └── case_202.json       # Edge case
```

### Taxonomia de cases (numeracao)

| Range | Categoria | Descricao |
|-------|-----------|-----------|
| 001-099 | Positivos | Documento correto, todos os campos presentes |
| 100-199 | Confusers | Documento errado (deve ser rejeitado/classificado diferente) |
| 200-299 | Edge cases | Documento correto mas com campos ausentes/incomuns |
| 300-399 | Degraded | Documento correto mas com OCR ruim/scan cortado |

### metadata.yaml — anatomia

```yaml
skill: matricula_v1
document_type: matricula
minimum_cases: 20              # meta final
current_cases: 8               # estado atual
annotator: diogo.dantas
status: seed_complete           # empty | seed_complete | production_ready

critical_fields:                # peso 3
  - numero_matricula
  - proprietario_cpf
  - onus
  - alienacao_fiduciaria

important_fields:               # peso 2
  - proprietario_nome
  - area_total

informative_fields:             # peso 1
  - endereco
  - comarca

field_weights:
  numero_matricula: 3
  proprietario_cpf: 3
  # ...
```

### case_NNN.json — anatomia

```json
{
  "case_number": 1,
  "document_hash": "sha256:PENDING_COMPUTE_FROM_PDF",
  "tags": ["seed", "pf", "negativa", "trt2", "cliente_a"],
  "annotator": "diogo.dantas",
  "reviewed_by": "claude_assistant",
  "created_at": "2026-04-18T20:00:00Z",
  "document_source": "internal:certidao_trabalhista:001",
  "notes": "Descricao textual do caso e suas particularidades",
  "expected_output": {
    "document_type": "certidao_trabalhista",
    "titular": "NOME DO TITULAR",
    "resultado": "negativa",
    "processos": [],
    "orgao_emissor": "Tribunal Regional do Trabalho da 2a Regiao (TRT-2)",
    "validade": "15/01/2026",
    "data_emissao": "16/07/2025",
    "codigo_verificacao": "ABC.123.456.789"
  },
  "citation": {
    "titular": {
      "page": 1,
      "excerpt": "Trecho do documento que fundamenta o valor"
    }
  }
}
```

**Nota:** cases sem `reviewed_by` geram warning no runner. O campo nao bloqueia execucao mas sinaliza cases nao revisados.

### Regras LGPD para golden sets

| Dado | Tratamento |
|------|-----------|
| CPF | `000.000.000-XX` (manter ultimos 2 digitos) |
| CNPJ | `00.000.000/0000-XX` |
| Raiz CNPJ | `XX.XXX.NNN` (manter 3 ultimos) |
| Nomes de pessoas | Substituir por ficticios (manter padrao) |
| Nomes de empresas (clientes reais) | Substituir (ex: BANCO PINE -> BANCO EXEMPLO S/A) |
| Enderecos | Substituir rua/numero, manter cidade/estado |
| Valores monetarios | Manter ordem de grandeza, alterar digitos |
| Tags | Nunca usar nome real do cliente (ex: "cliente_a" nao "banco_pine") |

Hash SHA-256 do documento original e armazenado para rastreabilidade sem expor o conteudo.

---

## 8. Task YAMLs — definicao de avaliacoes

Cada task YAML define O QUE avaliar, COM QUAIS graders, e QUAL threshold.

### Exemplo real: certidao_trabalhista_extraction.yaml

```yaml
task_id: extraction.certidao_trabalhista.fields
category: extraction
component: ai-engine
layer: product
tier: gate
tenant_profile: global
description: "Verifica extracao dos campos criticos de certidao trabalhista"

input:
  endpoint: /api/v1/extract
  payload:
    document_type: certidao_trabalhista
    skill: certidao_trabalhista_v1

expected:
  titular: "PLACEHOLDER"
  titular_cpf_cnpj: "PLACEHOLDER"
  resultado: "PLACEHOLDER"
  processos: "PLACEHOLDER"

graders:
  - type: field_f1
    field: titular
    weight: 3
    required: true
    config:
      severity: critical
  - type: exact_match
    field: resultado
    weight: 3
    required: true
    config:
      severity: critical
  - type: field_f1
    field: processos
    weight: 3
    required: true
    config:
      severity: critical
  - type: field_f1
    field: titular_cpf_cnpj
    weight: 3
    required: true
    config:
      severity: critical
  - type: field_f1
    field: orgao_emissor
    weight: 2
    config:
      severity: high
  - type: exact_match
    field: validade
    weight: 2
    config:
      severity: high

scoring_mode: hybrid
pass_threshold: 0.95
```

Os `expected` contem PLACEHOLDERs porque os valores reais vem dos golden sets em tempo de execucao (via `--golden-dir`). O task define QUAIS graders rodar e COM QUAL peso; o golden set fornece os VALORES esperados.

### Inventario de tasks (48 total)

| Categoria | Tasks | Count |
|-----------|-------|-------|
| Classification | matricula, contrato_social, cnd, procuracao, certidao_trabalhista, balanco + confusers | 11 |
| Extraction | matricula_cpf, contrato_social, cnd, procuracao, certidao_trabalhista, balanco | 6 |
| Citation | matricula, contrato_social, cnd, procuracao, certidao_trabalhista, balanco | 6 |
| Decision | score_aprovado | 1 |
| Cost | journey_cost_limit | 1 |
| Latency | sla_p95_limit | 1 |
| Engineering (atom-back-end) | tenant_id_filter, rbac_enforcement, audit_log, sensitive_data_filter, api_versioning | 5 |
| Engineering (engine-billing) | decimal_not_float, idempotency_key, audit_trail, reconciliation | 4 |
| Engineering (engine-integracao) | configurable_timeout, no_credentials_in_code, retry_backoff, circuit_breaker, provider_isolation | 5 |
| Engineering (garantia-ia) | prompt_versioning, pii_sanitization, output_schema, cost_tracking | 4 |
| Engineering (notifier) | template_approval, idempotency, lgpd_opt_out, rate_limiting | 4 |

**Engineering tasks** avaliam codigo (Camada E), nao outputs de IA. Usam graders `pattern_required`, `pattern_forbidden`, e `convention_check`.

### Anatomia de uma Engineering task

```yaml
task_id: eng.atom.tenant_id_filter
category: classification
component: atom-back-end
layer: engineering
tier: gate
description: "Toda query deve filtrar por tenant_id"
eval_owner: diogo.dantas            # responsavel atual pela avaliacao
eval_cadence: per-pr                # frequencia recomendada

input:
  payload:
    repo: atom-back-end             # qual repo escanear (deve bater com --code-dir)
    scan_target: "**/*.py"          # glob de arquivos a avaliar

expected:
  convention: tenant_id_required

graders:
  - type: pattern_required
    field: tenant_id_usage
    required: true
    config:
      pattern: 'tenant_id'
      file_key: content

scoring_mode: binary
pass_threshold: 1.0
```

**Nota:** Engineering tasks nao tem `endpoint` no bloco `input` — o Code Loader e ativado via flag `--code-dir` na CLI, nao via endpoint field. O runner detecta automaticamente que se trata de uma task de engineering pela presenca de `input.payload.repo` e `input.payload.scan_target`.

**`eval_owner`** e o responsavel atual pela avaliacao. A evolucao para `eval_owner_role` (role-based, agnostico a nomes) esta planejada mas ainda nao implementada — sera feita quando o modulo de users com permissoes por role for criado no frontend.

**`input.payload.repo`** e `scan_target` trabalham juntos com `--code-dir`: o runner procura arquivos que batem com `scan_target` dentro do diretorio `--code-dir/repo/` (ou diretamente em `--code-dir/` se o path ja aponta para o repo correto).

---

## 9. 5 Skills P0 — golden sets anotados

### Status atual (Track A — Seed Round + Edge/Confuser)

| Skill | Tipo doc (sistema) | Cases | Status | Campos criticos |
|-------|--------------------|-------|--------|-----------------|
| matricula_v1 | 135 | 8 (5+2+1) | seed_complete | numero_matricula, proprietario_cpf, onus (array), alienacao_fiduciaria |
| contrato_social_v1 | 130 | 8 (5+2+1) | seed_complete | cnpj, razao_social, socios (array), capital_social, poderes |
| cnd_v1 | 96 | 8 (5+2+1) | seed_complete | tipo_certidao, numero, orgao_emissor, validade, status |
| procuracao_v1 | 146 | 8 (5+2+1) | seed_complete | outorgante, outorgante_cpf, outorgado, poderes_especificos, validade |
| certidao_trabalhista_v1 | 113 | 8 (5+2+1) | seed_complete | titular, resultado, processos (array), orgao_emissor |
| ~~balanco_v1~~ | 293 | 0 | blocked | Substituido por certidao_trabalhista (0 docs disponiveis) |

### Processo de anotacao

1. O especialista responsavel identifica documentos reais no sistema de producao (Django Admin backoffice)
2. Le o campo `analise_ia` (JSON com extracao do ai-engine) e o PDF original
3. Anota expected_output com valores corretos e citation linking
4. Anonimiza PII conforme regras LGPD
5. Claude assiste como reviewer (never as validator — CLO valida)
6. Case e comitado com tags descritivas, hash pendente, e metadata completo

### Particularidade: certidao trabalhista positiva

Cases 004 e 005 sao certidoes POSITIVAS (com processos trabalhistas). O campo `processos` tem dois formatos reais que coexistem:

**Formato 1 — agregado por vara (TRT-10):**
```json
{"vara": "1a Vara do Trabalho de Araguaina - TO", "quantidade": 11}
```

**Formato 2 — individual com numero do processo (TRT-2):**
```json
{"vara": "2a Vara do Trabalho de Santo Andre", "numero": "1000508-38.2025.5.02.0432"}
```

**Decisao pendente:** o grader field_f1 precisa tratar ambos os formatos, ou o schema deve ser padronizado. Recomendacao: grader polimorfico (a realidade e polimorfica).

---

## 10. Regressao e tendencias

### Regressao (regression.py)

Compara dois EvalRuns (baseline vs current):

```python
@dataclass
class RegressionDelta:
    baseline_run_id: str         # ID do run de referencia
    current_run_id: str          # ID do run atual
    newly_failing: list[str]     # tasks que passavam e agora falham
    newly_passing: list[str]     # tasks que falhavam e agora passam
    new_tasks: list[str]         # tasks novas (sem baseline)
    removed_tasks: list[str]     # tasks removidas
    score_deltas: dict[str, float]
    stable_pass: list[str]
    stable_fail: list[str]
    overall_delta: float
    has_regressions: bool        # True se newly_failing > 0 OR degraded_scores > 0
    degraded_scores: list[str]   # tasks que PASSAM mas tiveram queda significativa de score
```

**degraded_scores:** captura degradacao silenciosa. Uma task caindo de 1.0 para 0.6 com threshold 0.5 nao aparece em `newly_failing` (ainda passa), mas e um problema de qualidade real. Configuravel via `score_degradation_threshold` (default 0.05).

```python
delta = compare_runs(baseline, current, score_degradation_threshold=0.05)
# Se task.A caiu de 1.0 para 0.90 (delta -0.10 > threshold 0.05):
#   delta.degraded_scores == ["task.A"]
#   delta.has_regressions == True
```

Regras:
- So detecta degradacao em tasks que PASSAM em ambos os runs
- Tasks que falham em qualquer run sao capturadas por `newly_failing`

Uso via CLI:
```bash
gbr-eval run --suite tasks/product/ --baseline-run runs/2026-04-18.json
```

Se `has_regressions = True` -> GateResult = NO_GO_ABSOLUTE (exit code 2).

### Tendencias (trends.py)

Detecta score em queda ou subida consistente ao longo de N runs:

```python
@dataclass
class TrendAlert:
    task_id: str
    metric: str              # "score"
    direction: str           # "declining", "improving", ou "declining_trend"
    consecutive_runs: int
    current_value: float
    threshold: float         # pass_threshold do task
    distance_to_threshold: float
```

**Dois mecanismos de deteccao:**

1. **Monotonico:** detecta N scores consecutivos estritamente declinantes (1.0 -> 0.9 -> 0.8). Direction: `"declining"` ou `"improving"`.

2. **Slope-based:** detecta tendencia negativa ruidosa que deteccao monotonica perde. Usa `_linear_slope()` (regressao linear least-squares) sobre janela de N runs. Direction: `"declining_trend"`.

```python
alerts = detect_trends(runs, min_consecutive=3, slope_window=5, slope_threshold=-0.02)
```

Exemplo — scores `[0.98, 0.94, 0.96, 0.92, 0.93]`:
- Monotonica: nao detecta (ultimos 3 sao `[0.96, 0.92, 0.93]` — nao estritamente declinante)
- Slope: detecta (slope < -0.02 sobre janela de 5)

**Anti-duplicacao:** quando deteccao monotonica ja emitiu alerta para uma task, slope NAO emite alerta adicional para a mesma task.

Uso via CLI:
```bash
gbr-eval trends --runs-dir runs/ --min-consecutive 3
```

---

## 11. Relatorios (reporter.py)

4 formatos de output:

| Formato | Funcao | Uso |
|---------|--------|-----|
| Console | `console_report(run, delta)` | Terminal, debug local |
| JSON | `json_report(run, output_path)` | Armazenamento, API, dashboards |
| JUnit XML | `junit_xml_report(run, output_path)` | GitHub Actions, Jenkins |
| CI Summary | `ci_summary(run)` | Uma linha para CI annotations |

---

## 12. Calibracao (iaa.py)

Cohen's kappa para medir concordancia entre anotadores:

```python
result = cohens_kappa(annotator_a_labels, annotator_b_labels, threshold=0.75)
# result.kappa = 0.87
# result.interpretation = "almost_perfect"
# result.calibrated = True (kappa >= threshold)
```

Escala de Landis & Koch: poor (< 0.00), slight (0.00-0.20), fair (0.21-0.40), moderate (0.41-0.60), substantial (0.61-0.80), almost_perfect (0.81-1.00).

---

## 13. CI Pipeline

### .github/workflows/ci.yml

```yaml
# Simplificado — 2 jobs
jobs:
  quality:
    steps:
      - uv sync --all-extras
      - uv run ruff check .
      - uv run mypy src/
      - uv run pytest --cov=src/gbr_eval --cov-fail-under=80

  eval-gate:
    needs: quality
    steps:
      - uv sync --all-extras
      - uv run gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval --output-format json --output-file eval-report.json
      - python3 -c "... valida resultados ..."
      - Upload eval-report.json como artifact
```

**Seguranca CI:** o step de validacao usa env vars (`$REPORT_PATH` via `env:` block) em vez de interpolacao direta no `python3 -c` — evita injection.

### .github/actions/gbr-eval-gate/action.yml

GitHub Action reutilizavel para repos alvo consumirem o eval como gate no PR. Aceita inputs para suite path, golden dir, e baseline run.

Testes que dependem de `ANTHROPIC_API_KEY` usam `pytest.mark.skipif` — nunca quebram o CI por falta de env var.

---

## 14. Frontend — Admin Panel

O frontend e uma aplicacao Next.js 16 com SQLite local que serve como painel de administracao e observabilidade do eval.

### Stack

- **Framework:** Next.js 16 (Turbopack)
- **Runtime:** React 19
- **DB:** SQLite via better-sqlite3 + Drizzle ORM (23 tabelas, WAL mode)
- **UI:** shadcn/ui + Tailwind CSS
- **Auth:** middleware com comparacao timing-safe (HMAC via Web Crypto) + fail-closed quando ADMIN_API_TOKEN nao configurado (retorna 500)

### Modulos (39 paginas, 57 API routes)

| Modulo | O que faz |
|--------|-----------|
| Dashboard | KPIs, recent runs, active alerts, quick links |
| Runs | Import, view, trends, comparison, postmortem |
| Golden Sets | CRUD, import/export JSON, case versioning, PII redaction |
| Tasks | Definicao de tasks, graders, thresholds |
| Rubrics | CRUD, A/B testing, concordance tracking, promotion lifecycle |
| Conventions | Rules, coverage matrix, import de CLAUDE.md |
| Calibration | Sessions, annotations, disagreements, Cohen's kappa |
| Contracts | Schema snapshots, version history, OpenAPI import, drift detection |
| Skills | Skill definitions, field schemas, criticality |
| Alerts | Score drops, regressions, trend declines |

### Webhook para CI

`POST /api/runs/webhook` com Bearer token auth permite ingestao de eval runs diretamente do CI pipeline.

### Setup frontend

```bash
cd frontend && pnpm install
pnpm dev          # dev server (port 3000)
pnpm type-check   # TypeScript check
pnpm db:push      # apply DB schema
```

---

## 15. Como adicionar um novo grader

1. Criar arquivo em `src/gbr_eval/graders/` (ou adicionar ao existente)
2. Implementar o Protocol:

```python
from gbr_eval.graders.base import register_grader
from gbr_eval.harness.models import GraderResult, GraderSpec

@register_grader("meu_grader")
class MeuGrader:
    def grade(self, output: dict, expected: dict, spec: GraderSpec) -> GraderResult:
        field = spec.field
        valor_output = output.get(field)
        valor_esperado = expected.get(field)

        passed = (valor_output == valor_esperado)
        return GraderResult(
            grader_type="meu_grader",
            field=field,
            passed=passed,
            score=1.0 if passed else 0.0,
            weight=spec.weight,
            required=spec.required,
        )
```

3. Garantir que o modulo e importado em `src/gbr_eval/graders/__init__.py`
4. Escrever testes em `tests/graders/`
5. Usar em tasks via `type: meu_grader`

**Regras:** graders sao funcoes puras (mesma entrada -> mesma saida). Excecao unica: LLM-judge. Nunca hardcodar thresholds dentro do grader — receber via `spec.config`.

### Como adicionar um grader context-aware

Para graders que precisam dos resultados de graders anteriores (como LLM-judge):

```python
@register_grader("meu_grader_contextual", context_aware=True)
class MeuGraderContextual:
    def grade(self, output: dict, expected: dict, spec: GraderSpec, *, context: GraderContext | None = None) -> GraderResult:
        # Acessar resultados anteriores
        if context and context.previous_results:
            previous_failed = [r for r in context.previous_results if not r.passed]
            # ... usar na avaliacao
        
        # Acessar model_roles
        if context:
            model_roles = context.metadata.get("model_roles", {})
            model = model_roles.get(spec.model_role, "default-model")
        ...
```

**Nota:** `context_aware=True` no decorator e obrigatorio — sem ele, o dispatcher nao passa `context` ao grader.

---

## 16. Como adicionar um novo skill (golden set)

1. Criar diretorio `golden/{document_type}/`
2. Criar `metadata.yaml` com campos, pesos e status
3. Anotar cases como `case_001.json`, `case_002.json`, etc.
4. Incluir pelo menos 1 confuser (`case_101.json`) e 1 edge case (`case_201.json`)
5. Anonimizar PII ANTES de commitar
6. Criar tasks em `tasks/product/` referenciando o document_type
7. Rodar self-eval para validar:

```bash
gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval
```

**Quem anota:** o especialista designado para cada skill. Claude assiste, nunca valida. Golden sets sao a ground truth do sistema — zero tautologia.

---

## 17. Regras de decisao deterministicas

O motor de decisao da GarantiaBR (Athena) NAO usa LLM. E deterministico:

```
Score >= 0.90 AND zero critical non-conforming -> aprovado
Score >= 0.70 AND critical conforming AND >= 1 warning -> aprovado_com_ressalvas
Any critical non-conforming -> reprovado
>= 3 critical fields nao_verificavel -> inconclusivo
```

Score = SUM(field_weight * field_confidence) / SUM(critical_weights)

Pesos por severidade: CRITICAL = 3, IMPORTANT = 2, INFORMATIVE = 1.

O eval verifica se essas regras produzem o resultado correto contra golden sets com decisoes pre-anotadas.

---

## 18. O que foi feito (estado atual — 2026-04-20)

### Framework (codigo)

| Modulo | Arquivos | Status |
|--------|----------|--------|
| Graders | 5 (base + deterministic + field_f1 + engineering + model_judge) | 12 graders implementados, testados |
| Solvers | 3 (base + models + passthrough) | Solver Protocol + AgentTrace models, testados |
| Harness | 11 (models + runner + async_runner + async_suite_runner + task_helpers + code_loader + reporter + regression + trends + analyzer + client) | Implementado, testado |
| Shared | 1 (_shared.py) | Utilitarios compartilhados |
| Calibracao | 1 (iaa.py) | Implementado, testado |
| Contracts | 1 (validator.py) | Implementado |
| CLI | runner.py (Click) | 2 comandos: `run`, `trends` |
| CI | ci.yml + action.yml | 2 jobs: quality + eval-gate (SHA-pinned actions) |
| Frontend | Next.js 16 (204 arquivos TS) | 39 paginas, 57 API routes, 23 tabelas |
| Tools | 4 scripts | generate_synthetic, generate_all_synthetic, compute_hashes, sync_frontend |

533 testes passando. ruff clean. mypy clean. Cobertura >= 80%.

### Golden sets (Track A — Seed + Edge + Confuser)

40 cases anotados por especialistas em 5 skills P0 (8 cases cada). Cada case inclui expected_output completo, citation linking, tags descritivas, metadata de anotacao, e anonimizacao LGPD validada. Taxonomia: positivos (001-099), confusers (100-199), edge cases (200-299).

### Tasks

48 task YAMLs: 26 em `tasks/product/` (classification 11, extraction 6, citation 6, cost 1, latency 1, decision 1) + 22 em `tasks/engineering/` (atom-back-end 5, engine-billing 4, engine-integracao 5, garantia-ia 4, notifier 4).

### Auditorias independentes (6 rodadas)

| Rodada | Agentes | Findings | Status |
|--------|---------|----------|--------|
| Audit #1 | 3 | Iniciais | Todos corrigidos |
| Audit #2 | 3 | Follow-up | Todos corrigidos |
| Audit #3 | 3 (architect, code-reviewer, security-reviewer) | 25 findings | Todos corrigidos, 37 novos testes |
| Audit #4 | 3 (fresh) | ~15 findings | Avaliados |
| Audit #5 | Independente | 15 findings (1 CRITICAL, 6 HIGH, 8 MEDIUM) | Todos corrigidos, 26 novos testes |
| Audit #6 | Re-audit (seguranca) | 4 imediatos + 3 medios | Imediatos corrigidos, 533 testes |

Hardening from audits: overall_score mean, field_f1 spec.field priority, degraded_scores, slope trends, ReDoS guard, PII recursive walk, target_threshold validation, tags union, KeyError protection, CI injection fix, dependency upper bounds, ContextAwareGrader Protocol, _CONTEXT_AWARE registry, model_roles via GraderContext, shared _run_single_epoch, multi-epoch async_runner, SSRF protection, timing-safe auth, fail-closed middleware, PII RG/PIS patterns, error message sanitization, YAML config stripping, SSRF redirect bypass prevention (_SSRFSafeRedirectHandler), IPv4-mapped IPv6 detection, CI SHA-pinned actions, narrowed exception handling in runner, max_retries cap (10).

### Eval runs gravados

3 runs em `runs/`: baseline (2026-04-18), self-eval (2026-04-18, 2026-04-19).

---

## 19. O que falta fazer

### Prioridade 1 — Expansao de golden sets

Meta: >= 150 cases totais (atual: 40 seed). Proximos passos:
1. Gerar positivos sinteticos adicionais via `tools/generate_synthetic.py`
2. Gerar confusers e edge cases adicionais
3. CLO revisa amostra de 20-30% antes de commitar

### Prioridade 2 — SHA-256 hashes dos PDFs

Hashes pendentes (`sha256:PENDING_COMPUTE`) em todos os 40 cases. O script `tools/compute_hashes.py` esta pronto — precisa acesso aos PDFs do backoffice.

### Prioridade 3 — CI cross-repo (gbr-engines)

Eval-gate funciona no CI do gbr-eval (self-eval). Falta conectar ao CI do gbr-engines:
1. Workflow cross-repo que faz checkout de ambos os repos
2. Roda eval runner contra outputs reais do ai-engine
3. Baseline automatico via GitHub Artifacts

### Prioridade 4 — Online eval em staging (Fase 5 do plano)

Runner com HTTP client para chamadas reais ao ai-engine. Flag `--record` para salvar outputs. Comando `gbr-eval analyze` para feedback loop.

### Prioridade 5 — LLM-judge calibracao

Apos 50+ runs, medir auto-concordancia do LLM-judge. Se >= 0.90, promover de INFORMATIVE a BLOCKING.

### Prioridade 6 — Formato de processos

O campo `processos` em certidao trabalhista tem dois formatos reais (agregado vs individual). Decidir se o grader trata ambos (polimorfico) ou se o schema e padronizado.

### Issues conhecidos (nao bloqueantes)

- CSP no frontend permite `unsafe-inline` e `unsafe-eval` — a ser tratado quando Next.js estiver em producao
- `\b\d{11}\b` no PII sanitizer pode ter over-redaction em numeros genericos de 11 digitos
- field_f1 `_compare_list` sem credito parcial para match parcial de itens

---

## 20. Invariantes — NUNCA violar

1. **Graders sao funcoes puras** (excecao: LLM-judge, documentada)
2. **Zero tautologia** — golden sets anotados por humano, nunca gerados automaticamente
3. **Contract testing via snapshots** — mudanca no schema do repo alvo quebra o CI aqui
4. **Separacao build-time vs operate-time** — mesmos graders, configs diferentes
5. **Schema wide, implementation narrow** — schemas cobrem 4 camadas, implementacao atual e engineering + product
6. **LLM-judge: informative primeiro, blocking depois** — baseado em dados, nao palpite
7. **LGPD** — nunca commitar PII real, nunca logar conteudo de golden sets em CI output
8. **Compliance > Seguranca > Correcao > Features > Polish**
9. **overall_score = media dos task scores** (nunca pass-rate)
10. **Tags = uniao** de todos os cases no golden set

---

## 21. Referencia rapida

### Caminhos importantes

| O que | Onde |
|-------|------|
| Graders | `src/gbr_eval/graders/` |
| Models | `src/gbr_eval/harness/models.py` |
| Runner | `src/gbr_eval/harness/runner.py` |
| Async Runner | `src/gbr_eval/harness/async_runner.py` |
| Task helpers | `src/gbr_eval/harness/task_helpers.py` |
| Regression | `src/gbr_eval/harness/regression.py` |
| Trends | `src/gbr_eval/harness/trends.py` |
| Solvers | `src/gbr_eval/solvers/` |
| RFC Solver | `docs/RFC-solver-pattern.md` |
| Tasks (product) | `tasks/product/` |
| Tasks (engineering) | `tasks/engineering/` |
| Tools | `tools/` |
| Golden sets | `golden/` |
| Testes | `tests/` |
| CI | `.github/workflows/ci.yml` |
| CI Action | `.github/actions/gbr-eval-gate/action.yml` |
| Frontend | `frontend/` |
| Eval runs | `runs/` |
| Docs | `docs/` |

### Comandos do dia a dia

```bash
# Setup
uv sync --all-extras

# Rodar testes
uv run pytest

# Lint + types
uv run ruff check . && uv run mypy src/

# Self-eval dos golden sets
gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval

# Cobertura
uv run pytest --cov=src/gbr_eval --cov-report=term-missing

# [ENGINEERING] Eval local de codigo antes do PR (local-first)
# Substitua /caminho/para/repo-alvo/ pelo path real do repo
gbr-eval run --suite tasks/engineering/ --code-dir /caminho/para/repo-alvo/

# [ENGINEERING] Avaliar apenas as tasks de um repo especifico
gbr-eval run --suite tasks/engineering/atom/ --code-dir ~/repos/atom-back-end/
gbr-eval run --suite tasks/engineering/billing/ --code-dir ~/repos/engine-billing/
gbr-eval run --suite tasks/engineering/integracao/ --code-dir ~/repos/engine-integracao/

# Frontend
cd frontend && pnpm install && pnpm dev
```

### Autonomia

| Pode fazer sem aprovacao | Pedir aprovacao | Bloqueado |
|--------------------------|-----------------|-----------|
| Criar/editar graders, tasks, testes, docs | Alterar thresholds | Validar golden sets (role: product) |
| Rodar testes, lint, mypy | Adicionar grader type | Decidir blocking vs informative |
| Rodar eval local com `--code-dir` (engineering) | Modificar models.py | Push direto em main |
| Criar branches | Abrir PR | Commitar PII |
| Consultar Jira/Confluence | Instalar dependencias | Definir convencoes de engenharia (role: technology) |
| | Definir criterios de qualidade de produto (role: product) | |

**Nota sobre ownership por role:** a coluna "Bloqueado" inclui decisoes que pertencem a um role especifico — nao significa que ninguem pode fazer, mas que apenas o role responsavel pode. Engenheiros com role `technology` podem definir convencoes; com role `product`, podem validar golden sets.
