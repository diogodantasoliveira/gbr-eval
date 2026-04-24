# Plano: gbr-eval Multi-Projeto

> **Problema:** O gbr-eval foi construído como projeto único flat. Tasks, golden sets, runs e contracts vivem em diretórios raiz sem namespace. Com a entrada do projeto Caixa (e futuros Itaú, Bradesco, Pine, etc.), a estrutura atual não escala — nomes de document_type colidem, runs se misturam, e o frontend não sabe de qual projeto veio cada resultado.

> **Meta:** Suportar N projetos isolados no mesmo repositório, com zero breaking change para os artefatos existentes (que viram o projeto "default" ou "gbr-engines").

---

## 1. Estado Atual — Acoplamentos Identificados

### 1.1 Estrutura de diretórios (flat, sem namespace)

```
gbr-eval/
├── tasks/
│   ├── product/           # 31 tasks — projeto implícito "gbr-engines"
│   └── engineering/       # 139+ tasks
├── golden/                # 5 doc types, 40 cases
│   ├── matricula/
│   ├── contrato_social/
│   └── ...
├── contracts/schemas/     # 10 schemas snapshot
├── runs/                  # 44 runs históricos (flat)
```

### 1.2 Código acoplado ao layout flat

| Arquivo | Linha | Acoplamento |
|---------|-------|-------------|
| `src/gbr_eval/harness/models.py:104` | `Task` model | Sem campo `project` |
| `src/gbr_eval/harness/models.py:168` | `EvalRun` model | Sem campo `project` |
| `src/gbr_eval/harness/runner.py:107` | `load_tasks_from_dir()` | Sem filtro por projeto |
| `src/gbr_eval/harness/runner.py:320` | `load_golden_cases()` | `golden_dir / document_type` sem namespace |
| `src/gbr_eval/harness/runner.py:346` | `_extract_document_type()` | Retorna "matricula" sem projeto |
| `src/gbr_eval/harness/runner.py:867` | CLI `run` command | Sem `--project` |
| `src/gbr_eval/harness/reporter.py:19` | `console_report()` | Sem projeto no output |
| `tools/sync_frontend.py:23-26` | `GOLDEN_DIR`, `TASKS_DIR` | Hardcoded para raiz |
| `tools/generate_all_synthetic.py:32` | `ROOT / "golden"` | Sem namespace |
| `tools/check_contract_drift.py:16` | `SCHEMAS_DIR` | Sem namespace |

---

## 2. Design Proposto

### 2.1 Princípio: Convenção sobre configuração

Em vez de arquivo de config complexo, usar **convenção de diretório**:

```
gbr-eval/
├── projects/
│   ├── gbr-engines/           # Projeto existente (migrado)
│   │   ├── tasks/
│   │   │   ├── product/
│   │   │   └── engineering/
│   │   ├── golden/
│   │   │   ├── matricula/
│   │   │   ├── contrato_social/
│   │   │   └── ...
│   │   ├── contracts/
│   │   │   └── schemas/
│   │   ├── runs/
│   │   └── project.yaml       # Metadados do projeto
│   │
│   ├── caixa/                 # Projeto novo
│   │   ├── tasks/
│   │   │   ├── product/
│   │   │   │   ├── classification/
│   │   │   │   ├── extraction/
│   │   │   │   ├── fraud-scoring/
│   │   │   │   ├── rules-simple/
│   │   │   │   ├── rules-composite/
│   │   │   │   ├── consulta-externa/
│   │   │   │   └── jornada/
│   │   │   └── engineering/
│   │   ├── golden/
│   │   │   ├── rg/
│   │   │   ├── cnh/
│   │   │   ├── holerite/
│   │   │   └── ...
│   │   ├── contracts/
│   │   │   └── schemas/
│   │   ├── runs/
│   │   └── project.yaml
│   │
│   └── itau/                  # Futuro
│       └── ...
│
├── src/                       # Framework (inalterado na estrutura)
├── tests/
├── docs/
└── tools/
```

### 2.2 `project.yaml` — Metadados do projeto

Cada projeto tem um arquivo de metadados na raiz:

```yaml
project_id: caixa
name: "BPO CAIXA Econômica Federal"
client: "CAIXA"
owner: "diogo.dantas"
created_at: "2026-04-24"
status: active                  # active | archived | draft

document_types:
  - rg
  - cnh
  - selfie
  - matricula
  - contrato_social
  # ... 32 tipos

layers:
  - product
  - engineering
  - operational
  - compliance

metadata:
  edital: "Pregão Eletrônico XXX/2026"
  vigencia: "24 meses"
  volume_anual: 25900000
```

