# Track A — Manual de Anotacao de Golden Sets

> **Quem executa:** Diogo Dantas (CLO)
> **Estimativa:** ~30h (5-6 cases/skill x 5 skills + buffer)
> **Deadline:** Antes do Phase 2 Checkpoint (Phase 1 -> Phase 2 transition)
> **Resultado:** >= 25 cases anotados em `golden/`, prontos para eval via CLI

---

## 0. Antes de Comecar

### Pre-requisitos

```bash
# 1. Garantir que o projeto roda limpo
cd ~/Python-Projetos/gbr-eval
git pull
uv sync --all-extras
uv run pytest -q  # deve passar 215 tests

# 2. Ter acesso aos documentos originais
# - Documentos reais (matriculas, CNDs, contratos, etc.)
# - Acesso ao sistema de arquivos ou vault onde estao armazenados

# 3. Ferramentas necessarias
# - Editor de texto/JSON (VS Code recomendado)
# - sha256sum ou shasum (vem com macOS)
# - jq (opcional, para validacao: brew install jq)
```

### Onde ficam os golden sets

```
golden/
  matricula/       <- 5-6 cases aqui
  contrato_social/ <- 5-6 cases aqui
  cnd/             <- 5 cases aqui
  procuracao/      <- 5 cases aqui
  balanco/         <- 5 cases aqui
  red_team/        <- BLOQUEADO (criterion 4 NOT EVALUABLE)
```

Cada diretorio ja tem `metadata.yaml` com os campos esperados e seus pesos.

---

## 1. Fluxo de Anotacao (por case)

Para CADA documento que voce anotar, siga estes 7 passos:

### Passo 1: Selecionar o documento

Escolha um documento REAL do tipo correspondente. Priorize diversidade:
- Documentos de diferentes cartorio/orgao/empresa
- Variar complexidade (simples e complexos)
- Incluir edge cases (campos faltantes, formatacao incomum)
- Pelo menos 1 case por skill com campos opcionais ausentes

### Passo 2: Gerar o hash do documento original

```bash
# Para PDF
shasum -a 256 /caminho/do/documento.pdf
# Output: a1b2c3d4e5f6...  /caminho/do/documento.pdf

# Para imagem
shasum -a 256 /caminho/do/documento.png
```

Copie APENAS o hash (primeira coluna). O hash garante rastreabilidade sem expor o documento.

### Passo 3: Extrair os campos manualmente

Abra o documento e extraia TODOS os campos listados no `metadata.yaml` do skill correspondente. Anote em um rascunho:
- Valor exato como aparece no documento
- Se o campo nao existe no documento, anote como `null`
- Se o campo e ambiguo, anote a melhor interpretacao e adicione nota

### Passo 4: Anonimizar os dados

**OBRIGATORIO antes de salvar no JSON.** Regras LGPD:

| Dado | Regra de Anonimizacao | Exemplo |
|------|----------------------|---------|
| CPF | `000.000.000-XX` (manter ultimos 2 digitos) | `123.456.789-09` -> `000.000.000-09` |
| CNPJ | `00.000.000/0000-XX` (manter ultimos 2 digitos) | `12.345.678/0001-95` -> `00.000.000/0000-95` |
| Nomes de pessoas | Substituir por nomes ficticios (manter padrao 2-3 palavras) | `Maria Silva Santos` -> `Ana Costa Lima` |
| Nomes de empresas | Substituir mantendo o tipo societario | `Tech Corp Ltda` -> `Alpha Sistemas Ltda` |
| Enderecos | Substituir rua/numero, MANTER cidade/estado | `Rua Augusta 1500, SP` -> `Rua Exemplo 100, SP` |
| Valores monetarios | Manter ORDEM DE GRANDEZA, alterar digitos | `R$ 1.234.567,89` -> `R$ 1.100.000,00` |
| Numeros de registro/matricula | Substituir mantendo formato | `123.456` -> `999.001` |
| Datas | MANTER inalteradas (nao sao PII) | `2024-03-15` -> `2024-03-15` |
| Telefones | Substituir por `(00) 0000-0000` | |
| Emails | Substituir por `exemplo@anonimizado.com` | |

