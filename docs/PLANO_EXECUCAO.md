# gbr-eval — Plano de Execucao

> De framework funcional a pipeline de qualidade em producao.
> Autor: Diogo Dantas (CLO/CAIO) | Data: 2026-04-20
> Baseado em: feedback CTO + recomendacoes Anthropic + 4 auditorias independentes

---

## Contexto: onde estamos

### O que temos

| Componente | Estado | Detalhes |
|-----------|--------|---------|
| **Backend Python** | Operacional | 12 graders (7 deterministicos + field_f1 + llm_judge + 3 engineering), runner CLI, code loader (file-by-file, security hardened), regression (degraded_scores), trends (slope-based), reporter (4 formatos), calibracao IAA, 389 testes, CI (ruff+mypy+pytest 80%+) |
| **Frontend admin panel** | Operacional | 39 paginas, 57 API routes, 23 tabelas SQLite. Dashboard, runs, golden sets, tasks, rubrics, conventions, calibration, contracts, skills, alerts |
| **Golden sets** | Seed + Edge + Confuser | 40 cases em 5 skills P0 (8/skill), anotados por humano, LGPD-compliant |
| **Tasks** | Definidos | 34 task YAMLs (23 product + 8 engineering + 3 confusers) |
| **CI** | Operacional | Testa framework (pytest) + eval-gate (self-eval) + reusable action |
| **Webhook** | Pronto | `POST /api/runs/webhook` com Bearer auth para ingestao do CI |
| **Auditorias** | 4 rodadas | 3 com correcoes completas, 1 com findings pendentes |

### O que falta

| Lacuna | Impacto |
|--------|---------|
| **CI cross-repo nao configurado** | Code Loader funciona localmente mas ainda nao integrado ao CI dos 5 repos alvo |
| Evals nao rodam no CI de nenhum repo alvo | Framework nao integrado ao workflow de desenvolvimento |
| 40 cases (meta: 100-200) | Volume insuficiente para confianca estatistica |
| Runner nao faz HTTP real contra ai-engine | Avalia apenas offline, nao testa o produto real em staging |
| SHA-256 hashes pendentes | Rastreabilidade ISO 27001 incompleta |
| Feedback loop nao operacional | Resultados do eval nao alimentam melhoria continua automatizada |
| `eval_owner_role` (role-based) nao implementado | `eval_owner` atual e por nome de pessoa, nao por role |
| Calibracao de patterns pendente | Patterns precisam ser validados contra repos reais (zero falsos positivos) |

---

## Fase 1 — Self-Eval Validation (Semana 1)

> **Status: CONCLUÍDO (2026-04-19)**
> 23/23 tasks PASS, gate GO, score 1.0.

### 1.1 Rodar self-eval e corrigir inconsistências ✅

Self-eval executado com sucesso. Correções aplicadas:
- 3 balanco tasks → `tier: canary` (sem golden sets disponíveis)
- Self-eval fallback implementado para tasks sem golden set (cost/latency/decision usam `task.expected`)
- Decision task: removido `document_type: matricula` do payload para evitar golden set match incorreto
- Resultado: 23/23 PASS, score 1.0, gate GO

### 1.2 Computar SHA-256 hashes dos PDFs

Substituir `"sha256:PENDING_COMPUTE_FROM_PDF_doc_id_XXXXX"` pelo hash real em todos os 25 cases.

**Status:** Pendente — PDFs estão locais mas não serão processados agora (decisão do CLO).

---

## Fase 2 — Exemplos Negativos (Semana 1-2)

> **Status: CONCLUÍDO (2026-04-19)**
> 15 cases negativos criados (5 confusers + 10 edge cases). Taxonomia documentada. Tag filtering implementado.

### 2.1 Taxonomia de negativos ✅

| Categoria | O que testa | Cases | Numeração |
|-----------|-------------|-------|-----------|
| **Confuser** | Classificação incorreta | 5 (1/skill) | 101+ |
| **Edge case** | Campos ausentes/null | 10 (2/skill) | 201+ |
| **Degraded** | OCR/qualidade ruim | 0 (Fase 3) | 300+ |
| **Adversarial** | Fraude/adulteração | 0 (depende red_team) | — |

Taxonomia documentada em `docs/NEGATIVE_CASES_TAXONOMY.md`.

