# Plano de Desenvolvimento Eval-First — Projeto Caixa Econômica Federal

> **Versão:** 1.0 | **Data:** 2026-04-24 | **Owner:** Diogo Dantas (CAIO)
> **Premissa:** Tudo que está neste plano segue a metodologia eval-first — os critérios de qualidade existem ANTES do código que será avaliado.

---

## 1. Contexto do Edital

A CAIXA contratará até 3 empresas simultâneas para BPO documental (front/middle/backoffice). Modelo 100% variável — remuneração condicionada a níveis de serviço (NS) e qualidade (NQ).

| Dimensão | Valor |
|----------|-------|
| Volume anual | ~25,9M demandas / ~480,9M análises de regras |
| Vigência | 24 meses, renovável |
| Operação | 24×7×365 |
| Disponibilidade mínima | 99,5% |
| Documentos/ano | ~19,6M (tratamento + classificação + extração) |
| Tipos documentais | 32 tipos, 12 famílias |
| Critério de julgamento | Menor preço, atendidos requisitos técnicos |
| Processos atendidos | 12 (Pé de Meia, Conta Digital, Habitacional, Agro, etc.) |

### Vedações relevantes

- **Não é licenciamento de software** — é contrato de SERVIÇO exclusivamente.
- CAIXA redistribui volumes entre contratadas unilateralmente, com base em desempenho.
- Melhoria contínua obrigatória SEM reajuste de preço.

---

## 2. Pipeline de Serviços

```
                    ┌─────────────────────────────────────────────────────────┐
                    │            JORNADAS AUTOMATIZADAS (orquestrador)        │
                    └─────┬──────┬───────┬──────────┬──────────┬─────────┬───┘
                          │      │       │          │          │         │
                          ▼      ▼       ▼          ▼          ▼         ▼
┌────────────┐    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌──────────┐
│ Tratamento │───▶│Classifi- │─▶│ Extração │─▶│Validação │  │Consul│  │  Regras   │
│  Arquivo   │    │  cação   │  │ de Dados │  │Autentici-│  │ ta   │  │Negociais │
│  Digital   │    │Documental│  │          │  │  dade    │  │Bases │  │          │
└────────────┘    └──────────┘  └────┬─────┘  └──────────┘  └──────┘  └──────────┘
                                     │                                      │
                                     └──────────────────────────────────────┘
                                      Extração alimenta Regras (não remunerado)
```

### Dependências de efeito cascata

| Erro em... | Propaga para... | Efeito |
|-----------|----------------|--------|
| Tratamento | Classificação, Extração, tudo | Imagem distorcida = OCR falha |
| Classificação | Extração, Validação, Regras | Schema errado selecionado |
| Extração | Regras, Validação, Consulta | Campos incorretos ou faltantes |
| Validação | Regras compostas | Score de fraude errado |

---

## 3. Volumetria por Serviço

| Serviço | Volume/ano | Remunerado? | SLA mais agressivo |
|---------|-----------|-------------|-------------------|
| Tratamento de Arquivo | 19.659.587 | Sim | 1h (Pé de Meia) |
| Classificação Documental | 19.659.587 | Sim | 1h |
| Extração de Dados | 19.659.587 (real: ~100M+) | Só quando produto final | 1h |
| Validação Autenticidade | 14.418.118 | Sim | 1h |
| Regras Simples | 96.151.084 validações | Sim | 1h |
| Regras Compostas | 1.690.623 validações | Sim | 18h |
| Consulta Bases Externas | 350.487 | Sim + ressarcimento | 1h |

**Alerta financeiro:** Extração como etapa preparatória para regras NÃO é remunerada. Volume real de extração pode ser 5× o volume remunerado (~100M+ OCR/ano vs. 19,6M pagas).

---

## 4. Metas de Qualidade (do Edital)

### 4.1 Acurácia por serviço

| Serviço | Métrica | Meta |
|---------|---------|------|
| Classificação | Acurácia top-1 geral | >= 95% |
| Classificação | Acurácia alta frequência (RG, CNH, Selfie, Residência) | >= 98% |
| Classificação | Taxa "não classificado" | <= 3% |
| Classificação | Falso positivo (alta confiança) | <= 1% |
| Extração | Field-level accuracy (simples) | >= 97% |
| Extração | Field-level accuracy (complexos) | >= 92% |
| Extração | Character Error Rate | <= 2% |
| Extração | Completude campos obrigatórios | >= 98% |
| Autenticidade | True Positive Rate (sensibilidade) | >= 95% |
| Autenticidade | True Negative Rate (especificidade) | >= 98% |
| Autenticidade | False Positive Rate | <= 2% |
| Autenticidade | Face matching 1:1 | >= 99% |
| Autenticidade | Liveness detection | >= 97% |
| Regras Simples | Acurácia | >= 99% |
| Regras Compostas | Acurácia | >= 95% |
| Consulta Bases | Taxa de sucesso | >= 95% |
| Tratamento | Acerto correção inclinação | >= 95% |
| Tratamento | Acerto separação mosaico | >= 95% |
| Tratamento | Acerto orientação | >= 98% |

