# PRD — gbr-eval

## Visão

gbr-eval é o framework de avaliação eval-first da GarantiaBR. Ele define e verifica critérios de qualidade ANTES de os sistemas serem construídos, garantindo que novas construções atendam padrões desde o dia 1.

## Contexto estratégico

Os produtos legados (plataforma-modular com 1042 branches, originacao_imobiliaria com 582 branches) serão **descontinuados e reconstruídos**. gbr-eval é o primeiro projeto a ser construído — antes dos sistemas que avalia.

### Por que eval-first?

1. **Três jornadas críticas** (Inteligência em Documentos, Due Diligence, Avaliação de Bens) têm **zero testes automatizados** — apenas checklists manuais de QA
2. O eval existente em gbr-engines é **tautológico** — mock_generator.py copia `task.expected` para fabricar respostas, fazendo graders comparar output consigo mesmo
3. A governança ISO 27001 já exige evals automatizadas (KPIs definidos no RACI), mas não há implementação

## Arquitetura de camadas

gbr-eval é o **backbone centralizado de qualidade** da GarantiaBR. Todas as regras de qualidade vivem aqui — nunca distribuídas nos repos alvo. Isso garante visibilidade unificada, consistência cross-repo, e auditabilidade para ISO 27001/SOC 2/BACEN.

### Quatro camadas de qualidade

| Camada | Nome | O que avalia | Status |
|--------|------|-------------|--------|
| **E** | Engineering Quality | Código segue padrões de engenharia e regras de domínio? | **Planejado** — regras por repo definidas, implementação pendente |
| **P** | Product Quality | Outputs do produto estão corretos? | **Parcial** — 34 tasks, 40 golden cases, 12 graders, self-eval operacional |
| **O** | Operational Quality | Sistema opera dentro dos SLAs? | **Futuro** — latência, custo, disponibilidade |
| **C** | Compliance Quality | Regulatório e legal atendidos? | **Futuro** — LGPD, audit trail, BACEN |

**Princípio:** Qualidade > Velocidade. Sempre. Cada camada evolui independentemente, mas todas vivem centralizadas no gbr-eval.

### Camada E — Engineering Quality (por repo)

Avalia se o código produzido pelo time (com ou sem IA) atende padrões de engenharia e regras de domínio específicas de cada serviço. Substitui e expande o antigo L1 (que era restrito a "Claude Code behavior").

Perguntas que o eval responde:
- O código segue as convenções do CLAUDE.md do repo?
- Queries filtram por `tenant_id`?
- Cálculos financeiros usam `Decimal`?
- Integrações têm retry com backoff?
- Audit trail cobre toda mutação de estado?

### Camada P — Product Quality

Avalia se os outputs de IA (ai-engine, extractor, parecer, compliance_agent) estão corretos contra golden sets anotados por humano. Equivale ao antigo L2.

Perguntas que o eval responde:
- O CPF extraído está correto?
- O scoring bate com o golden set?
- Campos críticos têm citation linking?
- O Evaluator Loop detecta inconsistências injetadas?
- O parecer segue a rubrica do CLO?

### Camada O — Operational Quality (futuro)

Avalia métricas operacionais em produção/staging:
- Latência P95 < SLA
- Custo por jornada <= limite
- Disponibilidade >= target
- Taxa de erro < threshold

### Camada C — Compliance Quality (futuro)

Avalia conformidade regulatória:
- LGPD: PII tratada corretamente
- Audit trail: toda ação rastreável
- BACEN: controles financeiros atendidos
- ISO 27001: evidências de qualidade geradas

## Repos alvo — Camada E

O eval cross-repo é centralizado: regras vivem no gbr-eval, são consumidas via GitHub Action por cada repo. Regras são **específicas por domínio** — cada serviço tem riscos diferentes.

### 5 repos prioritários

| Repo | Stack | Domínio | Risco principal |
|------|-------|---------|----------------|
| **engine-integracao** | Python | Integrações externas (SERPRO, ONR, TRTs) | Falha silenciosa, retry infinito, timeout global |
| **garantia_ia** | Python | IA/ML, prompts, extração | Prompt sem versionamento, PII em prompt, custo descontrolado |
| **notifier** | TypeScript | Notificações para clientes bancários | Notificação duplicada, canal errado, LGPD |
| **engine-billing** | (novo) | Faturamento, billing events | Float em financeiro, operação sem idempotency, audit gap |
| **atom-back-end** | (novo) | Backoffice multi-tenant | Vazamento tenant, RBAC bypass, sem audit log |

