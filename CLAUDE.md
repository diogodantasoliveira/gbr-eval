# CLAUDE.md — gbr-eval

## Identidade do projeto
- **Nome:** gbr-eval
- **Propósito:** Framework de avaliação eval-first para os produtos GarantiaBR
- **Repos alvo:** `GarantiaBR/gbr-engines` (atual), futuros repos reconstruídos
- **Relação:** Projeto SEPARADO — não vive dentro do monorepo gbr-engines
- **Owner:** Diogo Dantas (CAIO)

## O que é este projeto

gbr-eval é o framework de avaliação que define e verifica critérios de qualidade para dois tipos de uso de LLM na GarantiaBR:

1. **LLM como Desenvolvedor (L1):** Claude Code gerando código para a plataforma — segue CLAUDE.md? Filtra por tenant_id? Não hardcoda dados de negócio?
2. **LLM como Produto (L2):** ai-engine, extractor, parecer, compliance_agent produzindo outputs para clientes — extrai o CPF correto? O scoring bate com o golden set?

### Metodologia: Eval-First

Este projeto existe ANTES dos sistemas que ele avalia. Os produtos legados (plataforma-modular, originacao_imobiliaria) serão descontinuados e reconstruídos. gbr-eval define os critérios de qualidade que as novas construções devem atender desde o dia 1.

### Três camadas de qualidade

| Camada | O que avalia | Implementação |
|--------|-------------|---------------|
| **L0** (estática) | lint, type-check, testes unitários | Já existe no CI dos repos alvo |
| **L1** (dev agent) | Claude Code gera código correto? | Sprint 1 — este projeto |
| **L2** (product AI) | ai-engine produz outputs corretos? | Schema agora, implementação quando produção existir |

## Regra Zero — Nunca Inferir

> **Herdada de gbr-engines. Aplica-se integralmente.**

A LLM NÃO toma decisões sobre:
- Quais critérios de qualidade usar (humano decide)
- O que constitui "correto" em um golden set (CLO valida)
- Limiares de aprovação/reprovação (configuração, não código)
- Se um grader deve ser blocking ou informative (decisão de negócio)

Na dúvida, **perguntar**.

## Arquitetura

```
gbr-eval/
├── src/gbr_eval/
│   ├── graders/          # Graders: f(input, output, reference, config) → score
│   │   ├── base.py       # Interface abstrata + registry
│   │   ├── deterministic.py  # exact_match, numeric_range, regex, field_not_empty
│   │   ├── field_f1.py   # F1 por campo com fuzzy matching
│   │   └── model_judge.py    # LLM-as-judge (Claude Sonnet)
│   ├── harness/          # Runner de avaliação
│   │   ├── runner.py     # Execução de tasks, parallelismo, reporting
│   │   ├── models.py     # Pydantic models (Task, GraderResult, EvalRun)
│   │   └── reporter.py   # Geração de relatórios (CI, console, JSON)
│   ├── contracts/        # Schema snapshots dos repos alvo
│   │   └── schemas/      # Cópias versionadas dos schemas de API
│   └── calibration/      # Concordância inter-anotador
│       └── iaa.py        # Cohen's kappa, concordance tracking
├── tasks/                # Definições de tarefas de avaliação (YAML)
│   ├── layer1/           # L1: dev agent behavior
│   └── layer2/           # L2: product AI (schema only por ora)
├── golden/               # Golden sets por tipo de documento
│   ├── matricula/
│   ├── contrato_social/
│   ├── cnd/
│   ├── procuracao/
│   └── balanco/
├── tests/                # Testes do próprio framework
└── docs/                 # Documentação
```

## Comandos de desenvolvimento

```bash
# Setup
uv sync

# Rodar testes do framework
uv run pytest

# Rodar testes com cobertura
uv run pytest --cov=src/gbr_eval --cov-report=term-missing

# Lint
uv run ruff check .

# Type check
uv run mypy src/

# Rodar uma suite de eval
uv run python -m gbr_eval.harness.runner --suite layer1

# Rodar task específica
uv run python -m gbr_eval.harness.runner --task tasks/layer1/extraction/matricula_cpf.yaml
```

## Invariantes — NUNCA violar

### 1. Graders são funções puras
```python
def grade(input: dict, output: dict, reference: dict, config: GraderConfig) -> GraderResult:
```
Mesma assinatura para CI, sampling em produção, e triggers de ação.
**Exceção documentada:** LLM-judge não é puro (chama API externa, não-determinístico). Tratado como caso especial com retry e seed fixo.

### 2. Zero tautologia
O golden set NUNCA é gerado automaticamente a partir do expected do task. Cada golden set é:
- Anotado por humano (Diogo como CLO)
- Validado por segundo revisor (Claude como annotator auxiliar, com limites documentados)
- Versionado e rastreável (quem anotou, quando, hash do documento)