### 4.2 Latências exigidas (P95)

| Serviço | Doc simples | Doc complexo |
|---------|-------------|-------------|
| Classificação | < 2s | < 5s |
| Extração | < 5s | < 60s |
| Autenticidade | < 5s | < 30s |
| Regra Simples | < 500ms | N/A |
| Regra Composta | N/A | < 30s |
| Consulta Bases (online) | < 10s | N/A |

### 4.3 Penalidades

- **Indisponibilidade (DI):** `DI = VSETF × FAIDS`
- **Serviço incorreto (VDSI):** `VDSI = 0,05% × SI × VSETF`, teto 10% do VSETF
- **Segurança:** 10% do faturamento mensal (mais severa)
- **Efeito multiplicador:** erro em uma etapa gera penalidades cascata nas etapas downstream

---

## 5. O que o gbr-eval já tem vs. o que falta

### 5.1 Golden sets existentes

| Document type | Cases | Status | Reutilizável para Caixa? |
|--------------|-------|--------|-------------------------|
| matricula | 8 | Seed completo | Sim — expandir campos (cadeia dominial, averbações) |
| contrato_social | 8 | Seed completo | Sim — expandir campos (NIRE, cláusulas decisão) |
| cnd | 8 | Seed completo | Parcial — verificar se Caixa usa CND |
| procuracao | 8 | Seed completo | Parcial |
| certidao_trabalhista | 8 | Seed completo | Parcial |
| balanco | 0 | Bloqueado | Não |
| red_team | 0 | Bloqueado (falta authenticity_flag) | Sim — desbloquear |

**Total existente:** 40 cases em 5 doc types.
**Necessário para Caixa:** ~247 cases em 32 doc types.

### 5.2 Graders existentes

| Grader | Tipo | Suficiente? |
|--------|------|------------|
| `exact_match` | Determinístico | Sim |
| `numeric_range` | Determinístico | Sim |
| `numeric_tolerance` | Determinístico | Sim |
| `regex_match` | Determinístico | Sim |
| `field_not_empty` | Determinístico | Sim |
| `set_membership` | Determinístico | Sim |
| `string_contains` | Determinístico | Sim |
| `field_f1` | Determinístico | Sim — para F1 por campo |
| `pattern_required` | Engineering | Sim |
| `pattern_forbidden` | Engineering | Sim |
| `convention_check` | Engineering | Sim |
| `decimal_usage` | Engineering | Sim |
| `subprocess` | Subprocess | Sim |
| `haiku_triage` | LLM (Haiku) | Sim |
| `llm_judge` | LLM (Sonnet) | Sim |
| `engineering_judge` | LLM (Opus) | Sim |

### 5.3 Graders novos necessários

| Grader | Tipo | Propósito | Serviços |
|--------|------|-----------|----------|
| `checklist_completeness` | Determinístico | 100% itens do checklist avaliados | Regras Negociais |
| `multi_step_calculation` | Determinístico | Valida cada etapa de cálculo composto | Regras Compostas |
| `cross_document_match` | Determinístico | Campo doc A == campo doc B | Autenticidade, Regras |
| `array_sum_match` | Determinístico | Soma de array == total esperado | Extração (holerite) |
| `fuzzy_name_match` | Determinístico | Jaro-Winkler >= threshold com normalização | Regras Simples, Consulta Bases |
| `classification_accuracy` | Agregado | Acurácia global sobre golden set completo | Classificação |
| `semantic_interpretation` | LLM-judge | Interpretação de texto jurídico (ônus, poderes) | Regras Compostas |
| `workflow_steps` | Determinístico | Etapas executadas na ordem correta | Jornadas |

---

## 6. Tipologia Documental Caixa (32 tipos)

### 6.1 Por dificuldade de classificação

**FÁCIL (8 tipos) — layout padronizado, alta frequência:**
RG, CNH, Selfie, IPTU, Nota Fiscal, CRLV, Modelo Padrão Caixa, Comprovante Residência

**MÉDIO (9 tipos) — variação de emissor:**
Certidão Estado Civil, Certidão Matrícula Imóvel, Holerite, IRPF, Alvará de Construção, Registro CREA, Apólice de Seguro, Extrato Bancário, Certidão Ônus Imóvel

**DIFÍCIL (11 tipos) — subtipos que se confundem:**
Contrato Comercial, Contrato Comercial Registrado, Contrato Habitacional, Contrato Arrendamento, Documento Constitutivo, Parecer Jurídico, Plano de Negócios, Laudo de Avaliação, Laudo de Vistoria, Licenciamento Ambiental, Constituição de Garantia

**MUITO DIFÍCIL (4 tipos) — ambiguidade semântica:**
Comprovante de Faturamento (confunde com Extrato/Holerite), Certidões Rurais (DAP/CAF/CCIR/ITR/CAR), Registro Sanitário, Documento de Margem

### 6.2 Pares de confusão prioritários

