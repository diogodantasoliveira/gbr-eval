# Comparacao: Campos gbr-eval (metadata.yaml) vs Sistema de Producao

> Gerado em 2026-04-18. Objetivo: identificar divergencias para decidir quais campos anotar nos golden sets.

---

## 1. Matricula de Imovel

### gbr-eval (metadata.yaml)
| Campo | Peso | Tipo esperado |
|-------|------|---------------|
| numero_matricula | 3 CRITICAL | string |
| proprietario_cpf | 3 CRITICAL | string |
| proprietario_nome | 2 IMPORTANT | string |
| area_total | 2 IMPORTANT | float |
| onus | 3 CRITICAL | boolean |
| alienacao_fiduciaria | 3 CRITICAL | boolean |
| endereco | 1 INFORMATIVE | string |
| comarca | 1 INFORMATIVE | string |

### Sistema de producao (prompt tipo 135)
Extrai 8 blocos (nao campos flat): numero matricula, endereco, descricao completa (area, dimensoes, confrontacoes, benfeitorias), cadeia dominial (array de proprietarios com CPF/CNPJ, valor), ultimos 4 R/AV, onus e acoes (com cancelamentos), observacoes gerais, data emissao.

### Divergencias
| Aspecto | gbr-eval | Sistema | Decisao necessaria |
|---------|----------|---------|-------------------|
| Proprietarios | Campo unico (nome + CPF) | Array com historico cronologico | Anotar ultimo proprietario ou array completo? |
| Area | `area_total` (float) | Dentro de "descricao do imovel" (texto) | OK — extrair float da descricao |
| Onus | Boolean simples | Lista detalhada com tipo, R/AV, envolvidos, cancelamento | Boolean E lista? Ou so boolean? |
| Alienacao fiduciaria | Boolean simples | Dentro de onus, como subtipo | OK — derivavel da lista de onus |
| Cadeia dominial | NAO existe no eval | Bloco completo no prompt | Adicionar? Ou manter scope minimo? |
| Ultimos 4 R/AV | NAO existe no eval | Bloco completo no prompt | Adicionar? |
| Data emissao | NAO existe no eval | Sim no prompt | Adicionar como INFORMATIVE? |
| Comarca | Sim (INFORMATIVE) | NAO explicito no prompt | Manter — esta na certidao |
| Schema JSON | — | VAZIO | — |

**Recomendacao:** Manter os 8 campos do metadata.yaml como baseline. Sao os campos que o grader vai avaliar. Os blocos adicionais do sistema (cadeia dominial, 4 ultimos R/AV) podem ser adicionados em fase futura. Para a Track A, focar nos campos ja definidos.

---

## 2. Contrato Social (Junta Comercial)

### gbr-eval (metadata.yaml)
| Campo | Peso |
|-------|------|
| cnpj | 3 CRITICAL |
| razao_social | 3 CRITICAL |
| socios | 3 CRITICAL |
| participacao_percentual | 2 IMPORTANT |
| capital_social | 2 IMPORTANT |
| poderes | 3 CRITICAL |
| objeto_social | 1 INFORMATIVE |
| data_constituicao | 1 INFORMATIVE |

### Sistema de producao (schema JSON tipo 130)
Estruturado em blocos: `dados_empresa` (razao_social, nome_fantasia, natureza_juridica, cnpj, nire, endereco_sede, data_inicio_atividades, objeto_social), `capital_social` (valor, moeda, qtd_quotas, valor_nominal), `socios[]` (nome, cpf, qualificacao, participacao_quotas, valor, percentual), `administradores[]` (nome, cpf, forma_atuacao), `alteracoes_contratuais[]`, `situacao_atual`, `observacoes_gerais` (prazo_duracao, data_constituicao, nire), `assinatura_certidao`.

### Divergencias
| Aspecto | gbr-eval | Sistema | Decisao necessaria |
|---------|----------|---------|-------------------|
| Socios | Campo generico | Array com nome, cpf, qualificacao, quotas, valor, % | Eval deve usar array? |
| Participacao | Campo separado (dict) | Dentro de cada socio | Manter como campo separado ou embutir em socios? |
| Poderes | Campo unico "poderes" | Dentro de `administradores[].forma_atuacao` | Campo eval mais generico — OK |
| Capital social | Float | String formatada (R$ X) | Normalizar para float no eval |
| NIRE | NAO existe no eval | Sim no schema | Adicionar? |
| Nome fantasia | NAO existe no eval | Sim no schema | Opcional — adicionar? |
| Administradores | Coberto por "poderes" | Array separado | Mais granular no sistema |

**Recomendacao:** Usar os campos do metadata.yaml. Para `socios`, anotar como array de objetos (compativel com o schema do sistema). `poderes` como string descritiva ("conjunta"/"isolada"/etc). `capital_social` como float.

---

## 3. CND Federal

### gbr-eval (metadata.yaml)
| Campo | Peso |
|-------|------|
| tipo_certidao | 3 CRITICAL |
| numero | 3 CRITICAL |
| orgao_emissor | 2 IMPORTANT |
| validade | 3 CRITICAL |
| status | 3 CRITICAL |
| cpf_cnpj_consultado | 2 IMPORTANT |
| data_emissao | 1 INFORMATIVE |

### Sistema de producao (prompt tipo 96)
5 campos: tipo_certidao, dados_contribuinte (nome + CPF/CNPJ), situacao_contribuinte, orgao_emissor, data_hora_emissao.