### 3. Contract testing via snapshots
gbr-eval mantém cópias dos schemas de API dos repos alvo em `contracts/schemas/`. Quando o repo alvo muda um schema sem atualizar o snapshot aqui, o CI do gbr-eval QUEBRA. Isso é comportamento desejado — força sincronização.

### 4. Separação build-time vs operate-time
- **Build-time (CI):** graders rodam como gate antes do merge. Resultado: pass/fail no PR.
- **Operate-time (futuro L2):** graders rodam como sampling em produção. Resultado: métricas, alertas, dashboards.
- Mesmos graders, contextos diferentes. A configuração (threshold, blocking vs informative) muda, o código não.

### 5. Schema wide, implementation narrow
Os schemas Pydantic cobrem as 3 camadas (L0, L1, L2). A implementação atual cobre apenas L1. Schemas de L2 existem mas não têm tasks nem graders — estão prontos para quando a produção existir.

## Gate Fase 1 — Mapeamento para Graders

Os 13 critérios do Gate Fase 1 (Confluence ADA) que este eval deve verificar:

| # | Critério Gate | Grader(s) | Layer |
|---|---|---|---|
| 1 | Classification >= 90% | `accuracy` over golden set | L2 |
| 2 | Extraction >= 95% (P0) | `field_f1` per field | L2 |
| 3 | Citation linking = 100% | `field_not_empty` on citation | L2 |
| 4 | Evaluator detection >= 80% | Red team suite (injected docs) | L2 |
| 5 | Cost <= R$50/journey | `numeric_range` on cost metric | L2 |
| 6 | Audit trail = 100% | Schema completeness check | L1/L2 |
| 7 | Security P0 = Zero | SAST + manual (fora do eval) | L0 |
| 8 | SLA P95 < 10 min | `numeric_range` on duration | L2 |
| 9-13 | Business/UX criteria | Fora do escopo do eval automatizado | — |

**Nota:** Critérios 1-6 e 8 são automatizáveis. Critérios 9-13 (NPS, proposta comercial, assinaturas) são humanos.

## 5 P0 Skills — Golden Sets Prioritários

| Skill | Documento | Campos Críticos |
|---|---|---|
| `matricula_v1` | Matrícula imóvel | nº registro, proprietário CPF/CNPJ, área, ônus, alienação fiduciária |
| `contrato_social_v1` | Contrato social | CNPJ, razão social, sócios %, capital, poderes |
| `cnd_v1` | Certidão negativa | tipo, número, órgão, validade, status |
| `procuracao_v1` | Procuração | outorgante, outorgado, poderes específicos, validade |
| `balanco_v1` | Balanço patrimonial | ativo total, passivo, PL, dívida líquida, liquidez corrente |

## Regras de decisão determinísticas

O motor de decisão NÃO usa LLM. É determinístico e avaliável com graders puros:

```
Score >= 0.90 AND zero critical non-conforming → aprovado
Score >= 0.70 AND critical conforming AND >= 1 warning → aprovado_com_ressalvas
Any critical non-conforming → reprovado
>= 3 critical fields nao_verificavel → inconclusivo
```

Score = SUM(field_weight × field_confidence) / SUM(critical_weights)
- CRITICAL: weight 3
- IMPORTANT: weight 2
- INFORMATIVE: weight 1

## Convenções

- **Branch:** `tipo/descricao-curta` (ex: `feat/grader-field-f1`, `fix/runner-timeout`)
- **Commit:** Conventional Commits (`tipo(escopo): mensagem`)
- **Escopos válidos:** graders, harness, contracts, golden, calibration, tasks, docs, ci
- **Testes:** pytest, AAA pattern, coverage >= 80%
- **Lint:** ruff
- **Types:** mypy strict
- **Python:** 3.12+

## Relação com gbr-engines

gbr-eval é **consumidor** de gbr-engines, nunca ao contrário:
- Lê schemas de API (via snapshots em `contracts/`)
- Lê golden sets exportados (via `golden/`)
- Roda graders contra outputs reais ou gravados
- NUNCA importa código de gbr-engines diretamente
- NUNCA altera código de gbr-engines

## Decisões pendentes

> Estas decisões precisam ser tomadas pelo Diogo antes de implementar:

1. **LLM-judge no CI:** Blocking (falha impede merge) ou informative (alerta mas não bloqueia)?
2. **Runner:** pytest como runner ou CLI customizado?
3. **Sprint:** Dedicado (1-2 semanas só eval) ou diluído (em paralelo com outras entregas)?
4. **Auto-promotion:** PRs com todos graders determinísticos passando recebem label "low-risk" para fast-track review?

## Autonomia

### AUTÔNOMO
- Criar/editar graders, tasks, golden sets, testes, docs
- Rodar testes e linters
- Criar branches e commits

### PEDIR APROVAÇÃO
- Alterar limiares de aprovação/reprovação
- Adicionar novo grader type
- Modificar schema de Task
- Abrir PR

### BLOQUEADO
- Validar golden sets (CLO valida)
- Decidir se grader é blocking vs informative
- Push direto em main
- Alterar contratos de API dos repos alvo