| Par | Risco |
|-----|-------|
| Holerite ↔ Extrato ↔ Comprovante Faturamento | Muito alto — ambiguidade semântica |
| Contrato Comercial ↔ Registrado ↔ Habitacional ↔ Arrendamento | Alto — subtipos sobrepostos |
| Certidões rurais entre si (DAP/CAF/CCIR/ITR/CAR) | Alto — visualmente similares |
| Parecer Jurídico ↔ Contrato | Alto — texto corrido |
| Laudo Avaliação ↔ Laudo Vistoria | Médio — layouts similares |
| Selfie ↔ Foto do RG | Médio — impacta biometria |

---

## 7. Detalhamento por Serviço

### 7.1 Tratamento de Arquivo Digital

**O que faz:** Recebe scans brutos e aplica correções (deskew, rotação, mosaico, bordas, recorte). Primeiro serviço do pipeline.

**10 operações obrigatórias:**
1. Correção de posição (deskew)
2. Separação de mosaicos
3. Rotação automática
4. Remoção de bordas
5. Eliminação de áreas não úteis
6. Mosaico com classificação (filtrar por tipologia)
7. Avaliação de conformidade (recusa com motivo)
8. Retorno do arquivo tratado vinculado ao ID
9. Respeito à extensão de arquivo (CAIXA define formato)
10. Documentos multipaginados (TIFF/PDF)

**Formatos:** PDF, TIFF, PNG, BMP, JPEG

**Decisão arquitetural para eval:** Golden sets baseados em **metadados de resultado** (JSON), não comparação pixel-a-pixel de imagens. O eval verifica se o serviço REPORTA corretamente o que fez.

**Tasks a criar (10):**

| Task ID | Operação | Graders |
|---------|----------|---------|
| `caixa.tratamento.deskew` | Correção de inclinação | `numeric_range` (ângulo residual < 0.5°) |
| `caixa.tratamento.rotacao` | Detecção de orientação | `exact_match` (orientação correta) |
| `caixa.tratamento.mosaico_count` | Separação de mosaico | `exact_match` (contagem de docs) |
| `caixa.tratamento.mosaico_classificado` | Mosaico com filtragem | `exact_match` (tipos retidos) |
| `caixa.tratamento.bordas` | Remoção de bordas | `field_not_empty` (área útil definida) |
| `caixa.tratamento.formato_saida` | Formato correto | `exact_match` (extensão) |
| `caixa.tratamento.multipaginas` | Documento multipaginado | `exact_match` (formato TIFF/PDF) |
| `caixa.tratamento.recusa` | Recusa com motivo | `field_not_empty` (motivo) + `set_membership` |
| `caixa.tratamento.cheque` | Conformidade BACEN | `checklist_completeness` |
| `caixa.tratamento.preservacao` | Resolução >= 95% da original | `numeric_range` |

**Golden sets (14 cenários):**
Doc reto (idempotência), inclinado 5-15°, rotacionado 180°, bordas pretas, mosaico 2 docs (RG frente+verso), mosaico com classificação (3 docs, 1 tipologia), multipáginas→TIFF único, multipáginas→separadas, formato preservado (PNG), cheque, ilegível (recusa), scan baixa qualidade, doc com foto (CNH 3×4), volume de pico (stress).

---

### 7.2 Classificação Documental

**O que faz:** Identifica a qual dos 32 tipos um documento pertence. Roteador lógico do pipeline.

**Metas críticas:**
- Acurácia geral top-1 >= 95%
- Alta frequência (RG, CNH, Selfie, Residência) >= 98%
- Taxa "não classificado" <= 3%
- Falso positivo com alta confiança <= 1%
- Latência P95 < 2s

**Tasks a criar (~47):**

| Categoria | Quantidade | Descrição |
|-----------|-----------|-----------|
| Classificação por tipo | 32 | 1 task por tipo documental |
| Confusers | 15 | Pares de confusão (seção 6.2) |

**Golden sets prioritários:**

| Prioridade | Tipos | Cases/tipo | Total | Justificativa |
|-----------|-------|-----------|-------|---------------|
| P0 | RG, CNH, Selfie, Residência | 8-10 | ~36 | 53% do volume |
| P1 | Holerite, Extrato, Certidão EC, IRPF, Contrato Habitacional | 6-8 | ~35 | 30% do volume |
| P2 | 23 tipos restantes | 3-5 | ~90 | 17% do volume, alta complexidade |
| Confusers | 6 pares | 4-6 | ~30 | Risco de erro cascata |

**Novo grader necessário:** `classification_accuracy` — agrega acurácia sobre todo o golden set (não apenas por task individual). Gate Fase 1 exige "Classification >= 90%" como critério global.

---

### 7.3 Extração de Dados

**O que faz:** OCR/ICR + IA para transformar documentos não-estruturados em campos estruturados (nome, valor, confiança, bounding box).

**10 tipos detalhados no edital com campos:**

