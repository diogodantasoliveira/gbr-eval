# Inventário de Skills — gbr-eval

> Mapeamento completo de tipos de documento no backoffice GarantiaBR com volume de documentos reais,
> análise de viabilidade para golden sets, e priorização por valor de negócio.
>
> **Gerado em:** 2026-04-18
> **Fonte:** sistema.garantiabr.com/backoffice (produção)
> **Método:** Enumeração exaustiva de 137 tipos de documento, contagem via filtro por tipo

---

## 1. Inventário Atual — Skills com Golden Sets

| Skill | Tipo ID | Nome no Sistema | Docs no Sistema | Cases Anotados | Status |
|-------|---------|-----------------|----------------:|---------------:|--------|
| `matricula_v1` | 135 | Certidão de Matrícula de Imóvel - Inteiro Teor | 2.212 | 5 | seed_complete |
| `contrato_social_v1` | 130 | Certidão de Inteiro Teor da Junta Comercial | 358 | 5 | seed_complete |
| `cnd_v1` | 96 | CND Federal (RFB/PGFN) | 296 | 5 | seed_complete |
| `procuracao_v1` | 146 | Certidão de Traslado de Procuração | 109 | 5 | seed_complete |
| `certidao_trabalhista_v1` | 113 | Certidão de Distribuição de Ações Trabalhistas (TRT) | 381 | 5 | seed_complete |
| `balanco_v1` | 293 | Balanço Patrimonial - Demonstrações Contábeis | **0** | 0 | **bloqueado — sem documentos** |

---

## 2. Tipos de Documento com Volume Real (não cobertos por skills existentes)

### Tier A — Alto volume, alto valor de negócio (>= 30 docs)

| Tipo ID | Nome | Docs | Valor para Crédito | Complexidade Extração | Candidato a Skill? |
|---------|------|-----:|--------------------|-----------------------|-------------------|
| 113 | Certidão de Distribuição de Ações Trabalhistas (TRT 1ª instância) | 381 | **CRÍTICO** — risco trabalhista é gate de crédito | Média: partes, vara, status, valor | **SIM — P0** |
| 101 | Certidão Cível (Justiça Estadual) | 138 | **CRÍTICO** — risco litigioso afeta parecer | Média: distribuição, comarca, status | **SIM — P0** |
| 254 | Consulta Dívida na PGFN | 37 | **CRÍTICO** — dívida ativa é bloqueante | Alta: valores, inscrições, situação | **SIM — P1** |
| 134 | Certidão de Matrícula de Imóvel - Ônus Reais | 40 | Alto — complementa matrícula inteiro teor | Média: ônus ativos, credores | Variante de `matricula_v1` |

### Tier B — Volume médio, relevância operacional (5-29 docs)

| Tipo ID | Nome | Docs | Valor para Crédito | Complexidade Extração | Candidato a Skill? |
|---------|------|-----:|--------------------|-----------------------|-------------------|
| 239 | Convenção de Condomínio | 16 | Médio — regras do imóvel, restrições de uso | Alta: cláusulas longas, tabelas de fração | Futuro (product) |
| 243 | Certidão Conjunta de Matrícula (Inteiro Teor + Ônus + Ações) | 13 | Alto — documento 3-em-1 do imóvel | Alta: combina 3 extrações | Variante de `matricula_v1` |
| 237 | Consulta de Protesto (sem valor jurídico) | 10 | **CRÍTICO** — protestos são red flag | Baixa: tabela simples | **SIM — P1** |
| 212 | CCIR (Certificado de Cadastro Imóvel Rural) | 7 | Alto — obrigatório para imóveis rurais | Baixa: campos fixos | **SIM — P2** |
| 241 | Certidão de Cadeia Dominial | 6 | Alto — histórico completo de propriedade | Muito alta: múltiplas transferências | Futuro (complexo) |
| 129 | Certidão de Inteiro Teor - Ata Eleição Administradores | 6 | Médio — confirma poderes de gestão | Média: similar a contrato social | Variante de `contrato_social_v1` |
| 98 | Certidão de Dados Cadastrais do Imóvel | 5 | Médio — dados descritivos do imóvel | Baixa: campos cadastrais fixos | Possível (P2) |

### Tier C — Volume baixo ou zero, sem viabilidade imediata (< 5 docs)