### Regras por repo (3-5 letais por repo — expandir após validação)

**engine-integracao:**
- Retry com backoff exponencial (nunca retry infinito ou sleep fixo)
- Timeout configurável por integração (nunca timeout global)
- Circuit breaker por provider
- Response validation contra schema do provider
- Credential nunca em código (vault/env only)

**garantia_ia:**
- Prompts versionados e rastreáveis (nunca string inline)
- PII sanitizada antes de entrar em prompt
- Output validado contra schema do contrato (ai-engine → ATOM)
- Cost tracking por inference (tag de custo obrigatória)
- Confidence threshold configurável, nunca hardcoded

**notifier:**
- Template aprovado antes de uso (nunca texto livre construído em runtime)
- Idempotência em toda notificação (dedup key obrigatório)
- LGPD: opt-out respeitado, dados mínimos no payload
- Rate limiting por destinatário
- Canal correto por tipo de evento

**engine-billing:**
- `Decimal` para todo cálculo financeiro (nunca `float`)
- Idempotency key em toda operação financeira
- Audit trail em toda mutação de saldo/cobrança
- Reconciliação sempre em par (débito/crédito)
- Tax compliance: cálculos ISS/PIS/COFINS documentados

**atom-back-end:**
- Toda query filtra por `tenant_id` — zero exceção
- RBAC enforcement em todo endpoint (decorator/middleware obrigatório)
- Audit log em toda ação administrativa
- Dados sensíveis nunca retornam em list endpoints
- Rate limiting por tenant

**Princípio:** Começar com 3-5 regras que já causaram bugs ou que, se violadas, geram incidente regulatório. Expandir somente quando cada regra provar valor. Nunca criar 50 regras não calibradas.

## Taxonomia de Graders

Dois Protocols:
```python
class Grader(Protocol):
    def grade(self, output: dict, expected: dict, spec: GraderSpec) -> GraderResult: ...

class ContextAwareGrader(Protocol):
    def grade(self, output: dict, expected: dict, spec: GraderSpec, *, context: GraderContext | None = None) -> GraderResult: ...
```

Runtime dispatch via `_CONTEXT_AWARE` set (populado por `register_grader(name, context_aware=True)`). Não usa `@runtime_checkable` isinstance — ambos os Protocols têm método `grade()`, o que causa false positives em isinstance checks.

| Tipo | Pureza | Determinismo | Uso em CI |
|------|--------|-------------|-----------|
| **Determinístico** | Puro | 100% reproduzível | Gate (blocking) |
| **Model-based** | Impuro (API externa) | Não-determinístico | Informative (anota no PR, não bloqueia). Promove a blocking após 50+ runs com auto-concordância >= 0.90 |
| **Humano** | N/A | Gold standard | Calibração offline |

### Graders determinísticos implementados

| Nome | O que verifica |
|------|---------------|
| `exact_match` | Valor extraído == referência |
| `numeric_range` | Valor dentro de [min, max] |
| `numeric_tolerance` | Valor dentro de ±tolerância |
| `regex_match` | Valor casa com pattern |
| `field_not_empty` | Campo existe e não é vazio |
| `set_membership` | Valor pertence a conjunto válido |
| `string_contains` | Substring presente no output |
| `field_f1` | F1 score sobre campos extraídos (fuzzy matching) |

### Grader model-based

| Nome | O que verifica |
|------|---------------|
| `llm_judge` | Avaliação semântica via Claude Sonnet, com rubrica markdown |

**Exceção documentada:** LLM-judge não é função pura. Chama API externa, é não-determinístico. Mitigações: seed fixo quando disponível, 3 runs para consistência, threshold de concordância.

### Graders de engenharia

| Nome | O que verifica |
|------|---------------|
| `pattern_required` | Padrão regex presente no código (com ReDoS guard) |
| `pattern_forbidden` | Padrão regex ausente no código |
| `convention_check` | Conjunto de regras (obrigatórias + proibidas) |

### Patterns portados do inspect_ai

Cinco patterns arquiteturais foram portados do inspect_ai (UK AI Security Institute) para gbr-eval:

**1. Epochs + Score Reducers** — Desacopla "quantas execuções" de "como agregar". Graders determinísticos fazem short-circuit automático (1 epoch independente da config). Reducers: MEAN, MEDIAN, AT_LEAST_ONE (pass@k), ALL_PASS (pass^k), MAJORITY.

**2. Model Roles** — Desacopla identidade do modelo da definição do task. `GraderSpec.model_role` mapeia para modelo real via `--model-role grader=claude-sonnet-4-6` no CLI. Resolução: role → model_roles dict → config["model"] → default. Compliance: auditor prova que "grading model ≠ evaluated model".

**3. GraderContext** — Contexto acumulado entre graders. `GraderContext.metadata` carrega task_id, tenant_profile, model_roles. `GraderContext.previous_results` acumula resultados dos graders anteriores. LLM-judge pode referenciar resultados de graders determinísticos.

**4. Solver/AgentTrace** — Protocol async para avaliar trajetória de agentes (não apenas output). `AgentTrace` captura messages, tool_calls, cost_usd, latency_ms. `async_runner.py` executa tasks via Solver e delega grading para `_run_single_epoch()` compartilhado com o runner sync.

**5. task_with()** — Copia tasks com overrides validados por Pydantic. Útil para per-tenant variants sem poluir YAML.

## Gate Fase 1 — Mapeamento

Os 13 critérios do Gate Fase 1 (Confluence ADA) mapeados para graders:

| # | Critério | Target | Grader | Automatizável |
|---|----------|--------|--------|--------------|
| 1 | Classification accuracy | >= 90% | accuracy over golden set | Sim (product) |
| 2 | Extraction accuracy P0 | >= 95% | field_f1 per field | Sim (product) |
| 3 | Citation linking coverage | 100% | field_not_empty on citation | Sim (product) |
| 4 | Evaluator detection | >= 80% | Red team suite | Sim (product) |
| 5 | AI cost per journey | <= R$50 | numeric_range | Sim (product) |
| 6 | Audit trail coverage | 100% | Schema completeness | Sim (engineering/product) |
| 7 | Security P0 | Zero | SAST (fora do eval) | Parcial (engineering) |
| 8 | SLA P95 | < 10 min | numeric_range | Sim (operational) |
| 9 | Real analyses Pine | >= 10 | Manual | Não |
| 10 | Pine NPS | >= 40 | Manual | Não |
| 11 | Proposta comercial | Enviada | Manual | Não |
| 12 | Score formula CLO | Assinada | Manual | Não |
| 13 | UI compliance | Zero violations | Manual | Não |

**Foco Sprint 1:** Critérios 6 (audit trail via engineering graders) + infraestrutura de graders para quando product existir.

## Task Specification

Cada tarefa de avaliação é um arquivo YAML:

```yaml
task_id: extraction.matricula.cpf_proprietario
category: extraction       # classification | extraction | decision | citation | cost | latency
component: ai-engine       # serviço avaliado
layer: product             # engineering | product | operational | compliance
tier: gate                 # gate | regression | canary
tenant_profile: global     # global | caixa | pine | ...

input:
  endpoint: /api/v1/extract
  payload:
    document_type: matricula
    # ... payload real ou referência a fixture

expected:
  proprietario_cpf: "123.456.789-09"
  # ... campos esperados

graders:
  - type: exact_match
    field: proprietario_cpf
    weight: 3           # CRITICAL
    required: true
  - type: field_not_empty
    field: citation.proprietario_cpf
    weight: 3
    required: true
  - type: llm_judge
    field: parecer_qualidade
    weight: 2
    model_role: grader   # resolvido via --model-role grader=<model-id>

scoring_mode: weighted     # weighted | binary | hybrid
pass_threshold: 0.95
epochs: 3                  # repetições (>1 útil para graders não-determinísticos)
reducers: [mean, majority] # como agregar epoch scores
primary_reducer: mean      # reducer que determina passed/failed (deve estar em reducers)
```

## Golden Sets

### Estrutura por skill

```
golden/
├── matricula/
│   ├── metadata.yaml      # quem anotou, quando, versão
│   ├── case_001.json       # input + expected + document hash
│   ├── case_002.json
│   └── ...
├── contrato_social/
│   └── ...
```

### Regras