| Tipo | Campos | Complexidade | Técnica principal |
|------|--------|-------------|------------------|
| RG | 12 (nome, CPF, RG, filiação, nascimento, foto 3×4, assinatura...) | Baixa-Média | OCR + template matching |
| CNH | 11 (nome, CPF, CNH, categoria, validade, foto, QR code...) | Baixa-Média | OCR + template matching |
| Matrícula Imóvel | 12 (número, proprietário, CPF, endereço, ônus, averbações...) | Muito Alta | OCR + LLM (texto jurídico) |
| Contrato Social | 10 (razão social, CNPJ, sócios[], capital, poderes, objeto...) | Muito Alta | OCR + NLP + LLM |
| Holerite | 11 (empresa, competência, salário bruto, descontos[], líquido...) | Média | OCR + table extraction |
| IRPF | 13 (CPF, nome, rendimentos, bens[], dívidas[], dependentes[]...) | Muito Alta | OCR + table extraction |
| Comp. Residência | 8 (nome, endereço, CEP, data, concessionária...) | Baixa | OCR + regex |
| Apólice de Seguro | 10 (seguradora, vigência, coberturas[], beneficiário, prêmio...) | Média-Alta | OCR + NLP |
| Laudo de Avaliação | 12 (avaliador, CREA, valor, endereço, coordenadas, fotos...) | Média-Alta | OCR + NLP + table extraction |
| Nota Fiscal | 10 (emitente, CNPJ, chave 44 dígitos, itens[], total...) | Média | OCR + template + regex |

**Total estimado:** ~190 milhões de campos individuais/ano.

**Campos de complexidade "Muito Alta" (risco financeiro):**
- Ônus e gravames (Matrícula) — hipotecas, penhoras, indisponibilidades
- Averbações (Matrícula) — histórico completo
- Quadro societário (Contrato Social) — nomes, CPFs, % participação, cargos
- Poderes de administração (Contrato Social) — quem pode assinar, limites
- Bens e direitos (IRPF) — tabela completa com valores
- Coberturas (Apólice) — tipos e valores por cobertura

**Tasks a criar (10):**

| Task ID | Doc type | Campos | Graders |
|---------|---------|--------|---------|
| `caixa.extracao.rg` | RG | 12 | `field_f1`, `exact_match` (CPF), `field_not_empty` (foto) |
| `caixa.extracao.cnh` | CNH | 11 | `field_f1`, `exact_match` (CPF/CNH) |
| `caixa.extracao.matricula` | Matrícula | 12 | `field_f1`, `llm_judge` (ônus/averbações) |
| `caixa.extracao.contrato_social` | Contrato Social | 10 | `field_f1`, `llm_judge` (poderes/sócios) |
| `caixa.extracao.holerite` | Holerite | 11 | `field_f1`, `array_sum_match` (descontos) |
| `caixa.extracao.irpf` | IRPF | 13 | `field_f1`, table mode (bens, dívidas) |
| `caixa.extracao.residencia` | Comp. Residência | 8 | `field_f1`, `exact_match` (CEP) |
| `caixa.extracao.apolice` | Apólice | 10 | `field_f1`, `field_not_empty` (cláusula CAIXA) |
| `caixa.extracao.laudo` | Laudo | 12 | `field_f1`, `numeric_tolerance` (valor) |
| `caixa.extracao.nf` | Nota Fiscal | 10 | `field_f1`, `exact_match` (chave 44) |

**Golden sets:** 8 cases mínimo por tipo. Expandir matrícula e contrato_social com campos faltantes (cadeia dominial, cláusulas de decisão, NIRE).

---

### 7.4 Validação de Autenticidade

**O que faz:** Verifica autenticidade de documentos com score composto de fraude (0.0-1.0). 100% automatizado.

**4 dimensões do score:**

| Dimensão | Peso sugerido | Verificações |
|----------|-------------|-------------|
| Suporte (integridade da imagem) | 25% | Consistência de fontes, ELA, metadados, resolução, marcas d'água, iluminação |
| Conteúdo (dados consistentes) | 35% | CPF válido, nome vs base, data plausível, órgão emissor real |
| Biometria (face match) | 25% | Face match 1:1/1:N, liveness, deepfake detection |
| Cruzamento dossiê | 15% | Nome RG vs holerite, CPF RG vs IRPF, foto vs selfie |

**Faixas de score:**
- Verde (0.85-1.00): aprovado automaticamente
- Amarelo (0.60-0.84): revisão humana
- Vermelho (0.00-0.59): rejeitado

**Tasks a criar (~10):**

| Task ID | Dimensão | Graders |
|---------|----------|---------|
| `caixa.autenticidade.score_composicao` | Score final | `numeric_tolerance` (soma ponderada) |
| `caixa.autenticidade.threshold_verde` | Faixa verde | `exact_match` (classificação) |
| `caixa.autenticidade.threshold_vermelho` | Faixa vermelha | `exact_match` (classificação) |
| `caixa.autenticidade.suporte_edicao` | Detecção de edição | `exact_match` (detected_tampering) |
| `caixa.autenticidade.conteudo_cpf` | Validação CPF | `exact_match` (cpf_valido) |
| `caixa.autenticidade.biometria_match` | Face match | `numeric_range` (similaridade >= 0.99) |
| `caixa.autenticidade.biometria_liveness` | Liveness | `exact_match` (live=true) |
| `caixa.autenticidade.cruzamento_dossie` | Cross-doc | `cross_document_match` (nome, CPF) |
| `caixa.autenticidade.redistribuicao_pesos` | Sem biometria | `numeric_tolerance` (pesos redistribuídos) |
| `caixa.autenticidade.red_team` | Adversarial | `classification_accuracy` (detection rate >= 80%) |