**Regra de ouro:** Se um campo identifica uma pessoa fisica ou juridica REAL, anonimize. Na duvida, anonimize.

### Passo 5: Criar o arquivo JSON do case

Nome do arquivo: `case_NNN.json` (NNN = sequencial com 3 digitos, comecando em 001)

```json
{
  "case_number": 1,
  "document_hash": "sha256:a1b2c3d4e5f6789...",
  "tags": ["seed"],
  "annotator": "diogo.dantas",
  "created_at": "2026-04-18T14:30:00Z",
  "document_source": "vault/matriculas/lote_2024Q1",
  "notes": "",
  "expected_output": {
    // campos extraidos anonimizados — ver secao 2 por skill
  },
  "citation": {
    // pagina/trecho onde cada campo foi encontrado — ver secao 3
  }
}
```

### Passo 6: Auto-revisar

Antes de salvar, verifique:

- [ ] Hash do documento corresponde ao arquivo original?
- [ ] TODOS os campos criticos preenchidos (nao faltou nenhum)?
- [ ] Anonimizacao aplicada em TODOS os dados pessoais?
- [ ] Nenhum CPF/CNPJ/nome real no JSON?
- [ ] Valores numericos mantem a ordem de grandeza correta?
- [ ] `tags` preenchido corretamente?
- [ ] JSON valido (sem virgulas extras, aspas faltando)?

Validar JSON rapidamente:

```bash
# Verifica se o JSON e valido
python3 -c "import json; json.load(open('golden/matricula/case_001.json'))"

# Verifica se nao tem CPF real (padrao XXX.XXX.XXX-XX com digitos reais)
grep -P '\d{3}\.\d{3}\.\d{3}-\d{2}' golden/matricula/case_001.json
# Se retornar algo que NAO comeca com 000, anonimizacao falhou
```

### Passo 7: Atualizar metadata.yaml

Apos adicionar cases, atualize o `current_cases` e `status` no `metadata.yaml`:

```yaml
current_cases: 5  # atualizar com o numero real
annotator: diogo.dantas
status: annotated  # mudar de "empty" para "annotated"
```

---

## 2. Campos por Skill — Referencia Completa

### 2.1 Matricula de Imovel (`matricula_v1`)

**Campos no `expected_output`:**

| Campo | Peso | Tipo | Obrigatorio | Exemplo Anonimizado |
|-------|------|------|-------------|---------------------|
| `document_type` | — | string | SIM | `"matricula"` |
| `numero_matricula` | 3 (CRITICAL) | string | SIM | `"999.001"` |
| `proprietario_cpf` | 3 (CRITICAL) | string | SIM | `"000.000.000-09"` |
| `proprietario_nome` | 2 (IMPORTANT) | string | SIM | `"Ana Costa Lima"` |
| `area_total` | 2 (IMPORTANT) | float | SIM | `150.0` |
| `onus` | 3 (CRITICAL) | boolean | SIM | `true` ou `false` |
| `alienacao_fiduciaria` | 3 (CRITICAL) | boolean | SIM | `true` ou `false` |
| `endereco` | 1 (INFORMATIVE) | string | NAO | `"Rua Exemplo 100, Sao Paulo/SP"` |
| `comarca` | 1 (INFORMATIVE) | string | NAO | `"Sao Paulo"` |

**Exemplo completo:**