| Tipo ID | Nome | Docs | Notas |
|---------|------|-----:|-------|
| 213 | Comprovante Situação Cadastral PF/PJ | 4 | Simples demais — pouco valor de eval |
| 92 | Ata de Assembleia Registrada | 3 | Complexo mas volume insuficiente |
| 228 | CNJ - Certidão Negativa de Improbidade | 2 | Volume insuficiente |
| 211 | CND ITR (Imóvel Rural) | 1 | Volume insuficiente |
| 253 | Contrato Administrativo | 1 | Volume insuficiente |
| 293 | Balanço Patrimonial | 0 | Tipo existe, nenhum documento cadastrado |
| 294 | DRE | 0 | Tipo existe, nenhum documento cadastrado |
| 292 | Nota Expositiva - Demonstrações Contábeis | 0 | Tipo existe, nenhum documento cadastrado |
| 157 | Escritura | 0 | Tipo existe, nenhum documento cadastrado |

---

## 3. Mapa Completo de Skills Possíveis

### Skills Ativas (4 com golden sets)

1. **`matricula_v1`** — Extração de matrícula imobiliária (inteiro teor)
   - Campos: proprietário, CPF/CNPJ, área, ônus, alienação fiduciária, registro
   - Volume: 2.212 docs | Cases: 5 | Status: seed_complete

2. **`contrato_social_v1`** — Extração de contrato/estatuto social
   - Campos: CNPJ, razão social, sócios, capital, poderes, administração
   - Volume: 358 docs | Cases: 5 | Status: seed_complete

3. **`cnd_v1`** — Extração de certidão negativa de débitos (RFB/PGFN)
   - Campos: tipo, código verificação, órgão, validade, status, titular
   - Volume: 296 docs | Cases: 5 | Status: seed_complete

4. **`procuracao_v1`** — Extração de procuração pública
   - Campos: outorgante, outorgado, poderes, validade, cartório
   - Volume: 109 docs | Cases: 5 | Status: seed_complete

### Skills Candidatas — Imediatas (dados disponíveis, alto valor)

5. **`certidao_trabalhista_v1`** — Extração de certidão de distribuição trabalhista
   - Campos: titular (PF/PJ), CPF/CNPJ, comarca/região TRT, resultado (positiva/negativa), processos listados (nº, vara, status, valor), data emissão, validade
   - Volume: **381 docs** — maior volume entre não-cobertos
   - Valor: **CRÍTICO** — risco trabalhista é critério de gate na decisão de crédito
   - Complexidade: Média — formato tabular com campos repetitivos
   - **Recomendação: SUBSTITUIR balanço por esta skill**

6. **`certidao_civel_v1`** — Extração de certidão de distribuição cível
   - Campos: titular, CPF/CNPJ, comarca, foro, resultado (positiva/negativa), processos (nº, vara, status, tipo ação, valor causa), data emissão
   - Volume: **138 docs**
   - Valor: **CRÍTICO** — processos cíveis impactam parecer de crédito
   - Complexidade: Média — similar à trabalhista

7. **`divida_pgfn_v1`** — Extração de consulta de dívida ativa (PGFN)
   - Campos: devedor, CPF/CNPJ, inscrições (número, valor, situação, data inscrição), valor total, quantidade inscrições
   - Volume: 37 docs
   - Valor: **CRÍTICO** — dívida ativa é bloqueante
   - Complexidade: Alta — múltiplas inscrições com status variados

8. **`protesto_v1`** — Extração de consulta de protesto
   - Campos: consultado, CPF/CNPJ, resultado (com/sem protesto), protestos (cartório, valor, data, credor), data consulta
   - Volume: 10 docs
   - Valor: **CRÍTICO** — protestos são red flag em análise de crédito
   - Complexidade: Baixa — formato tabular simples

### Skills Candidatas — Médio prazo (dados limitados ou variante)

9. **`ccir_v1`** — Extração de CCIR (imóvel rural)
   - Campos: código imóvel, denominação, área, município, proprietário, situação cadastral
   - Volume: 7 docs
   - Valor: Alto para operações rurais (Caixa, Pine)
   - Complexidade: Baixa

10. **`matricula_onus_v1`** — Variante de matrícula focada em ônus reais
    - Campos: matrícula, ônus listados (tipo, credor, valor, status), data certidão
    - Volume: 40 docs
    - Nota: Pode ser incorporada como variante do `matricula_v1` em vez de skill separada

11. **`convencao_condominio_v1`** — Extração de convenção de condomínio
    - Campos: nome condomínio, CNPJ, administradora, fração ideal, restrições de uso, taxa condominial
    - Volume: 16 docs
    - Valor: Médio — relevante para avaliação de imóvel em condomínio

12. **`cadeia_dominial_v1`** — Extração de cadeia dominial
    - Campos: sequência de proprietários (nome, CPF/CNPJ, data aquisição, título aquisitivo, registro)
    - Volume: 6 docs
    - Valor: Alto — comprova origem legítima da propriedade
    - Complexidade: Muito alta — documento longo com múltiplas transferências