---

## 3. Mudanças no Código

### 3.1 Models (`models.py`)

**Adicionar campo `project` a `Task` e `EvalRun`:**

```python
class Task(BaseModel):
    task_id: str
    project: str = "default"        # ← NOVO
    category: Category
    component: str
    layer: Layer
    # ... resto inalterado
```

```python
class EvalRun(BaseModel):
    run_id: str
    project: str = "default"        # ← NOVO
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # ... resto inalterado
```

**Por que `default` como fallback:** Tasks YAML existentes que não têm campo `project` continuam funcionando sem mudança — são do projeto "default" (ou "gbr-engines" após migração).

**Retrocompatibilidade:** O field tem default, então:
- YAMLs existentes sem `project:` → parseia como `project="default"`
- YAMLs novos com `project: caixa` → parseia como `project="caixa"`
- JSON de runs antigos sem `project` → deserializa como `project="default"`

### 3.2 Runner (`runner.py`)

**3.2.1 `load_task()` — ler campo project:**

```python
def load_task(path: Path) -> Task:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    # ... existing parsing ...
    task = Task(
        task_id=raw["task_id"],
        project=raw.get("project", "default"),   # ← NOVO
        category=Category(raw["category"]),
        # ... resto inalterado
    )
    return task
```

**3.2.2 `load_tasks_from_dir()` — filtro por projeto:**

```python
def load_tasks_from_dir(
    directory: Path,
    layer: Layer | None = None,
    tier: Tier | None = None,
    project: str | None = None,          # ← NOVO
) -> list[Task]:
    tasks: list[Task] = []
    for yaml_file in sorted(directory.rglob("*.yaml")):
        task = load_task(yaml_file)
        if layer and task.layer != layer:
            continue
        if tier and task.tier != tier:
            continue
        if project and task.project != project:  # ← NOVO
            continue
        tasks.append(task)
    return tasks
```

**3.2.3 `load_golden_cases()` — namespace por projeto:**

```python
def load_golden_cases(
    golden_dir: Path,
    document_type: str,
    tags: list[str] | None = None,
) -> list[dict[str, Any]]:
    skill_dir = golden_dir / document_type
    # ← Sem mudança na assinatura. O caller passa golden_dir já com namespace:
    #    golden_dir = projects_root / project_id / "golden"
    # ... resto inalterado
```

A mudança é no **caller**, não na função. O CLI resolve o path:

```python
if project != "default":
    golden_dir = projects_root / project / "golden"
    suite_dir = projects_root / project / "tasks"
```

**3.2.4 CLI — adicionar `--project`:**

```python
@click.option("--project", default="default",
              help="Project ID (e.g., caixa, itau). Auto-resolves tasks/golden dirs.")
def run(
    # ... existing params ...
    project: str,
):
    projects_root = Path("projects")

    # Auto-resolve paths se project != default
    if project != "default" and suite is None and task_path is None:
        suite = projects_root / project / "tasks"
        if not suite.exists():
            click.echo(f"Project directory not found: {suite}", err=True)
            raise SystemExit(EXIT_RUNTIME_ERROR)

    if project != "default" and golden_dir is None:
        golden_dir = projects_root / project / "golden"
```

**Comportamento:**
- `gbr-eval run --project caixa` → auto-resolve para `projects/caixa/tasks/` e `projects/caixa/golden/`
- `gbr-eval run --suite tasks/product/` → compatível com layout antigo (default)
- `gbr-eval run --project caixa --suite custom/path/` → project metadata + custom path

**3.2.5 CLI — adicionar `--project` a `analyze`, `trends`, `scores`:**

```python
@click.option("--project", default="default")
def analyze(project: str, runs_dir: Path | None, ...):
    if runs_dir is None and project != "default":
        runs_dir = Path("projects") / project / "runs"
```

### 3.3 Reporter (`reporter.py`)

**Adicionar projeto ao output:**

```python
def console_report(run: EvalRun, delta: RegressionDelta | None = None) -> str:
    lines = [
        f"{'='*60}",
        f"  Eval Run: {run.run_id[:8]}",
        f"  Project: {run.project}",     # ← NOVO
        f"  Layer: {run.layer.value}  |  Tier: ...",
```

```python
def json_report(run: EvalRun, output_path: Path | None = None) -> str:
    data = run.model_dump(mode="json")
    # project já está incluído porque é campo do EvalRun
```