**Golden sets (25 cases):**
- 5 docs autênticos boa qualidade (evitar falso positivo)
- 5 fraudes de suporte (foto substituída, texto editado, metadados adulterados)
- 5 fraudes biométricas (foto de foto, foto de tela, deepfake, face de terceiro)
- 5 fraudes de conteúdo (CPF inválido, nome trocado, valores inflados)
- 5 cruzamento divergente (nome RG ≠ holerite, CPF ≠ base)

**Pré-requisito bloqueante:** Implementar `authenticity_flag` no ai-engine para desbloquear `golden/red_team/`.

---

### 7.5 Regras Negociais

**O que faz:** Aplica lógica de negócio sobre dados extraídos. Maior volume do edital.

#### 7.5.1 Regras Simples (96,1M validações/ano)

Critério único, sem encadeamento, resultado direto.

**13 exemplos do TR, agrupados em 5 padrões:**

| Padrão | Exemplos TR | Grader |
|--------|------------|--------|
| Campo >= threshold | Idade >= 18, data emissão em 90 dias, valor <= teto | `numeric_range` |
| Campo == dado lógico | Nome confere, CPF confere, CNPJ confere, razão social | `fuzzy_name_match`, `exact_match` |
| Presença de elemento | Assinatura presente, checkbox marcado, local/data preenchidos | `field_not_empty` |
| Tipo confere | Tipo classificado == tipo esperado | `exact_match` |
| Cruzamento pontual | Nome RG == Nome Requerimento | `cross_document_match` |

**Tasks a criar (7):**

| Task ID | Padrão | Graders |
|---------|--------|---------|
| `caixa.regra_simples.idade_threshold` | Campo >= threshold | `numeric_range` |
| `caixa.regra_simples.validade_documento` | Campo >= threshold | `numeric_range` |
| `caixa.regra_simples.nome_confere` | Campo == dado lógico | `fuzzy_name_match` |
| `caixa.regra_simples.cpf_cnpj_confere` | Campo == dado lógico | `exact_match` |
| `caixa.regra_simples.presenca_elemento` | Presença | `field_not_empty` |
| `caixa.regra_simples.tipo_confere` | Tipo confere | `exact_match` |
| `caixa.regra_simples.cruzamento_pontual` | Cruzamento | `cross_document_match` |

#### 7.5.2 Regras Compostas (1,7M validações/ano)

Múltiplos critérios interdependentes. LLM obrigatório para 2 dos 5 exemplos.

**5 exemplos do TR:**

| Regra | Complexidade | Tecnologia | Graders |
|-------|-------------|-----------|---------|
| Poderes societários (contrato social) | Alta | LLM obrigatório | `semantic_interpretation` |
| Conferência de valores (holerite) | Média | Table extraction + math | `multi_step_calculation`, `array_sum_match` |
| Margem consignável | Média-Alta | Math multi-fonte | `multi_step_calculation` |
| Ônus na matrícula | Muito Alta | LLM obrigatório | `semantic_interpretation` |
| Conformidade agrícola | Alta | Workflow/DAG | `checklist_completeness`, `workflow_steps` |

**Tasks a criar (5 + 3 consolidação):**

| Task ID | Regra | Graders |
|---------|-------|---------|
| `caixa.regra_composta.poderes_contrato` | Poderes societários | `semantic_interpretation` |
| `caixa.regra_composta.somatorio_holerite` | Conferência valores | `multi_step_calculation`, `array_sum_match` |
| `caixa.regra_composta.margem_consignavel` | Margem | `multi_step_calculation` |
| `caixa.regra_composta.onus_matricula` | Ônus/impedimentos | `semantic_interpretation` |
| `caixa.regra_composta.conformidade_agro` | Conformidade agrícola | `checklist_completeness`, `workflow_steps` |
| `caixa.regras.checklist_completo` | 100% itens | `checklist_completeness` |
| `caixa.regras.taxa_inconclusivo` | <= 5% | `numeric_range` |
| `caixa.regras.resultado_consolidado` | CONFORME/NÃO_CONFORME | `exact_match` |

**Golden sets (40 cases):**
- 5 cases por regra composta (2 CONFORME + 2 NÃO_CONFORME + 1 INCONCLUSIVO) = 25
- 15 cases para regras simples (cobrindo os 5 padrões × 3 cenários)

**Pré-requisito:** Especialista jurídico para anotar golden sets de matrícula (ônus) e contrato social (poderes).

---

### 7.6 Consulta a Bases Externas

**O que faz:** Consulta bases públicas e privadas para validação ou obtenção de dados. Dois sub-serviços.