### Divergencias
| Aspecto | gbr-eval | Sistema | Decisao necessaria |
|---------|----------|---------|-------------------|
| Numero certidao | 3 CRITICAL | NAO no prompt | Existe no doc, prompt nao pede explicitamente |
| Validade | 3 CRITICAL | NAO no prompt | Existe no doc, prompt nao pede |
| Status | 3 CRITICAL | Coberto por "situacao contribuinte" | Derivavel |
| Codigo validacao | NAO no eval | NAO no prompt | gbr-engines tem, sistema nao |

**Recomendacao:** O metadata.yaml do eval e mais completo que o prompt do sistema para CND. Manter os 7 campos do eval — numero e validade existem no documento mesmo que o prompt nao peca explicitamente.

---

## 4. Procuracao

### gbr-eval (metadata.yaml)
| Campo | Peso |
|-------|------|
| outorgante | 3 CRITICAL |
| outorgante_cpf | 3 CRITICAL |
| outorgado | 3 CRITICAL |
| outorgado_cpf | 2 IMPORTANT |
| poderes_especificos | 3 CRITICAL |
| validade | 3 CRITICAL |
| data_lavratura | 1 INFORMATIVE |
| cartorio | 1 INFORMATIVE |

### Sistema de producao (prompt tipo 146)
9 blocos: dados tabelionato, outorgante (nome, CPF/CNPJ, nacionalidade, estado civil, profissao, endereco), outorgado (idem), poderes conferidos (genericos/especificos, detalhamento), prazo validade, substabelecimento, finalidade, observacoes, data emissao.

### Divergencias
| Aspecto | gbr-eval | Sistema | Decisao necessaria |
|---------|----------|---------|-------------------|
| Substabelecimento | NAO no eval | Sim no prompt | Adicionar? Relevante para compliance |
| Finalidade | NAO no eval | Sim no prompt | Adicionar como INFORMATIVE? |
| Dados tabelionato | `cartorio` generico | Bloco completo (nome, endereco, tabeliao) | OK — cartorio cobre |
| Outorgante detalhado | Nome + CPF | +nacionalidade, estado civil, profissao, endereco | Manter scope minimo |

**Recomendacao:** Campos do eval cobrem o essencial. Substabelecimento pode ser adicionado como IMPORTANT em fase futura. Para Track A, manter os 8 campos.

---

## 5. Balanco Patrimonial

### gbr-eval (metadata.yaml)
| Campo | Peso |
|-------|------|
| ativo_total | 3 CRITICAL |
| passivo_total | 3 CRITICAL |
| patrimonio_liquido | 3 CRITICAL |
| divida_liquida | 3 CRITICAL |
| liquidez_corrente | 3 CRITICAL |
| receita_liquida | 2 IMPORTANT |
| resultado_exercicio | 2 IMPORTANT |
| data_referencia | 1 INFORMATIVE |

### Sistema de producao (prompt tipo 293)
9 blocos: identificacao empresa (razao social, CNPJ, data), ativo circulante (detalhado), ativo nao circulante (detalhado), composicao imobilizado, passivo circulante (detalhado), passivo nao circulante, patrimonio liquido (capital social, reservas, lucros/prejuizos), verificacao A=P+PL, comparacao entre exercicios.

### Divergencias
| Aspecto | gbr-eval | Sistema | Decisao necessaria |
|---------|----------|---------|-------------------|
| Divida liquida | 3 CRITICAL | NAO explicito no prompt | Campo DERIVADO — precisa calcular |
| Liquidez corrente | 3 CRITICAL | NAO explicito no prompt | Campo DERIVADO (AC/PC) |
| Receita liquida | 2 IMPORTANT | NAO no prompt (BP nao tem DRE) | So existe se tiver DRE junto |
| Resultado exercicio | 2 IMPORTANT | Dentro de PL como lucros/prejuizos | OK — derivavel |
| Detalhamento AC/ANC | NAO no eval | Sim (blocos completos) | Nao necessario para Track A |
| Razao social / CNPJ | NAO no eval | Sim no prompt | Adicionar como INFORMATIVE? |

**Recomendacao:** Anotar os 8 campos do eval. Campos derivados (divida_liquida, liquidez_corrente) serao calculados a partir dos dados do documento. IMPORTANTE: nem todo balanco vem com DRE — `receita_liquida` pode ser null em muitos cases. Anotar `null` com nota explicativa.

---

## Decisao Consolidada

Para a **Track A**, anotar usando os campos do **metadata.yaml do gbr-eval**. Razoes:

1. Sao os campos que os graders ja estao preparados para avaliar
2. Tem pesos (CRITICAL/IMPORTANT/INFORMATIVE) definidos
3. Sao mais simples e objetivos — adequados para um primeiro golden set seed
4. Os campos adicionais do sistema de producao podem ser adicionados em fases futuras

**Decisoes do CLO (2026-04-18):**

- [x] `onus` e `alienacao_fiduciaria` em matricula: **LISTA DETALHADA** (alinhar com sistema de producao). onus = array de objetos {tipo, registro_av, status, envolvidos}. alienacao_fiduciaria = boolean derivado da lista (existe AF ativa?).
- [x] `socios` em contrato social: **ARRAY DE OBJETOS** {nome, cpf, percentual}. Alinhado com schema do sistema.
- [x] `divida_liquida` e `liquidez_corrente` em balanco: **SIM, anotar valores calculados**. Testa se o LLM calcula corretamente.
- [x] `receita_liquida`: **OPCIONAL com null**. Anotar quando presente, null quando BP nao inclui DRE. Tag 'sem_dre' no case.
- [x] CND `numero` e `validade`: **MANTER AMBOS**. Eval deve ser mais completo que o prompt atual do sistema.