```json
{
  "case_number": 1,
  "document_hash": "sha256:3f2a1b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a",
  "tags": ["seed"],
  "annotator": "diogo.dantas",
  "created_at": "2026-04-18T14:30:00Z",
  "document_source": "vault/matriculas/lote_2024Q1",
  "notes": "",
  "expected_output": {
    "document_type": "matricula",
    "numero_matricula": "999.001",
    "proprietario_cpf": "000.000.000-09",
    "proprietario_nome": "Ana Costa Lima",
    "area_total": 150.0,
    "onus": true,
    "alienacao_fiduciaria": false,
    "endereco": "Rua Exemplo 100, Sao Paulo/SP",
    "comarca": "Sao Paulo"
  },
  "citation": {
    "numero_matricula": {"page": 1, "excerpt": "Matricula n. 999.001 do 1o Oficio"},
    "proprietario_cpf": {"page": 1, "excerpt": "CPF 000.000.000-09"},
    "proprietario_nome": {"page": 1, "excerpt": "Ana Costa Lima, brasileira"},
    "area_total": {"page": 2, "excerpt": "area total de 150,00 m2"},
    "onus": {"page": 3, "excerpt": "R.5 - Hipoteca em favor de..."},
    "alienacao_fiduciaria": {"page": 3, "excerpt": "Nao consta alienacao fiduciaria"}
  }
}
```

**Dicas especificas para matricula:**
- `onus`: verificar TODAS as averbacoes (R.1, R.2, ...) na margem. Se qualquer uma registra hipoteca, penhora, arresto, etc. -> `true`
- `alienacao_fiduciaria`: buscar nos registros termos como "alienacao fiduciaria", "cedula de credito", "garantia real"
- `area_total`: usar sempre m2 (metros quadrados) como unidade. Se o documento mostra hectares, converter
- CPFs com digitos de verificacao: manter os 2 ultimos digitos para o eval validar formato

---

### 2.2 Contrato Social (`contrato_social_v1`)

**Campos no `expected_output`:**

| Campo | Peso | Tipo | Obrigatorio | Exemplo Anonimizado |
|-------|------|------|-------------|---------------------|
| `document_type` | — | string | SIM | `"contrato_social"` |
| `cnpj` | 3 (CRITICAL) | string | SIM | `"00.000.000/0000-95"` |
| `razao_social` | 3 (CRITICAL) | string | SIM | `"Alpha Sistemas Ltda"` |
| `socios` | 3 (CRITICAL) | list[object] | SIM | ver exemplo |
| `participacao_percentual` | 2 (IMPORTANT) | dict | SIM | `{"socio_1": 60, "socio_2": 40}` |
| `capital_social` | 2 (IMPORTANT) | float | SIM | `500000.00` |
| `poderes` | 3 (CRITICAL) | string | SIM | `"administracao conjunta"` |
| `objeto_social` | 1 (INFORMATIVE) | string | NAO | `"desenvolvimento de software"` |
| `data_constituicao` | 1 (INFORMATIVE) | string | NAO | `"2020-05-15"` |

**Exemplo do campo `socios`:**

```json
"socios": [
  {
    "nome": "Carlos Ferreira",
    "cpf": "000.000.000-12",
    "participacao_pct": 60.0,
    "administrador": true
  },
  {
    "nome": "Mariana Souza",
    "cpf": "000.000.000-34",
    "participacao_pct": 40.0,
    "administrador": false
  }
]
```

**Dicas especificas para contrato social:**
- Se houver alteracoes contratuais consolidadas, usar a versao MAIS RECENTE
- `poderes`: transcrever de forma resumida (ex: "cada socio isoladamente", "socios em conjunto", "apenas socio administrador")
- `capital_social`: valor em reais, sem centavos se for redondo
- Se o contrato tiver mais de 3 socios, incluir TODOS

---

### 2.3 Certidao Negativa de Debitos (`cnd_v1`)

**Campos no `expected_output`:**

| Campo | Peso | Tipo | Obrigatorio | Exemplo Anonimizado |
|-------|------|------|-------------|---------------------|
| `document_type` | — | string | SIM | `"cnd"` |
| `tipo_certidao` | 3 (CRITICAL) | string | SIM | `"negativa"` ou `"positiva_com_efeito_negativa"` |
| `numero_certidao` | 3 (CRITICAL) | string | SIM | `"9999.0001.0001-00"` |
| `orgao_emissor` | 2 (IMPORTANT) | string | SIM | `"Receita Federal"` |
| `data_validade` | 3 (CRITICAL) | string | SIM | `"2026-06-15"` (formato ISO) |
| `status` | 3 (CRITICAL) | string | SIM | `"valida"` ou `"vencida"` |
| `cpf_cnpj_consultado` | 2 (IMPORTANT) | string | SIM | `"00.000.000/0000-95"` |
| `data_emissao` | 1 (INFORMATIVE) | string | NAO | `"2026-01-15"` |