### 2.2 Golden set tag filtering ✅

- Modelo `Task` recebeu campo `golden_set_tags: list[str] | None`
- `load_golden_cases()` filtra por tags quando especificado
- Tasks configuradas: extraction/citation → `["seed"]`, classification target → `["seed", "edge_case"]`, confuser → `["confuser"]`
- Inventário: 25 seed + 5 confuser + 10 edge_case = 40 cases

**Critério de conclusão:** ✅ 15 cases negativos (meta ≥20 alcançável com geração sintética).

---

## Fase 3 — Geração Sintética (Semana 2-3)

> **Status: PREPARADO (2026-04-19)**
> Scripts prontos. Aguardando execução pelo CLO com API key.

### 3.1 Script de geração ✅

Dois scripts implementados:
- `tools/generate_synthetic.py` — gerador por skill/categoria (já existia)
- `tools/generate_all_synthetic.py` — orquestrador one-shot (novo)

Modelo configurável via env var `GBR_EVAL_SYNTH_MODEL` ou flag `--model`.

Execução:
```bash
# 1. Configurar .env com ANTHROPIC_API_KEY
# 2. (Opcional) Escolher modelo: GBR_EVAL_SYNTH_MODEL=claude-opus-4-20250514
# 3. Preview: uv run python tools/generate_all_synthetic.py
# 4. Gerar:  uv run python tools/generate_all_synthetic.py --apply
```

### 3.2 Review amostral pelo CLO

CLO revisa 20-30% dos cases sintéticos. Critérios:
- Valores plausíveis (CNPJ com dígito verificador válido, datas razoáveis)
- Combinações consistentes (certidão positiva COM processos, negativa SEM)
- Anonimização consistente

### 3.3 Distribuição alvo (160 cases com orquestrador)

| Categoria | Existentes | Gerados | Total |
|-----------|-----------|---------|-------|
| Positivos reais (seed) | 25 | — | 25 |
| Positivos sintéticos | 0 | 75 | 75 |
| Confusers (manuais + sintéticos) | 5 | 25 | 30 |
| Edge cases (manuais + sintéticos) | 10 | 20 | 30 |
| **Total** | **40** | **120** | **160** |

Custo estimado: ~$2-4 (Sonnet) ou ~$8-15 (Opus).

**Critério de conclusão:** Parcial — scripts prontos. Falta: execução + review CLO.

---

## Fase 4 — Pipeline CI/CD (Semana 2-3, paralelo à Fase 3)

> **Status: IMPLEMENTADO (2026-04-19)**
> CI workflow completo em `.github/workflows/ci.yml`. Reusable action em `.github/actions/gbr-eval-gate/`.

### 4.1 Eval gate no CI do gbr-eval ✅

Job `eval-gate` no `.github/workflows/ci.yml`:
- Roda `gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval --tier gate`
- `--tier gate` exclui canary tasks (balanco) automaticamente
- Exit code do runner é o gate: 0=GO, 1=NO_GO, 2=NO_GO_ABSOLUTE
- Report salvo como artifact `eval-report`

### 4.2 Eval gate no CI do gbr-engines ✅ (reusable action pronta)

Reusable composite action em `.github/actions/gbr-eval-gate/action.yml`. Uso no repo alvo:

```yaml
- uses: GarantiaBR/gbr-eval/.github/actions/gbr-eval-gate@main
  with:
    layer: engineering  # ou product
    tier: gate
```

Outputs: `gate-result`, `overall-score`, `report-path`.

**Pendente:** Configurar nos 5 repos alvo (depende de tasks engineering-layer — Fase 7).

### 4.3 Persistência de baselines ✅

**Opção A implementada (zero infra):** GitHub Artifacts com `dawidd6/action-download-artifact@v6`.
- PRs: download baseline do último main run bem-sucedido, passa como `--baseline-run`
- Main merges: salva `eval-baseline` com retention 90 dias
- Se baseline não existe (primeiro run), roda sem comparação

### 4.4 GitHub PR Annotations ✅

`dorny/test-reporter@v1` converte `test-results.xml` (JUnit) em annotations inline no PR.

### 4.5 Ingestão via webhook no frontend ✅

Step condicional no CI (main merges only):
- Requer secrets `EVAL_WEBHOOK_URL` e `EVAL_WEBHOOK_TOKEN`
- POST eval-report.json para `POST /api/runs/webhook`
- Graceful: skip se secrets não configurados