### 3.4 Sync Frontend (`sync_frontend.py`)

```python
@click.option("--project", default="default")
def sync(project: str, base_url: str, ...):
    if project == "default":
        golden_dir = ROOT / "golden"
        tasks_dir = ROOT / "tasks" / "product"
        eng_dir = ROOT / "tasks" / "engineering"
    else:
        project_root = ROOT / "projects" / project
        golden_dir = project_root / "golden"
        tasks_dir = project_root / "tasks" / "product"
        eng_dir = project_root / "tasks" / "engineering"
```

### 3.5 Runs — auto-organização por projeto

```python
if output_file is None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if project != "default":
        output_dir = Path("projects") / project / "runs"
    else:
        output_dir = Path("runs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{layer_enum.value}_{timestamp}.json"
```

---

## 4. Migração dos Artefatos Existentes

### 4.1 Estratégia: symlinks para retrocompatibilidade

Em vez de mover arquivos (quebraria imports, git history, CI):

```bash
# Criar estrutura multi-projeto
mkdir -p projects/gbr-engines

# Mover artefatos
mv tasks projects/gbr-engines/tasks
mv golden projects/gbr-engines/golden
mv contracts projects/gbr-engines/contracts
mv runs projects/gbr-engines/runs

# Symlinks para retrocompatibilidade
ln -s projects/gbr-engines/tasks tasks
ln -s projects/gbr-engines/golden golden
ln -s projects/gbr-engines/contracts contracts
ln -s projects/gbr-engines/runs runs

# Criar project.yaml
cat > projects/gbr-engines/project.yaml << 'EOF'
project_id: gbr-engines
name: "GarantiaBR Platform"
client: "GarantiaBR"
owner: "diogo.dantas"
created_at: "2026-04-18"
status: active
EOF
```

**Resultado:**
- `gbr-eval run --suite tasks/product/` → funciona via symlink (retrocompatível)
- `gbr-eval run --project gbr-engines` → funciona via resolução direta
- `gbr-eval run --project caixa` → funciona via resolução direta

### 4.2 Fase de transição

1. **Semana 1:** Adicionar campo `project` aos models com default "default" → zero breaking change
2. **Semana 1:** Adicionar `--project` ao CLI → opt-in, não obrigatório
3. **Semana 2:** Criar `projects/caixa/` para o projeto novo
4. **Semana 3:** Migrar `tasks/`, `golden/`, etc. para `projects/gbr-engines/` com symlinks
5. **Semana 4:** Atualizar CI para usar `--project gbr-engines`
6. **Semana 5:** Remover symlinks após confirmar que tudo funciona

---

## 5. Impacto nos Testes

### 5.1 Testes existentes (758 passando)

**Zero breaking change** porque:
- Campo `project` tem default `"default"` → YAMLs de teste sem campo `project` continuam parseando
- `load_tasks_from_dir()` sem filtro de projeto continua retornando tudo
- Golden sets carregados por path relativo continuam funcionando

### 5.2 Testes novos necessários

```python
# tests/harness/test_multi_project.py

def test_load_task_with_project():
    """Task YAML com campo project parseia corretamente."""
    task = load_task(Path("projects/caixa/tasks/product/classification/rg.yaml"))
    assert task.project == "caixa"

def test_load_task_without_project_defaults():
    """Task YAML sem campo project usa 'default'."""
    task = load_task(Path("tasks/product/extraction/matricula_cpf.yaml"))
    assert task.project == "default"

def test_load_tasks_filter_by_project():
    """Filtro por projeto retorna apenas tasks daquele projeto."""
    all_tasks = load_tasks_from_dir(Path("projects"), project="caixa")
    assert all(t.project == "caixa" for t in all_tasks)

def test_golden_set_isolation():
    """Golden sets de projetos diferentes não se misturam."""
    caixa_cases = load_golden_cases(Path("projects/caixa/golden"), "matricula")
    engines_cases = load_golden_cases(Path("projects/gbr-engines/golden"), "matricula")
    # Mesmo doc_type, projetos diferentes → cases diferentes
    assert caixa_cases != engines_cases

def test_eval_run_includes_project():
    """EvalRun serializa com campo project."""
    run = EvalRun(run_id="test", project="caixa", layer=Layer.PRODUCT)
    data = run.model_dump(mode="json")
    assert data["project"] == "caixa"

def test_cli_project_resolves_paths():
    """--project caixa auto-resolve para projects/caixa/."""
    # Testar via subprocess ou mock do Click
    ...
```