**Valores validos para `tipo_certidao`:**
- `"negativa"` — nenhum debito encontrado
- `"positiva"` — debitos encontrados
- `"positiva_com_efeito_negativa"` — debitos existem mas estao suspensos/parcelados

**Valores validos para `status`:**
- `"valida"` — dentro da data de validade
- `"vencida"` — apos a data de validade

**Dicas especificas para CND:**
- Verificar a data de validade no momento da anotacao. Se vencida, anotar `status: "vencida"`
- Orgao emissor: usar nome padronizado (`"Receita Federal"`, `"PGFN"`, `"INSS"`, `"FGTS"`, `"Estadual"`, `"Municipal"`)
- Numero da certidao: manter o formato exato do documento (com pontos, tracos, barras)

---

### 2.4 Procuracao (`procuracao_v1`)

**Campos no `expected_output`:**

| Campo | Peso | Tipo | Obrigatorio | Exemplo Anonimizado |
|-------|------|------|-------------|---------------------|
| `document_type` | — | string | SIM | `"procuracao"` |
| `outorgante` | 3 (CRITICAL) | string | SIM | `"Carlos Ferreira"` |
| `outorgante_cpf` | 3 (CRITICAL) | string | SIM | `"000.000.000-12"` |
| `outorgado` | 3 (CRITICAL) | string | SIM | `"Ana Costa Lima"` |
| `outorgado_cpf` | 2 (IMPORTANT) | string | SIM | `"000.000.000-34"` |
| `poderes_especificos` | 3 (CRITICAL) | string | SIM | `"vender, comprar e hipotecar imoveis"` |
| `validade` | 3 (CRITICAL) | string | SIM | `"2027-12-31"` ou `"indeterminada"` |
| `data_lavratura` | 1 (INFORMATIVE) | string | NAO | `"2026-01-10"` |
| `cartorio` | 1 (INFORMATIVE) | string | NAO | `"1o Oficio de Notas de Sao Paulo"` |

**Dicas especificas para procuracao:**
- `poderes_especificos`: transcrever os poderes EXATOS, nao resumir. Se a procuracao diz "poderes amplos e irrestritos", anotar exatamente isso
- `validade`: se a procuracao nao menciona validade, anotar `"indeterminada"`
- Se ha mais de um outorgante ou outorgado, usar arrays:
  ```json
  "outorgante": ["Carlos Ferreira", "Mariana Souza"],
  "outorgante_cpf": ["000.000.000-12", "000.000.000-34"]
  ```
- Diferenciar procuracao publica (lavrada em cartorio) de particular (assinatura privada)

---

### 2.5 Balanco Patrimonial (`balanco_v1`)

**Campos no `expected_output`:**

| Campo | Peso | Tipo | Obrigatorio | Exemplo Anonimizado |
|-------|------|------|-------------|---------------------|
| `document_type` | — | string | SIM | `"balanco"` |
| `ativo_total` | 3 (CRITICAL) | float | SIM | `15000000.00` |
| `passivo_total` | 3 (CRITICAL) | float | SIM | `8500000.00` |
| `patrimonio_liquido` | 3 (CRITICAL) | float | SIM | `6500000.00` |
| `divida_liquida` | 3 (CRITICAL) | float | SIM | `3200000.00` |
| `liquidez_corrente` | 3 (CRITICAL) | float | SIM | `1.45` |
| `receita_liquida` | 2 (IMPORTANT) | float | NAO | `22000000.00` |
| `resultado_exercicio` | 2 (IMPORTANT) | float | NAO | `1800000.00` |
| `data_referencia` | 1 (INFORMATIVE) | string | NAO | `"2025-12-31"` |