**Critério de conclusão:** ✅ CI workflow completo. Baseline automático. Webhook preparado. Reusable action pronta.

---

## Fase 5 — Online Eval em Staging (Semana 4-5)

> **Status: IMPLEMENTADO (2026-04-19)**
> HTTP client, record/replay, analyze — todos implementados e testados (28 testes).

### 5.1 Runner com HTTP client ✅

`EvalClient` em `src/gbr_eval/harness/client.py` (stdlib `urllib.request`, zero deps extras).

```bash
# Online eval contra staging
gbr-eval run --suite tasks/product/ --golden-dir golden/ \
  --endpoint http://staging:8000 --tenant itau

# Com recording para replay offline
gbr-eval run --suite tasks/product/ --golden-dir golden/ \
  --endpoint http://staging:8000 --tenant itau \
  --record outputs/2026-04-25/
```

Flags: `--endpoint` (base URL), `--tenant` (X-Tenant-ID header, default "global").
Mutually exclusive com `--self-eval`.

**Pendente:** ai-engine em staging acessível + golden sets com document_id real.

### 5.2 Modo record/replay ✅

`OutputRecorder` em `client.py` salva/carrega outputs por task_id/case_number.

```bash
# Replay offline (sem HTTP)
gbr-eval run --suite tasks/product/ --golden-dir golden/ \
  --replay outputs/2026-04-25/
```

Record salva em `{record_dir}/{task_id}/case_{NNN}.json`. Replay carrega automaticamente.

### 5.3 Feedback loop (`gbr-eval analyze`) ✅

```bash
gbr-eval analyze --runs-dir runs/
gbr-eval analyze --runs-dir runs/ --output-format json
```

Output: per-task pass rate, avg/min/p5 scores, weakest tasks, most failing fields.

**Critério de conclusão:** ✅ HTTP client, record/replay, analyze — todos implementados. 277 testes passando.

---

## Fase 6 — Calibração e Promoção do LLM-Judge (Semana 5-6)

### 6.1 Acumular 50+ runs

Após Fases 4-5 operacionais, acumular runs. Para cada run, LLM-judge avalia os mesmos cases. Medir auto-concordância.

### 6.2 Calibração inter-anotador