1. **Nunca gerado automaticamente** — cada caso anotado por humano (Diogo como CLO)
2. **Validado** — Claude como segundo anotador, concordância medida (Cohen's κ >= 0.75)
3. **Versionado** — metadata.yaml rastreia quem, quando, hash do documento original
4. **Anonimizado** — PII removida antes de entrar no repo (LGPD)
5. **Mínimo 20 por skill P0** — 100+ documentos total para Gate Fase 1
6. **Composição atual:** 8 cases por skill (5 standard + 2 edge cases + 1 confuser) = 40 total

### 5 P0 Skills — Golden Sets Prioritários

| Skill | Documento | Campos Críticos |
|-------|-----------|----------------|
| `matricula_v1` | Matrícula imóvel | nº registro, proprietário CPF/CNPJ, área, ônus, alienação fiduciária |
| `contrato_social_v1` | Contrato social | CNPJ, razão social, sócios %, capital, poderes |
| `cnd_v1` | Certidão negativa | tipo, número, órgão, validade, status |
| `procuracao_v1` | Procuração | outorgante, outorgado, poderes específicos, validade |
| `certidao_trabalhista_v1` | Certidão trabalhista | titular, resultado, processos (array), órgão emissor |
| ~~`balanco_v1`~~ | ~~Balanço patrimonial~~ | Blocked — 0 docs disponíveis |

### HITL confidence thresholds (referência para golden sets)

| Tipo de campo | Auto-approval | HITL obrigatório |
|---------------|---------------|-----------------|
| CPF/CNPJ | >= 0.99 | < 0.90 |
| Valores monetários/Datas | >= 0.95 | < 0.85 |
| Nomes próprios | >= 0.90 | < 0.75 |
| Campo P0 sem citation | — | Sempre |

## Contract Testing

gbr-eval mantém snapshots dos schemas de API dos repos alvo:

```
contracts/
└── schemas/
    ├── atom_extract_response.json    # JSON Schema do response de extração
    ├── atom_classify_response.json   # JSON Schema do response de classificação
    └── ...
```

**Mecanismo:**
1. Exportar schema do repo alvo (ex: Pydantic model → JSON Schema)
2. Copiar para `contracts/schemas/`
3. Testes no gbr-eval validam que o snapshot é compatível
4. Quando o repo alvo muda o schema, o CI do gbr-eval quebra → força atualização

## Calibração

### Processo (solo + Claude)

1. Diogo define critérios de avaliação para uma skill
2. Critérios codificados como grader/rubrica
3. Graders aplicados a N outputs
4. Diogo revisa amostra manualmente (5-10% dos outputs)
5. Concordância medida (Cohen's κ)
6. Se κ < 0.75, recalibrar rubrica e repetir
7. Quando κ >= 0.75, grader considerado calibrado

### Limites da calibração solo

- **Documentado:** O calibrador é uma pessoa (Diogo). Isso introduz viés individual.
- **Mitigação:** Claude como segundo anotador (não vota, mas discorda gera flag para revisão).
- **Milestone futuro:** Contratar especialista quando revenue > R$100k MRR.

## Classificação de risco de PR

O CI aplica labels automaticamente. Review humano é sempre obrigatório — a label guia a profundidade, não a necessidade.

| Nível | Critério | Label CI | Ação |
|-------|----------|----------|------|
| Low | Todos determinísticos passam, nenhum arquivo sensível | `eval:low-risk` | Review focado (5 min). 1 em cada 5 recebe review completo (amostragem) |
| Medium | Toca áreas de julgamento (prompts, rubrics, agent configs) | `eval:medium-risk` | Review humano focado |
| High | Toca golden sets, thresholds, calibração, contracts | `eval:high-risk` | Review humano completo por Diogo |

**Regra:** label sim, auto-merge NUNCA. Em contexto vibe-coding com 100% de código AI-generated, todo PR passa por humano.

## Roadmap de Maturidade

| Estágio | Nome | O que faz | Status |
|---------|------|-----------|--------|
| 0 | Manual | Checklists em planilha | ~~Concluído~~ |
| 1 | Gate Básico | Graders determinísticos + golden sets + CI self-eval | **Concluído** — 12 graders, 40 cases, 500 testes |
| 1.5 | Hardening | Patterns inspect_ai + auditoria (5 rodadas, 15 findings corrigidos) | **Concluído** — epochs, model_roles, GraderContext, Solver, SSRF, timing-safe auth |
| 2 | Pipeline P | Camada P: negativos + sintéticos (100-200 cases) + CI eval-gate | **Próximo** |
| 3 | Pipeline E | Camada E: regras por repo + GitHub Action cross-repo nos 5 repos prioritários | **Próximo (paralelo)** |
| 4 | Online | Camada P: runner HTTP em staging + record mode | Planejado (EvalClient implementado, falta endpoint staging) |
| 5 | Observabilidade | Frontend + trend alerts + calibração LLM-judge | Frontend pronto, calibração pendente |
| 5.5 | Solver Eval | Eval de trajetória de agentes via async_runner + AgentTrace | Planejado (infra pronta, falta Fase 17 Pipeline) |
| 6 | Camadas O+C | Operational + Compliance quality | Futuro |
| 7 | Flywheel | Evals geram dados que melhoram prompts automaticamente | Aspiracional |

## Estado Atual (2026-04-20)

### Backend Python (framework)
- **12 graders**: 7 determinísticos + field_f1 + model_judge (context-aware) + 3 engenharia (pattern_required/forbidden, convention_check)
- **Harness completo**: runner sync + async_runner, reporter (4 formatos), regression, trends, analyzer, client (SSRF-protected)
- **Solvers**: Solver Protocol (async), AgentTrace, PassthroughSolver, registry
- **Calibração**: Cohen's kappa em iaa.py
- **CLI**: 3 comandos (`run`, `analyze`, `trends`) com flags `--suite`, `--golden-dir`, `--self-eval`, `--baseline-run`, `--model-role`, `--allow-internal`
- **CI**: ruff + mypy + pytest (**500 testes**, 80%+ coverage)
- **Contract validator**: standalone, sem deps externas
- **5 auditorias independentes**: todas as findings corrigidas

### Segurança (audit-hardened)
- **SSRF protection**: EvalClient resolve DNS e bloqueia IPs internos (bypass via `allow_internal` para dev)
- **PII recursiva**: CPF, CNPJ, RG, PIS/PASEP, telefone, email — sanitização antes de enviar ao LLM-judge + em mensagens de erro
- **Frontend auth**: timing-safe (HMAC via Web Crypto) + fail-closed quando token não configurado
- **YAML stripping**: `load_task()` remove chaves privadas (`_`-prefixed) de grader config
- **ReDoS guard**: graders de engenharia validam patterns antes de aplicar

### Frontend (admin panel)
- **39 páginas**, **57 API routes**, **23 tabelas SQLite**
- Módulos: dashboard, runs (trends/comparison/postmortem), golden sets (CRUD/import/export/versioning), tasks, rubrics (A/B test/concordance), conventions (coverage matrix), calibration (sessions/kappa), contracts (drift detection), skills, alerts
- Webhook: `POST /api/runs/webhook` para ingestão do CI
- PII redaction em todos os endpoints de leitura

### Golden sets
- **40 cases** em 5 skills P0: matricula(8), contrato_social(8), cnd(8), procuracao(8), certidao_trabalhista(8)
- Composição: 5 standard + 2 edge cases + 1 confuser por skill
- balanco: blocked (0 docs), red_team: blocked (authenticity_flag pendente)
- **Zero negativos dedicados** — lacuna a ser endereçada com geração sintética

### Ferramentas auxiliares
- `tools/generate_synthetic.py` — gerador de golden sets sintéticos (4 categorias, Claude em contexto separado)
- `tools/generate_all_synthetic.py` — batch generation com env allowlist
- `tools/compute_hashes.py` — computação SHA-256 dos PDFs originais
- `tools/sync_frontend.py` — sincronização frontend com auth token

### CI (eval-gate)
- Job `eval-gate` no CI do gbr-eval roda self-eval após testes
- Self-eval: 28/34 tasks passam (6 blocked: balanco ×3, cost, decision, latency)
- Crash guard para arquivo ausente ou JSON malformado

### Lacunas identificadas
- Camada E não implementada — regras cross-repo definidas mas sem enforcement
- Evals não rodam no CI dos 5 repos alvo — CI só testa o framework
- 40 cases insuficiente — Anthropic recomenda 100-200 como mínimo
- Runner HTTP (EvalClient) implementado mas sem endpoint real em staging
- Pipeline de Pesquisa (Fase 17) pendente — bloqueio para eval end-to-end com outputs reais

## Anti-patterns

| Anti-pattern | Por que é ruim | O que fazer |
|-------------|---------------|-------------|
| Mock que copia expected | Tautologia — grader compara output consigo mesmo | Golden set real, anotado por humano |
| Grader que sempre passa | Falsa segurança | Incluir red team cases que DEVEM falhar |
| 100% model-based | Custo alto, não-determinístico, flaky CI | Máximo de determinísticos, model-based apenas para julgamento semântico |
| Eval sem calibração | Mede algo, mas não se sabe o quê | Cohen's κ >= 0.75 antes de confiar |
| Schema sem implementação | Engenharia no vácuo | Schema wide, implement narrow — OK ter schema product sem tasks product |

## Decisões tomadas

| # | Decisão | Escolha | Rationale |
|---|---------|---------|-----------|
| 1 | LLM-judge no CI | **Informative primeiro, blocking depois.** Anota no PR sem bloquear. Após 50+ runs com auto-concordância >= 0.90, promove a blocking. | LLM é não-determinístico — flaky gate treina time a ignorar falhas. Determinísticos já pegam erros factuais. |
| 2 | Runner | **Os dois.** pytest testa o framework. CLI (runner.py) executa suites de eval. | Papéis diferentes. pytest = "grader funciona?". CLI = "output está correto?" |
| 3 | Sprint | **Dedicado, 3-5 dias.** Framework já construído. Falta golden sets (CLO) + task YAMLs + CI integration. | Gate Fase 1 (~10/Mai) DEPENDE do eval. Não é concorrente, é pré-requisito. |
| 4 | Auto-promotion | **Label sim, auto-merge não.** CI aplica `eval:low-risk`. Reviewer faz review focado. 1/5 low-risk recebe review completo (amostragem). | Em vibe-coding com 100% AI code, auto-merge é arriscado. Label guia profundidade, não necessidade. |
| 5 | Exemplos negativos | **Obrigatórios.** Confusers, edge cases, degraded, adversariais. Mínimo 40% do total. | Anthropic confirmou: negativos são tão importantes quanto positivos para precision. |
| 6 | Geração sintética | **Em contexto separado.** LLM gera variações dos seeds em conversa sem acesso ao eval. CLO revisa amostra 20-30%. | Anthropic validou a abordagem. Tudo rastreável (source, seed_case, generator). |
| 7 | Volume de cases | **100-200 total** (sweet spot). Seeds humanos ~25, sintéticos ~125-175. | Recomendação Anthropic: abaixo de 100 é insuficiente, acima de 200 é preciosismo para fase seed. |
| 8 | Frontend | **Admin panel Next.js** (pronto). Cobre dashboard, golden sets, runs, calibração, contracts. Sem necessidade de dashboard estático separado. | 39 páginas, 57 API routes, 23 tabelas — observabilidade e configuração num único lugar. |
| 9 | Nomes das camadas | **Nomes semânticos completos:** `engineering`, `product`, `operational`, `compliance`. Substituem L0/L1/L2 em enum, diretórios, YAMLs, CLI e docs. | As 4 camadas são dimensões independentes (não hierarquia) — ordinais induzem ao erro. Letras soltas (E/P/O/C) são grep-hostile. Nomes completos são auto-documentados: `tasks/product/extraction/`, `--layer product`, `layer: product`. Extensível: nova camada ganha nome real (ex: `security`), não `L5`. |
| 10 | Context dispatch | **`_CONTEXT_AWARE` set**, não `@runtime_checkable` isinstance. | `@runtime_checkable` checa apenas nomes de métodos — ambos Protocols têm `grade()`, causando false positives. O set é explícito e zero-ambiguity. |
| 11 | Model roles | **Via `GraderContext.metadata`**, não via injeção em `spec.config`. | Evita poluir spec com chaves privadas. Naturalmente scoped a graders context-aware. |
| 12 | DRY runners | **`_run_single_epoch()` compartilhado** entre sync e async runners. | Garante lógica idêntica de grading. `extra_metadata` param diferencia contexto solver vs output direto. |
| 13 | SSRF protection | **Fail-closed por default**. `allow_internal=True` opt-in para dev. | Em produção, EvalClient nunca deve acessar rede interna. Dev local usa flag explícito. |