**Bases públicas (gratuitas):** Receita Federal (CPF, CNPJ), SEFAZ (NF-e), TSE, Correios (CEP), DETRAN (27 estaduais)
**Bases privadas (com custo):** Serasa (R$0,50-5,00), Registros de Imóveis (R$30-80), Junta Comercial (R$10-50)

**Tasks a criar (6):**

| Task ID | Base | Sub-serviço | Graders |
|---------|------|------------|---------|
| `caixa.consulta.validacao_cpf` | RF | Validação | `exact_match` (situação), `fuzzy_name_match` (nome) |
| `caixa.consulta.validacao_cnpj` | RF | Validação | `exact_match` (situação), `field_f1` (sócios) |
| `caixa.consulta.validacao_nfe` | SEFAZ | Validação | `exact_match` (status) |
| `caixa.consulta.disponibilizacao_matricula` | RI | Disponibilização | `field_not_empty` (arquivo_id) |
| `caixa.consulta.disponibilizacao_junta` | Junta | Disponibilização | `field_f1` (sócios, capital) |
| `caixa.consulta.dnf_impossibilidade` | Qualquer | DNF | `field_not_empty` (motivo), `set_membership` |

**Golden sets (20 cases):** Match correto, match divergente, base indisponível (DNF), dados parciais, CPF falecido, CNPJ em baixa, NF-e cancelada.

---

### 7.7 Jornadas Automatizadas (Orquestrador)

**O que faz:** Conecta e coordena todos os serviços em jornadas end-to-end. Camada transversal — NÃO tem item próprio de receita.

**7 capacidades obrigatórias:**
1. Parametrização dinâmica (checklist, etapas, formulários)
2. Automação inteligente com IA
3. Autonomia da CAIXA (sem intervenção técnica)
4. Low-code/no-code para construção de fluxos
5. Interfaces interativas (portal interno + externo)
6. Integração com sistemas CAIXA (SOAP, REST, AMQP, IBM MQ)
7. Governança e curadoria

**3 padrões de complexidade:**

| Padrão | Exemplo | Docs | Regras | SLA |
|--------|---------|------|--------|-----|
| Mínimo | Pé de Meia | 2 (ID + Selfie) | 2-3 simples | 1h |
| Simples | Abertura Conta PF | 3 (RG + Selfie + Residência) | ~5 simples | 1h |
| Complexo | Concessão Habitacional | ~10 (RG, IRPF, Holerite, Matrícula, Laudo...) | ~12 simples + ~8 compostas | 24h |

**Tasks a criar (4 jornadas + 4 operacionais):**

| Task ID | Jornada | Graders |
|---------|---------|---------|
| `caixa.jornada.pe_de_meia` | 2 docs, 2-3 regras, 1h | `workflow_steps`, `exact_match` (resultado), `numeric_range` (tempo) |
| `caixa.jornada.abertura_conta` | 3 docs, 5 regras, 1h | `workflow_steps`, `checklist_completeness` |
| `caixa.jornada.habitacional` | ~10 docs, ~20 regras, 24h | `workflow_steps`, `checklist_completeness`, `cross_document_match` |
| `caixa.jornada.agronegocio` | 4 docs, 6 sub-verificações, 24h | `workflow_steps`, `checklist_completeness` |
| `caixa.jornada.sla_1h` | SLA fila prioritária | `numeric_range` (< 3600s) |
| `caixa.jornada.sla_18h` | SLA fila média | `numeric_range` (< 64800s) |
| `caixa.jornada.sla_24h` | SLA fila padrão | `numeric_range` (< 86400s) |
| `caixa.jornada.disponibilidade` | 99,5% | `numeric_range` (>= 0.995) |

**Golden sets de jornada completa (8 cases):** Combinam golden sets de documentos individuais em um dossiê com resultado esperado end-to-end.

---

## 8. Fases de Desenvolvimento

### Fase 0 — Fundação (Semana 1)

**Objetivo:** Infraestrutura. Zero golden sets — só código e estrutura.

| Entrega | Descrição |
|---------|-----------|
| 5 novos graders | `checklist_completeness`, `multi_step_calculation`, `cross_document_match`, `array_sum_match`, `fuzzy_name_match` |
| 1 grader agregado | `classification_accuracy` |
| 1 grader LLM | `semantic_interpretation` (jurídico) |
| 1 grader workflow | `workflow_steps` |
| Estrutura de diretórios | `tasks/product/caixa/`, `golden/caixa/`, `contracts/schemas/caixa/` |
| Schemas JSON | Request/response por serviço |
| Testes unitários | Para cada grader novo |

**Critérios de aceite:**
- `uv run pytest` continua passando (758+ testes)
- Cada grader novo tem >= 5 testes unitários
- Schemas validam com o contract validator existente

---

### Fase 1 — Classificação Documental (Semanas 2-3)

**Objetivo:** Roteador lógico. Maior efeito cascata. Primeira coisa a validar.

| Entrega | Quantidade |
|---------|-----------|
| Tasks de classificação | 32 (1 por tipo) |
| Tasks de confusers | 15 (6 pares prioritários) |
| Golden sets P0 | ~36 cases (RG, CNH, Selfie, Residência) |
| Golden sets P1 | ~35 cases (Holerite, Extrato, Certidão EC, IRPF, Contrato Habitacional) |

