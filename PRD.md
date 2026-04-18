# PRD — gbr-eval

## Visão

gbr-eval é o framework de avaliação eval-first da GarantiaBR. Ele define e verifica critérios de qualidade ANTES de os sistemas serem construídos, garantindo que novas construções atendam padrões desde o dia 1.

## Contexto estratégico

Os produtos legados (plataforma-modular com 1042 branches, originacao_imobiliaria com 582 branches) serão **descontinuados e reconstruídos**. gbr-eval é o primeiro projeto a ser construído — antes dos sistemas que avalia.

### Por que eval-first?

1. **Três jornadas críticas** (Inteligência em Documentos, Due Diligence, Avaliação de Bens) têm **zero testes automatizados** — apenas checklists manuais de QA
2. O eval existente em gbr-engines é **tautológico** — mock_generator.py copia `task.expected` para fabricar respostas, fazendo graders comparar output consigo mesmo
3. A governança ISO 27001 já exige evals automatizadas (KPIs definidos no RACI), mas não há implementação

## Dois alvos de avaliação

### LLM como Desenvolvedor (L1)
Claude Code escrevendo código para a plataforma. Perguntas que o eval responde:
- O código gerado segue as convenções do CLAUDE.md?
- Queries SQLAlchemy filtram por `tenant_id`?
- Dados de negócio estão hardcodados em constantes?
- Enums fixos estão sendo usados para dados dinâmicos?
- Componentes UI usam `@agente/ui` ou shadcn direto?

### LLM como Produto (L2)
ai-engine, extractor, parecer, compliance_agent produzindo outputs para clientes. Perguntas:
- O CPF extraído está correto?
- O scoring bate com o golden set?
- Campos críticos têm citation linking?
- O Evaluator Loop detecta inconsistências injetadas?
- O parecer segue a rubrica do CLO?

## Três camadas de qualidade

| Camada | Escopo | Status |
|--------|--------|--------|
| **L0** — Estática | lint, types, unit tests | Existe nos repos alvo (ruff, mypy, pytest) |
| **L1** — Dev Agent | Claude Code gera código correto? | **Sprint 1 — implementar agora** |
| **L2** — Product AI | Outputs de IA corretos para clientes? | Schema definido, implementação quando produção existir |

**Princípio:** Schema wide, implementation narrow. Os schemas Pydantic cobrem as 3 camadas. A implementação cobre apenas L1. Schemas de L2 existem prontos.

## Taxonomia de Graders

Todos os graders seguem a mesma assinatura:
```python
grade(input, output, reference, config) → GraderResult
```

| Tipo | Pureza | Determinismo | Uso em CI |
|------|--------|-------------|-----------|
| **Determinístico** | Puro | 100% reproduzível | Gate (blocking) |
| **Model-based** | Impuro (API externa) | Não-determinístico | DECISÃO PENDENTE |
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

## Gate Fase 1 — Mapeamento

Os 13 critérios do Gate Fase 1 (Confluence ADA) mapeados para graders:

| # | Critério | Target | Grader | Automatizável |
|---|----------|--------|--------|--------------|
| 1 | Classification accuracy | >= 90% | accuracy over golden set | Sim (L2) |
| 2 | Extraction accuracy P0 | >= 95% | field_f1 per field | Sim (L2) |
| 3 | Citation linking coverage | 100% | field_not_empty on citation | Sim (L2) |
| 4 | Evaluator detection | >= 80% | Red team suite | Sim (L2) |
| 5 | AI cost per journey | <= R$50 | numeric_range | Sim (L2) |
| 6 | Audit trail coverage | 100% | Schema completeness | Sim (L1/L2) |
| 7 | Security P0 | Zero | SAST (fora do eval) | Parcial (L0) |
| 8 | SLA P95 | < 10 min | numeric_range | Sim (L2) |
| 9 | Real analyses Pine | >= 10 | Manual | Não |
| 10 | Pine NPS | >= 40 | Manual | Não |
| 11 | Proposta comercial | Enviada | Manual | Não |
| 12 | Score formula CLO | Assinada | Manual | Não |
| 13 | UI compliance | Zero violations | Manual | Não |

**Foco Sprint 1:** Critérios 6 (audit trail via L1 graders) + infraestrutura de graders para quando L2 existir.

## Task Specification

Cada tarefa de avaliação é um arquivo YAML:

```yaml
task_id: extraction.matricula.cpf_proprietario
category: extraction       # classification | extraction | decision | citation | cost | latency
component: ai-engine       # serviço avaliado
layer: L2                  # L1 | L2
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

scoring_mode: weighted     # weighted | binary | hybrid
pass_threshold: 0.95
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

## Classificação de risco de PR (futuro)

| Nível | Critério | Ação |
|-------|----------|------|
| Low | Todos os graders determinísticos passam, nenhum arquivo em zona perigosa | Candidato a fast-track review |
| Medium | Toca áreas de julgamento (prompts, rubrics, agent configs) | Review humano focado |
| High | Toca auth, billing, LGPD, core logic, infra | Review humano completo |

## Roadmap de Maturidade

| Estágio | Nome | O que faz |
|---------|------|-----------|
| 0 | Manual | Checklists em planilha. Onde estamos hoje. |
| 1 | Gate Básico | Graders determinísticos rodam no CI. **Meta Sprint 1.** |
| 2 | Classificação | Graders classificam risco de PR. Sprint 2. |
| 3 | Observabilidade Semântica | Graders rodam em produção como sampling. Quando L2 existir. |
| 4 | Resposta Automatizada | Triggers automáticos (rollback, alert, escalation). Futuro. |
| 5 | Flywheel Autônomo | Evals geram dados que melhoram evals. Aspiracional. |

## Anti-patterns

| Anti-pattern | Por que é ruim | O que fazer |
|-------------|---------------|-------------|
| Mock que copia expected | Tautologia — grader compara output consigo mesmo | Golden set real, anotado por humano |
| Grader que sempre passa | Falsa segurança | Incluir red team cases que DEVEM falhar |
| 100% model-based | Custo alto, não-determinístico, flaky CI | Máximo de determinísticos, model-based apenas para julgamento semântico |
| Eval sem calibração | Mede algo, mas não se sabe o quê | Cohen's κ >= 0.75 antes de confiar |
| Schema sem implementação | Engenharia no vácuo | Schema wide, implement narrow — OK ter schema L2 sem tasks L2 |

## Decisões pendentes

| # | Decisão | Trade-off | Status |
|---|---------|-----------|--------|
| 1 | LLM-judge no CI: blocking vs informative | Blocking: mais seguro, risco de flaky. Informative: menos atrito, risco de ignorar. | PENDENTE |
| 2 | Runner: pytest vs CLI customizado | pytest: integra com CI. Custom: mais flexível, mais manutenção. | PENDENTE |
| 3 | Sprint: dedicado vs diluído | Dedicado: mais rápido, compete com Gate. Diluído: menos impacto, mais lento. | PENDENTE |
| 4 | Auto-promotion guard | Fast-track para low-risk PRs: economiza review budget. Risco: falso senso de segurança. | PENDENTE |
