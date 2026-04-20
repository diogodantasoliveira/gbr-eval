# Taxonomia de Exemplos Negativos — gbr-eval

> Data: 2026-04-19
> Baseado em: recomendações Anthropic (100-200 cases, 40% negativos)
> Status: CLO deve revisar e aprovar cada categoria

---

## Por que negativos são necessários

Os 25 golden sets atuais são **todos positivos** — documentos corretos, bem formatados, com todos os campos presentes. Isso mede apenas **recall** (o sistema extrai certo quando o documento é bom?) mas não **precision** (o sistema rejeita quando o documento é ruim?).

Um extractor que retorna "positiva" para tudo teria 100% de recall e 0% de precision no set atual.

---

## 4 Categorias de Negativos

### 1. Confuser (classificação incorreta)

**O que testa:** Sistema recebe documento de tipo A mas deveria classificar como tipo B. O sistema deve rejeitar.

**Estrutura do case:**
```json
{
  "case_number": 101,
  "tags": ["negative", "confuser", "<tipo_real>_como_<tipo_esperado>"],
  "expected_output": {
    "document_type": "<tipo_real_do_documento>"
  }
}
```

**Confusers por skill:**

| Skill alvo | Confuser | Por que confunde |
|-----------|----------|-----------------|
| matricula_v1 | IPTU | Ambos referenciam imóvel com endereço e número |
| matricula_v1 | Escritura de compra e venda | Descreve mesmo imóvel com dados semelhantes |
| cnd_v1 | Certidão de casamento | "Certidão" no título, layout oficial similar |
| cnd_v1 | Certidão de distribuição cível | Formato quase idêntico, órgão emissor diferente |
| contrato_social_v1 | Alteração contratual | Referencia mesma empresa, CNPJ, sócios |
| contrato_social_v1 | Estatuto social (S.A.) | Estrutura similar mas regime jurídico diferente |
| procuracao_v1 | Substabelecimento | Transfere poderes mas não é procuração original |
| procuracao_v1 | Termo de representação | Outorga poderes mas não é instrumento notarial |
| certidao_trabalhista_v1 | Certidão cível | Formato similar, tribunal diferente |
| certidao_trabalhista_v1 | Certidão criminal | Mesmo layout judiciário, matéria diferente |

### 2. Edge case (extração parcial)

**O que testa:** Documento é do tipo correto mas tem campos ausentes, incompletos, ou em formato atípico.

**Estrutura do case:**
```json
{
  "case_number": 201,
  "tags": ["negative", "edge_case", "<campo_ausente>"],
  "expected_output": {
    "document_type": "<tipo_correto>",
    "<campo_ausente>": null,
    "<campo_presente>": "<valor>"
  }
}
```

**Edge cases por skill:**

| Skill | Edge case | Descrição |
|-------|-----------|-----------|
| matricula_v1 | Matrícula muito antiga | Formato anterior à Lei 6.015/73, campos em texto corrido |
| matricula_v1 | Matrícula com 50+ registros | Muitas averbações, performance de extração |
| cnd_v1 | CND vencida | Validade expirada — campo correto mas significado diferente |
| cnd_v1 | CND sem CNPJ visível | Emitida por CPF sem constar CNPJ |
| contrato_social_v1 | Contrato sem capital social | Capital não mencionado (empresas antigas) |
| contrato_social_v1 | 10+ sócios | Array grande, teste de completude |
| procuracao_v1 | Procuração revogada | Válida na forma mas juridicamente ineficaz |
| procuracao_v1 | Poderes genéricos (ad negotia) | Sem poderes específicos listados |
| certidao_trabalhista_v1 | Sem validade expressa | TRT-2 não coloca validade |
| certidao_trabalhista_v1 | 100+ processos | Volume alto, teste de completude do array |

### 3. Degraded (qualidade ruim)

**O que testa:** Documento é do tipo correto mas a qualidade de input é baixa (OCR ruim, scan cortado, etc.).

**Estrutura do case:**
```json
{
  "case_number": 301,
  "tags": ["negative", "degraded", "<tipo_degradacao>"],
  "expected_output": {
    "document_type": "<tipo_correto>",
    "<campo_ilegivel>": null
  },
  "notes": "Scan com [tipo de degradação]. Campos X e Y ilegíveis."
}
```

**Tipos de degradação:**
- `ocr_ruim` — texto reconhecido com erros
- `scan_cortado` — parte do documento fora da área de scan
- `baixa_resolucao` — 72dpi ou menos
- `manchas` — marcas d'água, carimbos sobre texto
- `foto_celular` — ângulo, sombra, reflexo

### 4. Adversarial (fraude/adulteração)

**O que testa:** Documento foi intencionalmente alterado para enganar o sistema.

**Status: BLOCKED** — depende do ai-engine implementar `authenticity_flag`.

**Planned cases (golden/red_team/):**
- Matrícula com proprietário alterado digitalmente
- CND vencida com data editada
- Contrato social com sócios fantasma
- Procuração revogada apresentada como válida
- Balanço com valores inflados

---

## Numeração de cases

| Range | Categoria | Exemplo |
|-------|-----------|---------|
| 001-099 | Positivos (seed + sintéticos) | case_001.json a case_099.json |
| 100-199 | Confusers | case_101.json (confuser IPTU) |
| 200-299 | Edge cases | case_201.json (sem validade) |
| 300-399 | Degraded | case_301.json (OCR ruim) |
| 400-499 | Adversarial | case_401.json (adulterado) |

---

## Tags obrigatórias para negativos

Todo case negativo DEVE ter:
- `negative` — marca como exemplo negativo
- Uma tag de categoria: `confuser`, `edge_case`, `degraded`, ou `adversarial`
- Tag descritiva do cenário específico

**Exemplo completo de tags para confuser:**
```
["negative", "confuser", "iptu_como_matricula", "pj", "cliente_a"]
```

---

## Distribuição alvo (200 cases total)

| Categoria | Quantidade | % |
|-----------|-----------|---|
| Positivos reais (seed) | 25 | 12.5% |
| Positivos sintéticos | 75 | 37.5% |
| Confusers | 30 | 15% |
| Edge cases | 30 | 15% |
| Degraded | 20 | 10% |
| Adversariais | 20 | 10% |

---

## Processo de anotação

1. **CLO identifica** documentos no backoffice que se encaixam em cada categoria
2. **CLO anota** expected_output com os valores corretos (inclusive null para campos ausentes)
3. **CLO anonimiza** PII conforme regras LGPD existentes
4. **Claude assiste** como reviewer (nunca como validador)
5. **Case comitado** com tags descritivas e metadata completo

Para confusers de classificação, é aceitável criar cases sintéticos (confirmado Anthropic) marcados como `"source": "synthetic"`.

---

## Compatibilidade com framework

O framework já suporta negativos nativamente:
- Graders são agnósticos — `exact_match` verifica igualdade, não "tipo de teste"
- `expected_output` define o que é correto — confusers têm `document_type` diferente do skill alvo
- Self-eval funciona — copia expected_output para output e compara
- Nenhuma alteração de código necessária