**Gate critério:** `classification_accuracy` >= 90% sobre golden set completo.

**Dependências bloqueantes:**
- Documentos reais anonimizados para 27 tipos sem cobertura
- Definição de quais tipos são classes independentes (certidões rurais: 1 tipo ou 5?)

---

### Fase 2 — Extração de Dados (Semanas 4-6)

**Objetivo:** Motor silencioso. Alimenta todos os serviços downstream.

| Entrega | Quantidade |
|---------|-----------|
| Tasks de extração | 10 (1 por tipo detalhado) |
| Golden sets novos | ~40 cases (RG, CNH, Holerite, IRPF, Residência) |
| Golden sets expandidos | +8 cases (matrícula: cadeia dominial; contrato_social: NIRE) |
| Grader `array_sum_match` em uso | Holerite (descontos) |

**Gate critérios:**
- Field-level accuracy >= 95% (simples >= 97%, complexo >= 92%)
- CER <= 2%
- Completude campos obrigatórios >= 98%

---

### Fase 3 — Validação de Autenticidade (Semanas 5-6, paralelo com F2)

**Objetivo:** Desbloquear red_team. Score de fraude composto.

| Entrega | Quantidade |
|---------|-----------|
| Desbloquear `golden/red_team/` | Implementar authenticity_flag |
| Tasks de fraud-scoring | 10 |
| Golden sets adversariais | 25 cases (5 por dimensão + 5 autênticos) |
| Grader `cross_document_match` em uso | Cruzamento dossiê |

**Gate critério:** Detection rate >= 80% (Gate critério 4).

---

### Fase 4 — Regras Negociais (Semanas 7-9)

**Objetivo:** Maior volume. Simples (99% acurácia) e compostas (95% acurácia).

| Entrega | Quantidade |
|---------|-----------|
| Tasks regras simples | 7 |
| Tasks regras compostas | 5 |
| Tasks consolidação | 3 |
| Golden sets | ~40 cases |
| Graders em uso | `multi_step_calculation`, `checklist_completeness`, `semantic_interpretation`, `fuzzy_name_match` |

**Dependência bloqueante:** Especialista jurídico para golden sets de ônus na matrícula e poderes no contrato social.

---

### Fase 5 — Consulta a Bases Externas (Semana 10)

| Entrega | Quantidade |
|---------|-----------|
| Tasks | 6 (4 validação + 2 disponibilização) |
| Golden sets | ~20 cases |

---

### Fase 6 — Tratamento de Arquivo Digital (Semana 11)

| Entrega | Quantidade |
|---------|-----------|
| Tasks | 10 (1 por operação) |
| Golden sets | ~14 cenários |

---

### Fase 7 — Jornadas End-to-End (Semanas 12-13)

**Objetivo:** Validar pipeline completo. Combina golden sets de múltiplos serviços.

| Entrega | Quantidade |
|---------|-----------|
| Tasks jornada | 4 |
| Tasks operacionais (SLA) | 4 |
| Golden sets de jornada | ~8 cases (multi-documento) |
| Grader `workflow_steps` em uso | Validação de etapas |

---

### Fase 8 — Operational + Compliance (Semanas 14-15)

| Entrega | Quantidade |
|---------|-----------|
| Tasks operational (latência, throughput, custo) | ~15 |
| Tasks compliance (LGPD, BACEN, audit) | ~10 |

---

### Buffer + Gate Final (Semanas 16-17)

- Verificação cruzada entre todas as fases
- Regression delta contra baseline
- Trend detection para degradações progressivas
- Gate final consolidado: todos os critérios do edital mapeados

---

## 9. Cronograma Visual

```
Sem 01: ████████ Fase 0 — Fundação (graders, schemas, estrutura)
Sem 02: ████████ Fase 1 — Classificação ─────────────────┐
Sem 03: ████████ Fase 1 — Classificação (continuação)     │
Sem 04: ████████ Fase 2 — Extração ──────────────────┐    │ Dependência
Sem 05: ████████ Fase 2 + Fase 3 (paralelo)          │    │
Sem 06: ████████ Fase 2 + Fase 3 (paralelo)          │    │
Sem 07: ████████ Fase 4 — Regras ────────────────────┘────┘
Sem 08: ████████ Fase 4 — Regras (continuação)
Sem 09: ████████ Fase 4 — Regras (continuação)
Sem 10: ████████ Fase 5 — Consulta Bases
Sem 11: ████████ Fase 6 — Tratamento Arquivo
Sem 12: ████████ Fase 7 — Jornadas E2E
Sem 13: ████████ Fase 7 — Jornadas (continuação)
Sem 14: ████████ Fase 8 — Operational + Compliance
Sem 15: ████████ Fase 8 (continuação)
Sem 16: ████████ Buffer + verificação cruzada
Sem 17: ████████ Gate final consolidado
```

---

## 10. Resumo Quantitativo