---

## 6. Impacto no Frontend

### 6.1 Schema do banco SQLite

O frontend (`gbr-eval-frontend`) precisa de uma coluna `project` em:
- Tabela `runs` → filtrar por projeto
- Tabela `tasks` → organizar por projeto
- Tabela `golden_sets` → agrupar por projeto

### 6.2 UI

- Seletor de projeto no header (similar ao tenant switcher do admin panel)
- Dashboard filtrado por projeto
- Comparação cross-projeto (ex: "matrícula" no gbr-engines vs "matrícula" na Caixa)

### 6.3 Sync tool

O `sync_frontend.py` já está coberto pela mudança da seção 3.4 — passa `--project` e o frontend recebe o campo no payload.

---

## 7. Resumo de Mudanças

### Código (6 arquivos, ~50 linhas adicionais)

| Arquivo | Mudança | Linhas |
|---------|---------|--------|
| `src/gbr_eval/harness/models.py` | Campo `project` em Task e EvalRun | +2 |
| `src/gbr_eval/harness/runner.py` | `load_task()` lê project; `load_tasks_from_dir()` filtra; CLI `--project`; auto-resolve de paths; output dir por projeto | +30 |
| `src/gbr_eval/harness/reporter.py` | Linha "Project:" no console report | +2 |
| `tools/sync_frontend.py` | `--project` option, resolve dirs | +10 |
| `tools/generate_all_synthetic.py` | `--project` option | +5 |
| `tools/check_contract_drift.py` | `--project` option | +5 |

### Testes (~30 linhas)

| Arquivo | Testes |
|---------|--------|
| `tests/harness/test_multi_project.py` (novo) | 6 testes |

### Estrutura de diretórios

| Ação | Path |
|------|------|
| Criar | `projects/` |
| Criar | `projects/gbr-engines/project.yaml` |
| Criar | `projects/caixa/project.yaml` |
| Mover + symlink | `tasks/` → `projects/gbr-engines/tasks/` |
| Mover + symlink | `golden/` → `projects/gbr-engines/golden/` |
| Mover + symlink | `contracts/` → `projects/gbr-engines/contracts/` |
| Mover + symlink | `runs/` → `projects/gbr-engines/runs/` |

---

## 8. Ordem de Execução

```
1. Adicionar campo project (default="default") aos models     → 0 breaking changes
2. Adicionar --project ao CLI com auto-resolve de paths        → opt-in
3. Adicionar project ao reporter (console + JSON)              → cosmético
4. Criar projects/caixa/ com project.yaml                      → novo projeto
5. Criar tasks e golden sets do projeto Caixa em projects/caixa/
6. Migrar gbr-engines para projects/gbr-engines/ com symlinks  → retrocompatível
7. Atualizar sync_frontend.py com --project                    → opt-in
8. Atualizar CI para --project gbr-engines                     → quando pronto
9. Remover symlinks após estabilização                         → cleanup final
```

Passos 1-3 são a Fase 0 do plano Caixa. Passo 4 abre caminho para a Fase 1.

---

## 9. Cenários de Uso

### Projeto Caixa (novo)
```bash
# Criar golden sets
gbr-eval run --project caixa --self-eval --golden-dir projects/caixa/golden

# Rodar eval de classificação
gbr-eval run --project caixa --suite projects/caixa/tasks/product/classification/

# Rodar eval completo
gbr-eval run --project caixa

# Ver trends
gbr-eval trends --project caixa

# Sync com frontend
python tools/sync_frontend.py --project caixa --base-url http://localhost:3002
```

### Projeto gbr-engines (migrado)
```bash
# Retrocompatível (via symlink)
gbr-eval run --suite tasks/product/

# Ou explicitamente
gbr-eval run --project gbr-engines
```

### Futuro projeto Itaú
```bash
mkdir -p projects/itau/{tasks/{product,engineering},golden,contracts/schemas,runs}
cat > projects/itau/project.yaml << 'EOF'
project_id: itau
name: "Itaú BBA"
client: "Itaú"
owner: "diogo.dantas"
status: draft
EOF

gbr-eval run --project itau
```

### Listar projetos (futuro)
```bash
gbr-eval projects list
# Output:
# PROJECT       STATUS    TASKS   GOLDEN CASES   LAST RUN
# gbr-engines   active    170     40             2026-04-23
# caixa         active    0       0              never
# itau          draft     0       0              never
```