**Regras de anonimizacao para valores financeiros:**
- Manter a ORDEM DE GRANDEZA (milhares, milhoes, bilhoes)
- Alterar os digitos especificos
- Manter as proporcoes entre campos (ativo = passivo + PL)
- `liquidez_corrente` e um indice (ratio), manter com 2 casas decimais

**Calculo de verificacao:**
```
ativo_total = passivo_total + patrimonio_liquido  (DEVE bater)
divida_liquida = endividamento_total - disponibilidades  (verificar)
liquidez_corrente = ativo_circulante / passivo_circulante  (verificar)
```

**Dicas especificas para balanco:**
- Se os valores estao em "milhares de reais" (x1.000), converter para valor absoluto
- Se ha balanco consolidado E individual, anotar o INDIVIDUAL (a menos que so exista consolidado)
- `resultado_exercicio`: lucro e positivo, prejuizo e negativo
- Verificar se os numeros batem: `ativo = passivo + PL` (se nao bate, ha erro no documento ou na leitura)

---

## 3. Citation — Como Anotar a Proveniencia

O campo `citation` documenta ONDE no documento cada campo foi encontrado. Isso e essencial para:
- Gate criterio 3 (citation linking = 100%)
- Auditoria: provar que a extracao veio do documento, nao de inferencia

### Formato

```json
"citation": {
  "nome_do_campo": {
    "page": 1,
    "excerpt": "trecho literal do documento onde o campo aparece"
  }
}
```

### Regras

1. **TODOS os campos criticos (peso 3) DEVEM ter citation**
2. Campos informativos (peso 1): citation e opcional mas recomendado
3. O `excerpt` deve ser o trecho LITERAL do documento, anonimizado
4. Se o campo vem de calculo (ex: `liquidez_corrente`), anotar os campos fonte:
   ```json
   "liquidez_corrente": {
     "page": 2,
     "excerpt": "Ativo Circulante: 7.250.000 / Passivo Circulante: 5.000.000",
     "derived": true
   }
   ```
5. Se o campo NAO existe no documento (ex: campo opcional nulo), NAO incluir citation para ele

---

## 4. Tags — Proveniencia do Case

Cada case DEVE ter pelo menos 1 tag no campo `tags`. Tags validas:

| Tag | Quando usar |
|-----|-------------|
| `seed` | Case inicial de bootstrap — todos os da Track A |
| `regression` | Case criado para capturar uma regressao especifica |
| `incident` | Case derivado de um incidente em producao |
| `edge_case` | Documento com caracteristicas incomuns (campos faltantes, formatacao estranha) |
| `hitl` | Case originado de revisao human-in-the-loop |

**Para a Track A:** Use `["seed"]` para todos os cases normais. Se um case for particularmente atipico, use `["seed", "edge_case"]`.

---

## 5. Ordem de Execucao Recomendada

### Dia 1-2: Matricula (5-6 cases)

Comecar por matricula porque:
- E o skill mais critico (Criterio 1 + 2 do Gate)
- Voce ja tem o template (`case_example.json`)
- Campos sao concretos e verificaveis

```bash
# Criar cases
golden/matricula/case_001.json
golden/matricula/case_002.json
golden/matricula/case_003.json
golden/matricula/case_004.json
golden/matricula/case_005.json

# Validar
for f in golden/matricula/case_*.json; do
  python3 -c "import json; d=json.load(open('$f')); print(f'OK: {d[\"case_number\"]} - {len(d[\"expected_output\"])} fields')"
done
```

### Dia 3: Contrato Social (5-6 cases)

Mais complexo por causa dos socios (array de objetos). Reserve tempo extra.

### Dia 4: CND (5 cases)

Mais rapido — campos sao simples e padronizados.

### Dia 5: Procuracao (5 cases)

Cuidado com `poderes_especificos` — transcrever exatamente.