| Dimensão | Total |
|----------|-------|
| Fases | 9 (0-8) |
| Duração estimada | 17 semanas |
| Tasks novos | ~132 |
| Golden cases novos | ~247 |
| Graders novos | 8 |
| Schemas de contrato | 5 (1 por serviço principal) |
| Tipos documentais cobertos | 32 (de 5 atuais) |
| Jornadas end-to-end | 4 |

---

## 11. Dependências Bloqueantes

| # | Dependência | Bloqueia | Severidade |
|---|-----------|---------|-----------|
| 1 | **Schemas de API** (request/response JSON por serviço) | Todas as fases | CRÍTICA |
| 2 | **Documentos reais anonimizados** para 27 tipos sem golden set | Fases 1-2 | CRÍTICA |
| 3 | **Authenticity flag no ai-engine** | Fase 3 (red_team) | ALTA |
| 4 | **Especialista jurídico** para anotação de matrícula/contrato | Fase 4b | ALTA |
| 5 | **Definição de thresholds pela CAIXA** (fuzzy match, faixas score) | Fases 1, 3, 4 | ALTA |
| 6 | **Tipologia final confirmada** (32 tipos? frente/verso RG? subtipos?) | Fase 1 | MÉDIA |
| 7 | **Multi-projeto no gbr-eval** (ver seção 12) | Antes de Fase 1 | ALTA |

---

## 12. Riscos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Documentos reais indisponíveis | Alta | Bloqueante | Golden sets sintéticos como placeholder, substituir por reais quando disponíveis |
| Expansão dos 32 tipos durante vigência | Média | Retrabalho | Automação: script de criação de task YAML por tipo |
| Custo de LLM para regras compostas (R$85K-850K/ano) | Alta | Margem negativa | Funnel 3-estágios: determinístico → Haiku → Opus |
| Volume de extração não remunerada (5× o remunerado) | Certa | Financeiro | Precificar considerando ~100M+ operações OCR/ano |
| Latência de bases externas (SEFAZ, RI) | Alta | SLA | Circuit breaker + cache com TTL por base |
| Deepfake detection como corrida armamentista | Alta | Escopo infinito | Baseline >= 80% detecção, atualização trimestral |
| Low-code/no-code como scope creep | Alta | Custo | Catálogo fechado de 20 operações permitidas |
| Compliance BACEN para cheques (3 normas) | Média | Multa | Mapear requisitos específicos antes de implementar |

---

## 13. Perguntas em Aberto (para validação com CAIXA/CLO)

### Classificação
1. A tipologia é exatamente 32 tipos, ou frente/verso de RG são labels separadas?
2. Certidões rurais (DAP/CAF/CCIR/ITR/CAR) são 1 tipo ou 5 tipos independentes?
3. O classificador retorna top-1 ou top-N com scores?

### Extração
4. Qual o schema de API (request/response) do endpoint de extração?
5. Documentos multipáginas: classificação pela primeira página ou por todas?
6. Recortes de imagem (foto 3×4, assinatura) são parte da extração ou serviço separado?

### Autenticidade
7. A composição do score é linear (soma ponderada) ou tem regras não-lineares?
8. Como redistribuir pesos quando biometria não se aplica (ex: holerite)?
9. Os thresholds de faixa (verde/amarelo/vermelho) são requisitos ou defaults configuráveis?

### Regras
10. Qual threshold de similaridade define que um nome "confere"? (Jaro-Winkler >= ?)
11. O resultado INCONCLUSIVO conta como falha para fins de penalidade?
12. Existem matrículas reais anotadas por jurídico para golden sets de ônus?

### Jornadas
13. Qual workflow engine será adotado (Camunda BPMN vs. Temporal code-first)?
14. O que exatamente a CAIXA pode fazer no low-code sem a contratada?
15. Demandas em andamento quando fluxo é editado: versão antiga ou nova?

### Consulta Bases
16. Qual a política de cache por tipo de base (TTL)?
17. Como distinguir consulta remunerada de embutida programaticamente?

---

## 14. Compliance e Segurança (checklist do edital)

| Requisito | Status | Ação |
|-----------|--------|------|
| LGPD — CAIXA controladora, contratada operadora | A implementar | PII sanitizada em golden sets |
| Dados em território brasileiro | A validar | Verificar localização de infra |
| TLS 1.3 obrigatório (fallback 1.2) | A implementar | Configuração de endpoints |
| AES 128 bits em repouso | A implementar | Criptografia de storage |
| FIPS 140-2 nível 3 (IaaS) / nível 2 (PaaS/SaaS) | A validar | Certificação de infra |
| Nota "A" no Qualys SSL Labs | A testar | Teste de endpoints |
| MFA obrigatório | A implementar | Autenticação de plataforma |
| Pentest anual por terceiro independente | A agendar | Sem custo para CAIXA |
| Logs retidos por 5 anos | A implementar | Política de retenção |
| Eliminação segura após 90 dias (LGPD) | A implementar | NIST SP 800-88 |
| SOC 2 Tipos 1 e 2 (semestral) | A agendar | Auditoria |
| Relatório de riscos cibernéticos anual | A agendar | Entrega para CAIXA |