13. **`ata_eleicao_v1`** — Extração de ata de eleição de administradores
    - Campos: empresa, CNPJ, administradores eleitos, poderes, mandato, data assembleia
    - Volume: 6 docs
    - Nota: Pode ser variante de `contrato_social_v1` para S.A.

14. **`dados_cadastrais_imovel_v1`** — Extração de dados cadastrais de imóvel
    - Campos: inscrição municipal, endereço, área terreno, área construída, proprietário, uso
    - Volume: 5 docs
    - Complexidade: Baixa

### Skills Futuras — Sem dados hoje, relevantes quando existirem

15. **`balanco_v1`** — Extração de balanço patrimonial (mantido como schema-only)
    - Campos: ativo_total, passivo_total, PL, dívida_líquida, liquidez_corrente
    - Volume: 0 docs — aguardando produção
    - Schema e metadata.yaml já preparados

16. **`dre_v1`** — Extração de DRE
    - Campos: receita_liquida, custos, despesas_operacionais, resultado_exercicio, EBITDA
    - Volume: 0 docs — tipo 294

17. **`escritura_v1`** — Extração de escritura pública de compra e venda
    - Campos: vendedor, comprador, imóvel, valor, forma pagamento, cartório
    - Volume: 0 docs — tipo 157/288

18. **`cnd_municipal_v1`** — Extração de CND municipal
    - Campos: similar à cnd_v1, com tributos municipais (ISS, IPTU)
    - Volume: a verificar (tipo 282)

19. **`cnd_estadual_v1`** — Extração de CND estadual
    - Campos: similar à cnd_v1, com tributos estaduais (ICMS)
    - Volume: a verificar (tipo 144)

---

## 4. Recomendação de Substituição para Track A

### Opção recomendada: `certidao_trabalhista_v1` (tipo 113)

**Por quê:**

1. **Volume massivo (381 docs)** — mais que CND e procuração combinados. Permite selecionar 5 cases diversos com facilidade.

2. **Valor de negócio máximo** — certidão trabalhista é critério BLOQUEANTE na decisão de crédito. Se o titular tem ações trabalhistas expressivas, o parecer muda de "aprovado" para "aprovado com ressalvas" ou "reprovado". É um dos documentos mais analisados no pipeline.

3. **Complexidade de extração adequada** — não é trivial (tem lista de processos com campos variados) nem impossível (formato semi-estruturado). Testa a capacidade do extractor de lidar com listas de tamanho variável.

4. **Complementaridade** — as 4 skills existentes cobrem: imóvel (matrícula), empresa (contrato social), fiscal (CND), representação (procuração). Falta o risco litigioso, que a certidão trabalhista cobre perfeitamente.

5. **Campos extraíveis claros:**
   - `titular` (string) — CRITICAL, weight 3
   - `titular_cpf_cnpj` (string) — CRITICAL, weight 3
   - `resultado` (enum: negativa | positiva) — CRITICAL, weight 3
   - `processos` (array de objetos) — CRITICAL, weight 3
   - `orgao_emissor` (string) — IMPORTANT, weight 2
   - `abrangencia` (string: região TRT) — IMPORTANT, weight 2
   - `data_emissao` (date) — INFORMATIVE, weight 1
   - `validade` (date) — IMPORTANT, weight 2
   - `codigo_verificacao` (string) — INFORMATIVE, weight 1

### Alternativa: `certidao_civel_v1` (tipo 101)

Se trabalhista não for desejada, a certidão cível (138 docs) tem estrutura quase idêntica e valor de negócio equivalente.

---

## 5. Roadmap de Skills por Sprint

### Sprint Atual (Track A Seed)
- [x] matricula_v1 (5 cases)
- [x] contrato_social_v1 (5 cases)
- [x] cnd_v1 (5 cases)
- [x] procuracao_v1 (5 cases)
- [x] **certidao_trabalhista_v1** (5 cases) — substitui balanço

### Sprint Seguinte (Expansão P0)
- [ ] certidao_civel_v1 (5 cases)
- [ ] divida_pgfn_v1 (5 cases)
- [ ] protesto_v1 (5 cases)

### Sprint Futuro (Expansão P1)
- [ ] ccir_v1 (quando rural for prioridade)
- [ ] convencao_condominio_v1
- [ ] cadeia_dominial_v1
- [ ] balanco_v1 (quando documentos existirem)

### Variantes (incorporar em skills existentes)
- matricula_onus como variante de matricula_v1
- matricula_conjunta como variante de matricula_v1
- ata_eleicao como variante de contrato_social_v1