### Dia 6: Balanco (5 cases)

Requer mais atencao nos numeros. Verificar `ativo = passivo + PL` em cada case.

### Dia 7: Revisao + Buffer

- Reler todos os cases com olhos frescos
- Verificar anonimizacao (grep por padroes de CPF/CNPJ reais)
- Verificar consistencia entre cases do mesmo skill
- Atualizar todos os `metadata.yaml`

---

## 6. Validacao Local

### 6.1 Validar formato de todos os cases

```bash
# Verificar que todos os JSONs sao validos
for f in golden/*/case_*.json; do
  python3 -c "import json; json.load(open('$f'))" 2>&1 && echo "OK: $f" || echo "ERRO: $f"
done
```

### 6.2 Verificar campos obrigatorios

```bash
# Verificar que todo case tem os campos base
for f in golden/*/case_*.json; do
  python3 -c "
import json, sys
d = json.load(open('$f'))
required = ['case_number', 'document_hash', 'tags', 'annotator', 'created_at', 'expected_output']
missing = [k for k in required if k not in d]
if missing:
    print(f'FALTANDO em $f: {missing}')
else:
    print(f'OK: $f ({len(d[\"expected_output\"])} fields)')
"
done
```

### 6.3 Verificar anonimizacao (CRITICO)

```bash
# Buscar padroes de CPF que NAO comecam com 000
grep -rn '[1-9][0-9]\{2\}\.[0-9]\{3\}\.[0-9]\{3\}-[0-9]\{2\}' golden/*/case_*.json
# Se retornar QUALQUER resultado, ha CPF real nao anonimizado!

# Buscar padroes de CNPJ que NAO comecam com 00
grep -rn '[1-9][0-9]\.[0-9]\{3\}\.[0-9]\{3\}/[0-9]\{4\}-[0-9]\{2\}' golden/*/case_*.json
# Se retornar QUALQUER resultado, ha CNPJ real nao anonimizado!
```

### 6.4 Contar cases por skill

```bash
echo "=== Contagem de cases ==="
for dir in golden/matricula golden/contrato_social golden/cnd golden/procuracao golden/balanco; do
  count=$(ls $dir/case_*.json 2>/dev/null | wc -l | tr -d ' ')
  echo "$dir: $count cases"
done
echo "========================="
```

### 6.5 Rodar o eval CLI com os cases (apos Phase 2 wiring)

```bash
# Isso so funciona apos o Phase 2 conectar golden sets aos tasks
# Por enquanto, validacao e manual (formato + anonimizacao)
gbr-eval run --suite tasks/product/ --output-format console
```

---

## 7. Upload para Storage Externo

Apos anotar e validar localmente, os cases devem ir para o storage externo (S3).

### 7.1 Configurar credenciais

```bash
# Verificar acesso ao bucket
aws s3 ls s3://gbr-eval-golden-sets/v1/
```

### 7.2 Upload dos cases

```bash
# Upload de todos os cases de um skill
aws s3 sync golden/matricula/ s3://gbr-eval-golden-sets/v1/matricula/ \
  --exclude "metadata.yaml" \
  --exclude "case_example.json"

# Upload de todos os skills de uma vez
for skill in matricula contrato_social cnd procuracao balanco; do
  aws s3 sync golden/$skill/ s3://gbr-eval-golden-sets/v1/$skill/ \
    --exclude "metadata.yaml" \
    --exclude "case_example.json"
  echo "Uploaded: $skill"
done
```

### 7.3 Verificar upload

```bash
# Contar cases no S3
for skill in matricula contrato_social cnd procuracao balanco; do
  count=$(aws s3 ls s3://gbr-eval-golden-sets/v1/$skill/case_ --recursive | wc -l)
  echo "$skill: $count cases no S3"
done
```

---

## 8. Checklist Final (Phase 1 Gate)

Antes de declarar Track A completa, TODOS estes itens devem ser verdadeiros:

### Quantidade
- [ ] Matricula: >= 5 cases
- [ ] Contrato Social: >= 5 cases
- [ ] CND: >= 5 cases
- [ ] Procuracao: >= 5 cases
- [ ] Balanco: >= 5 cases
- [ ] Total: >= 25 cases

### Qualidade
- [ ] TODOS os campos CRITICOS (peso 3) preenchidos em TODOS os cases
- [ ] Citation presente para TODOS os campos criticos
- [ ] Pelo menos 1 edge_case por skill (campo opcional ausente, formato incomum)
- [ ] Valores de balanco batem: ativo = passivo + PL (em todos os cases de balanco)

### Seguranca
- [ ] Zero CPF real nos JSONs (grep nao retorna nada)
- [ ] Zero CNPJ real nos JSONs (grep nao retorna nada)
- [ ] Zero nomes reais de pessoas fisicas
- [ ] Hashes de documentos presentes em todos os cases
- [ ] Nenhum documento original commitado no repo

### Metadata
- [ ] Todos os 5 `metadata.yaml` atualizados com `current_cases` e `status: annotated`
- [ ] `annotator: diogo.dantas` em todos os cases e metadatas
- [ ] `created_at` com timestamp real (nao placeholder)
- [ ] Tags definidas em todos os cases (`seed` no minimo)

### Rastreabilidade
- [ ] Cada case tem `document_hash` unico (sha256 do documento original)
- [ ] Nenhum hash duplicado (cada case vem de um documento diferente)
- [ ] `document_source` indica a localizacao generica (sem path completo de maquina local)

---

## 9. Erros Comuns a Evitar

| Erro | Consequencia | Como evitar |
|------|-------------|-------------|
| Esquecer de anonimizar um CPF | Vazamento de PII no repo | Sempre rodar grep de validacao (secao 6.3) |
| Copiar expected_output de um case para outro | Tautologia — eval nao testa nada | Cada case deve vir de um documento DIFERENTE |
| Arredondar valores de balanco | Grader numeric_range falha | Manter precisao de 2 casas decimais |
| Usar `null` para campo critico sem documentar | Grader falha sem explicacao | Se campo critico esta ausente, adicionar `"notes"` explicando |
| Formato de data inconsistente | exact_match falha | SEMPRE usar ISO 8601: `"2026-04-18"` |
| Esquecer citation em campo critico | Gate criterio 3 falha | Verificar que todo campo peso 3 tem citation |
| Gerar case sintetico (inventar dados) | Viola regra zero — golden sets sao dados REAIS anonimizados | Cada case deve vir de documento REAL |

---

## 10. Quanto Tempo Reservar

| Skill | Cases | Tempo estimado | Complexidade |
|-------|-------|---------------|-------------|
| Matricula | 5-6 | ~6h (1h/case) | Media — muitos campos, averbacoes na margem |
| Contrato Social | 5-6 | ~6h (1h/case) | Alta — socios sao array, poderes sao texto livre |
| CND | 5 | ~4h (45min/case) | Baixa — campos padronizados, pouco texto |
| Procuracao | 5 | ~4h (45min/case) | Media — poderes especificos requerem transcricao |
| Balanco | 5 | ~5h (1h/case) | Alta — numeros devem bater, calculos derivados |
| Revisao + Buffer | — | ~5h | — |
| **Total** | **25-27** | **~30h** | — |

**Sugestao de time-blocking:** 4h/dia de anotacao pela manha. Em 7-8 dias uteis a Track A esta completa.

---

## 11. Apos Completar a Track A

Quando todos os cases estiverem anotados, validados e uploaded:

1. Avisar para que o Phase 2 (Validation Sprint) inicie
2. Phase 2 vai:
   - Conectar os golden sets aos task YAMLs
   - Rodar `gbr-eval run --suite tasks/` com dados reais
   - Identificar falhas nos graders vs golden sets
   - Estabelecer o baseline para regressao
   - Produzir o Gate scorecard

O trabalho de anotacao NAO precisa esperar nada do backend — pode comecar HOJE.