O frontend já tem o módulo completo de calibração (sessions, annotations, disagreements, Cohen's kappa). Usar para:
- CLO vs Claude como anotadores de golden sets
- LLM-judge vs graders determinísticos nos mesmos cases

### 6.3 Promoção

Se auto-concordância >= 0.90, promover LLM-judge de INFORMATIVE a BLOCKING. PR documentando a decisão.

**Critério de conclusão:** 50+ runs acumulados. Auto-concordância medida. Decisão de promoção documentada.

---

## Fase 7 — Camada E: Engineering Quality + Code Loader (Semana 6-8)

> **Status: IMPLEMENTADO (parcial) (2026-04-20)**
> 3 graders implementados, 8 task YAMLs, reusable action pronta.
> Code Loader implementado: `load_code_files()`, `evaluate_file()`, `run_task_against_code()`, `run_engineering_suite()`.
> 35 testes (24 funcionais + 11 seguranca/edge-case). `GraderResult.file_path` para rastreabilidade.
> **Pendente:** CI cross-repo nos 5 repos alvo, calibracao de patterns, `eval_owner_role` migration.

### Decisoes de arquitetura (2026-04-20)

| # | Decisao | Escolha | Razao |
|---|---------|---------|-------|
| D8 | Primeiro ponto de insercao | Local → pre-PR | Engenheiro roda localmente, ganha confianca antes de bloquear CI |
| D9 | Ownership | Role-based (`eval_owner_role`), agnostico a nomes | Futuro tera users com permissoes |
| D10 | Code Loader | Hibrido: `--code-dir` local + CI fornece path | Flexivel — funciona local e CI |
| D11 | Avaliacao de arquivos | File-by-file com agregacao | Qualidade: saber QUAL arquivo violou QUAL regra |
| D12 | Exemplos (100-200) | Paralelo a arquitetura | Confirmado pela Anthropic como sweet spot |

### 7.1 Code Loader — Arquitetura

**Problema:** Os graders de engineering (`pattern_required`, `pattern_forbidden`, `convention_check`) esperam `output["content"]` com codigo. Hoje ninguem fornece esse conteudo — as tasks definem `input.payload.repo` e `scan_target` mas o runner ignora esses campos.

**Solucao implementada: `load_code_files()` + `evaluate_file()` + `run_task_against_code()`**

```
CLI:
  gbr-eval run --suite tasks/engineering/ --code-dir ~/repos/

Fluxo interno (code_loader.py):
  1. load_task(yaml) → Task
       task.input.payload.repo = "atom-back-end"
       task.input.payload.scan_target = "**/*.py"

  2. load_code_files(code_dir, repo, scan_target) → list[tuple[Path, str]]
       code_path = code_dir / repo
       files = glob(code_path, scan_target)
       retorna [(path, content), ...] com:
         - protecao path traversal (nenhum arquivo fora de code_dir)
         - symlink escape prevention
         - limite de tamanho: 1 MB por arquivo (_MAX_FILE_SIZE)
         - limite de quantidade: 10.000 arquivos (_MAX_FILES)

  3. Para cada arquivo: evaluate_file(task, file_path, content) → FileResult
       file_result.conforming = todos os graders passaram
       file_result.grader_results = [GraderResult(file_path=str(path), ...)]

  4. run_task_against_code(task, code_dir) → TaskResult
       task_score = arquivos_conformes / total_arquivos
       violations = [fr for fr in file_results if not fr.conforming]
```

**Estrutura do FileResult:**

```python
@dataclass
class FileResult:
    file_path: Path         # caminho relativo dentro do repo
    conforming: bool        # True se todos os graders passaram
    grader_results: list[GraderResult]
```

**Score da task engineering:**

```
task_score = arquivos_que_passaram_TODOS_graders / total_arquivos_avaliados
```

Um arquivo so e "conforme" se TODOS os graders passam nele. Se qualquer grader falha, o arquivo e nao-conforme. `GraderResult.file_path` registra qual arquivo gerou cada resultado, permitindo rastreabilidade completa.

**Violations report:**

O resultado indica claramente:
- Qual arquivo violou (path relativo via `GraderResult.file_path`)
- Qual regra foi violada (grader type + description)
- Qual pattern matched/missing

Isso permite ao engenheiro saber exatamente onde corrigir.

### 7.2 Workflow local-first

```
PASSO 1 — Engenheiro roda localmente:
─────────────────────────────────────

  # Repos clonados lado a lado:
  ~/repos/atom-back-end/
  ~/repos/engine-billing/
  ~/repos/engine-integracao/
  ~/Python-Projetos/gbr-eval/

  # Rodar eval de engenharia contra um repo:
  cd ~/Python-Projetos/gbr-eval
  gbr-eval run --suite tasks/engineering/atom-back-end/ \
    --code-dir ~/repos/

  # Rodar contra todos os repos:
  gbr-eval run --suite tasks/engineering/ \
    --code-dir ~/repos/

  # Output esperado:
  #   eng.atom.tenant_id_filter .............. PASS (47/47 files)
  #   eng.atom.rbac_enforcement .............. FAIL (43/47 files)
  #     VIOLATION: app/routes/legacy.py — pattern "require_auth" not found
  #     VIOLATION: app/routes/export.py — pattern "require_auth" not found
  #     ...

PASSO 2 — Pre-PR (CI):
───────────────────────

  # GitHub Action no repo alvo:
  - uses: actions/checkout@v4        # repo alvo
  - uses: actions/checkout@v4        # gbr-eval
    with:
      repository: GarantiaBR/gbr-eval
      path: gbr-eval
  - run: |
      cd gbr-eval
      uv sync --all-extras
      gbr-eval run --suite tasks/engineering/${{ github.event.repository.name }}/ \
        --code-dir ../

PASSO 3 — Staging (futuro, nao-bloqueante):
───────────────────────────────────────────

  # Pos-deploy, roda eval como auditoria:
  # Resultados vao pro dashboard via webhook
  # Nao bloqueia nada — observa e alimenta melhoria continua
```

### 7.3 Ownership role-based

**Estado atual:** tasks YAMLs usam `eval_owner` com nome de pessoa (ex: `eval_owner: diogo.dantas`).

**Evolucao planejada (step 7.5.5):** migrar para `eval_owner_role` como metadata declarativa agnostica a pessoas:

```yaml
# tasks/engineering/atom-back-end/tenant_id_filter.yaml
eval_owner_role: technology    # Tecnologia define padroes de codigo

# tasks/product/extraction/matricula_cpf.yaml
eval_owner_role: product       # Produto define corretude da extracao
```

Valores validos: `technology`, `product`, `operations`, `compliance`.

O sistema sera **agnostico a pessoas**. Futuro: criar modulo de users com permissoes por role, permitindo que cada area gerencie suas regras no frontend.

**Evolucao planejada:**
1. *Agora:* `eval_owner_role` como metadata sem enforcement
2. *Futuro:* Users no frontend com roles → so `technology` pode editar tasks de engineering
3. *Futuro+:* Workflow de aprovacao — tech lead aprova mudanca em regra de engineering

### 7.4 Regras por repo (3-5 letais — expandir apos validacao)

**engine-integracao** (Python, integracoes externas):
- Retry com backoff exponencial (nunca retry infinito ou sleep fixo)
- Timeout configuravel por integracao (nunca timeout global)
- Credential nunca em codigo (vault/env only)

**engine-billing** (Python, financeiro):
- `Decimal` para calculos financeiros (nunca `float`)
- Idempotency key em toda operacao financeira

**atom-back-end** (Python, backoffice multi-tenant):
- Toda query filtra por `tenant_id`
- RBAC em todo endpoint
- Audit log em toda acao administrativa

**Principio:** Comecar com 3-5 regras que ja causaram bugs ou que, se violadas, geram incidente regulatorio. Expandir somente quando cada regra provar valor.

### 7.5 Implementacao incremental

| Step | O que | Estimativa | Status |
|------|-------|-----------|--------|
| 7.5.1 | `load_code_files()` + `FileResult` no code_loader.py | 1 dia | ✅ DONE |
| 7.5.2 | File-by-file execution loop + `evaluate_file()` + `run_task_against_code()` | 1 dia | ✅ DONE |
| 7.5.3 | `GraderResult.file_path` para rastreabilidade de arquivo | 0.5 dia | ✅ DONE |
| 7.5.4 | 35 testes do Code Loader (24 funcionais + 11 seguranca/edge-case) | 0.5 dia | ✅ DONE |
| 7.5.5 | `eval_owner_role` migration nas 8 task YAMLs | 0.5 dia | pendente |
| 7.5.6 | Teste real: rodar contra atom-back-end clonado | 0.5 dia | pendente |
| 7.5.7 | GitHub Action cross-repo nos 5 repos alvo | 1 dia | pendente |
| 7.5.8 | Calibracao: ajustar patterns pra zero falsos positivos | 1-2 dias | pendente |

**Total restante: ~3-4 dias uteis** (7.5.5 a 7.5.8).

**Criterio de conclusao:** >= 3 regras por repo rodando no CI dos repos alvo. Engenheiro executa `gbr-eval run --code-dir` localmente e recebe violations claras. Zero falsos positivos em 3 runs consecutivos.

### 7.6 Feedback loop (CTO requirement)

```
[1] Engenheiro (ou LLM) gera codigo
        |
        v
[2] gbr-eval roda localmente (--code-dir)
        |
        v
[3] Violations reportadas: "arquivo X viola regra Y"
        |
        v
[4] Engenheiro corrige (ou ajusta prompt do LLM)
        |
        v
[5] Re-roda eval → score sobe
        |
        v
[6] Quando 100%: abre PR com confianca
        |
        v
[7] CI roda eval novamente (belt + suspenders)
        |
        v
[8] Resultados vao pro dashboard (webhook)
        |
        v
[9] Dashboard mostra tendencias over time
        |
        v
[10] Time identifica patterns → melhora regras/prompts
         (volta ao passo 1)
```

### 7.7 Red team (depende do ai-engine)

Desbloquear quando ai-engine implementar `authenticity_flag`. 5 cases adversariais ja planejados em `golden/red_team/metadata.yaml`.

---

## Decisoes — registro

### Decididas

| # | Decisao | Escolha | Data |
|---|---------|---------|------|
| D1 | Formato `processos` em certidao | Grader polimorfico (realidade e polimorfica) | pendente impl |
| D2 | Eval staging: offline ou online | Offline primeiro, staging como cercado depois | 2026-04-19 |
| D3 | Modelo para sinteticos | Sonnet para positivos, Opus para adversariais | 2026-04-19 |
| D4 | Distribuicao neg/pos | 60/40 (reflete producao real) | 2026-04-19 |
| D5 | Regras centralizadas vs distribuidas | Centralizado no gbr-eval | 2026-04-19 |
| D6 | Camadas E/P/O/C vs L0/L1/L2 | Novo modelo (4 camadas independentes) | 2026-04-19 |
| D7 | Nomes das camadas | Semanticos: engineering, product, operational, compliance | 2026-04-19 |
| D8 | Primeiro ponto de insercao workflow | Local → pre-PR (nao staging) | 2026-04-20 |
| D9 | Ownership de camadas | Role-based, agnostico a pessoas | 2026-04-20 |
| D10 | Code Loader | Hibrido: `--code-dir` local + CI fornece path | 2026-04-20 |
| D11 | Avaliacao de arquivos (engineering) | File-by-file com agregacao (qualidade > simplicidade) | 2026-04-20 |
| D12 | Exemplos (100-200 sweet spot) | Expandir em paralelo com arquitetura | 2026-04-20 |

### Pendentes

| # | Decisao | Opcoes | Impacto |
|---|---------|--------|---------|
| D13 | Formato processos: impl polimorfica | (A) Dict matching por keys (B) Schema union | Grader field_f1 |
| D14 | Frontend user management | (A) Roles simples (B) Full RBAC | Enforcement de ownership |
| D15 | Staging deploy trigger | (A) Pos-deploy hook (B) Cron (C) Manual | Quando o cercado roda |

---

## Cronograma consolidado

```
Semana 1     Semana 2     Semana 3     Semana 4     Semana 5     Semana 6     Semana 7     Semana 8
--------     --------     --------     --------     --------     --------     --------     --------
[Fase 1 ]    [  Fase 2  ] [  Fase 3              ]
Self-eval    Negativos     Sinteticos + review
 (DONE)       (DONE)       (scripts prontos)

             [     Fase 4 (paralelo)              ]
             CI gate gbr-eval + reusable action
              (DONE)

                           [     Fase 7 — Code Loader + Eng Workflow    ]
                            load_code     evaluate_file  Teste real    CI cross-repo
                            _files()DONE  DONE+35 testes atom-back-end  5 repos

                                       [  Fase 5            ]
                                        Runner HTTP + record   [Fase 6        ]
                                        Feedback loop           Calibracao
                                         (DONE)                 LLM-judge 50+ runs
```

**Estado:** Fases 1, 2, 4, 5 concluidas. Fase 3 pronta pra rodar (paralelo). **Fase 7 parcialmente concluida** — Code Loader implementado (7.5.1-7.5.4 done, 35 testes). Falta: CI cross-repo nos 5 repos alvo + calibracao de patterns + `eval_owner_role` migration.

**Fase 7 restante:** 3-4 dias uteis (7.5.5 a 7.5.8).

---

## Métricas de sucesso

| Métrica | Alvo | Como medir |
|---------|------|-----------|
| Golden sets totais | >= 200 | `find golden/ -name "case_*.json" \| wc -l` |
| Negativos / Total | >= 40% | Cases com tag "negative" |
| Self-eval score médio | >= 0.98 | `gbr-eval run --self-eval` |
| CI eval gate ativo | sim | Workflow roda em PRs |
| Baseline automático | sim | Artifact/S3 |
| LLM-judge auto-concordância | >= 0.90 | Após 50+ runs |
| Skills com 20+ cases reais | 5/5 | metadata.yaml |

---

## Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:---:|:---:|-----------|
| ai-engine staging instável | Alta | Bloqueia Fase 5 | Começar offline (Fases 1-4) |
| Cases sintéticos inconsistentes | Média | Golden sets poluídos | Review amostral CLO |
| LLM-judge não converge | Média | Não promove a blocking | Manter informative, ajustar rubric |
| Schema ai-engine muda sem aviso | Alta | Golden sets obsoletos | Frontend já tem contract drift detection |
| Red team bloqueado indefinidamente | Alta | Gate #4 não avaliável | Priorizar authenticity_flag no roadmap |
