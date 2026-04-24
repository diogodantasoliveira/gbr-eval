# Servico de Aplicacao de Regras Negociais
## Especificacao Completa — Edital BPO CAIXA

**Referencia:** Termo de Referencia, Secao 2.7 | Anexo I-A (Definicoes) | Anexo I-C (Volumetria) | Anexo I-H (Filas)
**Ultima atualizacao:** 2026-04-10

---

## 1. DEFINICAO FORMAL

> **Itens de analises** — Itens que descrevem a(s) informacao(oes) a ser(em) comparada(s) ou analisada(s) em cada demanda e que compoem o checklist.
>
> **Itens de Analises Simples** — Itens que utilizam apenas um criterio ou validacao para determinar o resultado esperado, sem necessidade de combinacoes ou dependencias adicionais.
>
> **Itens de Analises Compostas** — Itens de analise que exijam mais de uma regra/validacao/entendimento encadeados/dependentes para se chegar ao resultado esperado.
>
> **Itens de Precisao** — Definicao dos itens obrigatorios em cada servico/demanda.
>
> — Anexo I-A, Definicoes de Termos

O servico consiste em **comparar documentos e retornar resultados** conforme regras negociais (checklist) estabelecidas pela CAIXA, que serao definidas **por fluxo e tipo documental**. Inclui comparacao com informacoes obtidas em bases internas ou externas, e retorno de resultados estruturados — inclusive calculos, apuracao de rendas, margem consignavel, identificacao de vinculos societarios e poderes.

**Objetivo central:** Aplicar a logica de negocio da CAIXA sobre os dados extraidos dos documentos, validando conformidade com requisitos de cada produto/processo, e retornando resultados que permitam decisoes automatizadas ou assistidas.

---

## 2. ESCOPO DETALHADO DO SERVICO

### 2.1 Operacoes Obrigatorias (TR 2.7.1)

| # | Operacao | Descricao |
|---|----------|----------|
| 1 | **Comparar documentos conforme checklist** | Comparar documentos e retornar resultados conforme regras negociais (checklist) estabelecidas pela CAIXA, por fluxo e tipo documental |
| 2 | **Comparar com bases internas/externas** | Comparar documentos com informacoes obtidas em bases internas ou externas |
| 3 | **Retornar resultados de regras compostas** | Retornar resultados obtidos a partir de combinacoes de regras compostas, incluindo calculos, apuracao de rendas, margem consignavel, identificacao de vinculos societarios e poderes |
| 4 | **Apresentar resultados estruturados** | Apresentar resultados de forma estruturada, conforme modelo definido pela CONTRATANTE |

### 2.2 Organizacao em Itens de Analise (TR 2.7.2)

As regras negociais sao compostas por **Itens de Analise**, classificados em dois tipos com **diferenciacao na tarifacao**:

| Classificacao | Tarifacao | Volume Anual | Preco |
|--------------|----------|-------------|-------|
| **Regra Simples** | Valor unitario menor | 96.151.084 | Proposta |
| **Regra Composta** | Valor unitario maior | 1.690.623 | Proposta |

### 2.3 Demandas Mistas (TR 2.7.3)

> As demandas poderao conter itens analisados simples **e ou** compostos.

Uma unica demanda pode exigir a aplicacao de regras simples E compostas simultaneamente. Cada tipo de regra e remunerado separadamente pelo seu valor unitario proprio.

### 2.4 Definicao de Informacao Externa (TR 2.7.2.2)

> Para fins deste contrato, considera-se **informacao externa** todo dado que nao esteja exclusivamente contido no documento submetido a analise, ainda que fornecido pelo proprio CONTRATANTE, incluindo dados de importacao, dados de originacao, formularios eletronicos, bases internas ou bases externas.

Isso significa que mesmo dados enviados pela CAIXA junto com a demanda (ex: valor do financiamento, faixa de renda permitida, teto do programa) sao considerados "informacao externa" quando comparados com o conteudo do documento.

---

## 3. REGRA SIMPLES — ESPECIFICACAO COMPLETA

### 3.1 Definicao (TR 2.7.2.1)

Regra Simples e aquela que utiliza **um unico criterio** de validacao ou verificacao, aplicado de forma **direta, isolada e nao encadeada**, em que o resultado e obtido a partir de uma unica comparacao ou checagem objetiva, ainda que envolva dados externos, bases auxiliares ou multiplas fontes de informacao, **desde que nao haja combinacao logica entre criterios distintos**.

### 3.2 Caracteristicas Formais (TR 2.7.2.1, a-h)

| # | Caracteristica | Descricao |
|---|---------------|----------|
| a | **Validacao de campo unico** | Envolve a validacao de um unico campo, informacao ou atributo principal do documento, considerado isoladamente para fins de decisao |
| b | **Sem calculo matematico** | Nao exige calculo matematico, ponderacao de variaveis ou encadeamento logico multiplo de criterios |
| c | **Execucao visual ou estruturada** | Pode ser executada por inspecao visual ou com base em chaves previamente estruturadas do proprio documento |
| d | **Comparacao direta com dados de originacao** | Pode envolver comparacao com dados enviados na importacao ou originacao da transacao, quando utilizados de forma direta e nao combinada |
| e | **Consulta a base com checagem objetiva** | Pode envolver consulta a base interna ou externa, inclusive bases fornecidas pela CONTRATANTE, desde que a validacao se limite a uma checagem objetiva |
| f | **Cruzamento pontual entre documentos** | Pode envolver cruzamento pontual entre documentos, quando a analise se restringir a verificacao direta de um unico criterio |
| g | **Dados estruturados isolados** | Pode depender de dados estruturados para viabilizar sua execucao, desde que utilizados de forma isolada |
| h | **Comparacao com informacao externa direta** | Pode envolver a comparacao com qualquer informacao recebida, incluindo dados de importacao, dados de originacao, formularios eletronicos ou outras informacoes externas ao conteudo exclusivo do documento, desde que nao haja correlacao entre multiplos criterios ou etapas analiticas |

### 3.3 Exemplos do Edital — Regras Simples (TR 2.7.2.1)

O TR fornece **13 exemplos explicitos** de regras simples:

| # | Exemplo Literal do TR | Tipo de Validacao | Input | Output | Documento Tipico |
|---|----------------------|-------------------|-------|--------|-----------------|
| a | O titular possui idade maior ou igual a 18 anos | Comparacao numerica | Data nascimento extraida | Sim/Nao | RG, CNH |
| b | A data de emissao do documento esta no periodo de 90 dias | Comparacao de data | Data emissao extraida | Sim/Nao | Certidao, comprovante |
| c | O documento enviado corresponde ao tipo solicitado | Comparacao de classificacao | Tipo classificado vs. tipo esperado | Sim/Nao | Qualquer |
| d | Campo de Assinatura do Gerente esta preenchido | Presenca de elemento | Area de assinatura | Sim/Nao | Contrato, formulario |
| e | Campo Local e Data estao preenchidos | Presenca de elemento | Campos Local e Data | Sim/Nao | Contrato, formulario |
| f | O checkbox de Aceite aos termos esta preenchido | Presenca de elemento | Area do checkbox | Sim/Nao | Formulario, termo |
| g | O nome do titular no documento e igual ao informado no dado logico | Comparacao texto vs. base | Nome extraido vs. dado da CAIXA | Sim/Nao | RG, CNH |
| h | A data de nascimento esta identica a RF (consulta externa previa necessaria) | Comparacao com base externa | Data nasc. extraida vs. Receita Federal | Sim/Nao | RG, CNH |
| i | O nome no documento de identificacao e igual ao do Requerimento de Empresario | Cruzamento entre documentos | Nome em doc A vs. Nome em doc B | Sim/Nao | RG + Requerimento |
| j | A razao social e/ou CNPJ da Entidade estao de acordo com a informacao recebida | Comparacao com dado logico | Razao social/CNPJ extraidos vs. dados da CAIXA | Sim/Nao | Doc. Constitutivo |
| k | O documento apresenta o CNPJ da Entidade conforme informacao recebida | Comparacao com dado logico | CNPJ extraido vs. CNPJ informado | Sim/Nao | Doc. Constitutivo |
| l | Conferencia do valor do imovel em relacao ao limite maximo permitido pelo programa habitacional | Comparacao numerica com dado logico | Valor extraido do contrato vs. teto do programa por faixa de renda | Sim/Nao | Contrato Habitacional |
| m | Verificacao da correspondencia dos dados do bem oferecido como garantia no credito rural (chassi, modelo, numero de serie) com a apolice, clausula CAIXA como beneficiaria, e adequacao do valor do premio | Comparacao multi-campo pontual | Dados do bem vs. apolice de seguro | Sim/Nao | NF + Apolice |

### 3.4 Analise dos Exemplos — Padrao para Implementacao

| Padrao Identificado | Exemplos | Implementacao |
|--------------------|---------|--------------|
| **Campo >= Threshold** | a (idade >= 18), b (data em 90 dias), l (valor <= teto) | Extrair campo numerico/data, comparar com constante parametrizavel |
| **Campo == Dado logico** | g, h, i, j, k (nome/CPF/CNPJ confere com base) | Extrair campo, comparar com dado fornecido pela CAIXA (fuzzy match para nomes) |
| **Presenca de elemento** | d, e, f (assinatura, local/data, checkbox preenchidos) | Detectar se area/campo esta preenchido (nao vazio) |
| **Tipo confere** | c (tipo classificado == tipo solicitado) | Comparar resultado da classificacao com tipologia esperada |
| **Cruzamento pontual** | i (nome doc A == nome doc B), m (dados bem vs. apolice) | Comparar campos entre documentos do mesmo dossie |

---

## 4. REGRA COMPOSTA — ESPECIFICACAO COMPLETA

### 4.1 Definicao (TR 2.7.2.3)

Regra Composta e aquela que exige **multiplos criterios** de validacao, analises encadeadas ou etapas interdependentes, nas quais o resultado depende da **correlacao logica** entre duas ou mais verificacoes, informacoes, calculos ou fontes de dados, **nao sendo possivel obter a conclusao a partir de uma unica checagem isolada**.

### 4.2 Caracteristicas Formais (TR 2.7.2.3, a-h)

| # | Caracteristica | Descricao |
|---|---------------|----------|
| a | **Combinacao interdependente** | Envolve a combinacao de dois ou mais criterios de validacao, cuja aplicacao e interdependente para a obtencao do resultado |
| b | **Encadeamento logico** | Exige encadeamento logico, sequencial ou condicional, entre verificacoes, analises ou decisoes |
| c | **Calculo matematico** | Pode envolver calculo matematico, apuracao de valores, rendas, margens, limites ou percentuais, ainda que utilizando dados provenientes de uma ou mais fontes |
| d | **Correlacao entre multiplos campos** | Pode envolver correlacao entre multiplos campos, ainda que provenientes de um mesmo documento |
| e | **Cruzamento estruturado multi-documento** | Pode envolver cruzamento estruturado entre multiplos documentos, quando o resultado dependa da analise conjunta das informacoes |
| f | **Comparacao combinada com bases** | Pode envolver comparacao com dados de importacao, originacao, formularios eletronicos ou bases internas e externas, quando tais informacoes sejam utilizadas de forma combinada ou correlacionada |
| g | **Dados estruturados e nao estruturados** | Pode depender de dados estruturados ou nao estruturados, internos ou externos, quando utilizados em conjunto para compor a decisao final |
| h | **Interpretacao analitica** | Exige interpretacao analitica em situacoes em que a informacao nao esteja apresentada de forma objetiva, direta ou padronizada em um unico campo |

### 4.3 Exemplos do Edital — Regras Compostas (TR 2.7.2.3)

O TR fornece **5 exemplos explicitos** de regras compostas, cada um com alto nivel de detalhe:

#### Exemplo a) Poderes de Abertura de Conta no Contrato Social

| Aspecto | Detalhe |
|---------|--------|
| **Enunciado** | No contrato social: o Socio [xxx] possui poderes de Abertura de Conta |
| **Documento** | Documento Constitutivo (Contrato Social) |
| **Complexidade** | Interpretar clausulas de administracao para identificar quem tem poder especifico de abertura de conta |
| **Etapas** | 1) Identificar quadro societario → 2) Localizar clausulas de administracao → 3) Interpretar poderes delegados → 4) Verificar se socio especifico tem poder de abertura de conta |
| **Desafio tecnico** | Texto juridico nao padronizado, poderes podem estar implicitos ou delegados, alteracoes contratuais podem modificar poderes |
| **Tecnologia** | LLM obrigatorio — exige interpretacao semantica de texto juridico |

#### Exemplo b) Conferencia de Valores do Holerite

| Aspecto | Detalhe |
|---------|--------|
| **Enunciado** | No Holerite: o somatorio dos valores de debito corresponde ao campo Total Descontos |
| **Documento** | Holerite / Comprovante de Rendimentos |
| **Complexidade** | Extrair todos os itens de desconto da tabela, somar, e comparar com o total informado |
| **Etapas** | 1) Extrair tabela de proventos/descontos → 2) Identificar todos os itens de debito → 3) Calcular somatorio → 4) Comparar com campo "Total Descontos" |
| **Desafio tecnico** | Layouts de holerite variam por empresa, itens de desconto podem ter nomes diferentes, formatacao numerica variavel |
| **Tecnologia** | Table extraction + calculo matematico |

#### Exemplo c) Validacao de Margem Consignavel

| Aspecto | Detalhe |
|---------|--------|
| **Enunciado** | Validacao da margem consignavel do cliente, onde e necessario calcular se a parcela do emprestimo nao ultrapassa o percentual permitido sobre a remuneracao liquida informada |
| **Documento** | Holerite + dados do emprestimo (dado logico) |
| **Complexidade** | Calculo financeiro com multiplas variaveis de fontes diferentes |
| **Etapas** | 1) Extrair remuneracao liquida do holerite → 2) Obter percentual maximo permitido (dado logico/parametro) → 3) Calcular margem disponivel = liquido x percentual → 4) Obter valor da parcela pretendida (dado logico) → 5) Comparar parcela vs. margem disponivel |
| **Desafio tecnico** | Percentual pode variar por tipo de emprestimo, salario liquido pode ter componentes variaveis |
| **Tecnologia** | Extracao + calculo + comparacao com dados logicos |

#### Exemplo d) Identificacao de Onus/Impedimentos na Matricula de Imovel

| Aspecto | Detalhe |
|---------|--------|
| **Enunciado** | Identificacao quanto a existencia de onus ou impedimentos ao imovel dado como garantia, onde e necessario identificar na matricula do imovel, em toda a cadeia de registros, quanto a existencia de alguma situacao que possa impactar a aceitacao da garantia, bem como se ha item posterior que cancele ou anule tal impedimento |
| **Documento** | Certidao de Matricula de Imovel |
| **Complexidade** | Mais complexa do edital — analise semantica profunda de texto juridico |
| **Etapas** | 1) OCR completo da matricula (ate 20 paginas) → 2) Identificar todos os registros na cadeia dominial → 3) Para cada registro, detectar onus: hipotecas, penhoras, arrestos, indisponibilidades, usufrutos → 4) Verificar se onus identificados estao ativos ou foram cancelados por averbacoes posteriores → 5) Classificar impacto de cada onus na aceitacao da garantia → 6) Retornar lista de onus ativos com impacto |
| **Desafio tecnico** | Texto juridico extenso, linguagem cartorial, registros que referenciam outros registros, cancelamentos parciais, linguagem nao padronizada entre cartorios |
| **Tecnologia** | OCR + LLM obrigatorio — interpretacao semantica profunda com encadeamento logico de registros |

#### Exemplo e) Conformidade para Financiamento Agricola

| Aspecto | Detalhe |
|---------|--------|
| **Enunciado** | Validacao da conformidade para financiamento de aquisicao de trator agricola, onde e necessario aplicar multiplas verificacoes encadeadas para garantir a elegibilidade do bem e do fornecedor |
| **Documento** | Nota Fiscal + Apolice de Seguro + Projeto Tecnico + dados do programa |
| **Complexidade** | Multi-documento, multi-verificacao encadeada |
| **Etapas** | 1) Confirmar se o equipamento esta listado no projeto tecnico aprovado → 2) Verificar se o modelo atende as especificacoes minimas exigidas pelo programa de credito rural → 3) Analisar se o fornecedor esta habilitado junto ao agente financeiro → 4) Validar se a nota fiscal corresponde ao bem descrito no orcamento e se nao ha divergencias entre valores → 5) Verificar clausula da apolice tendo a CAIXA como beneficiaria → 6) Verificar adequacao do valor do premio |
| **Desafio tecnico** | 6 sub-verificacoes encadeadas, cada uma depende de documento diferente, cruzamento de dados entre 3-4 fontes |
| **Tecnologia** | Extracao multi-documento + regras encadeadas + cruzamento de dados |

### 4.4 Tabela Comparativa Simples vs. Composta

| Dimensao | Regra Simples | Regra Composta |
|----------|--------------|---------------|
| **Criterios** | Um unico | Dois ou mais interdependentes |
| **Encadeamento** | Nenhum | Logico, sequencial ou condicional |
| **Calculo matematico** | Nao exige | Pode exigir (somas, margens, percentuais) |
| **Fontes de dados** | Uma (mesmo que externa) | Multiplas combinadas |
| **Cruzamento** | Pontual (1 campo vs. 1 campo) | Estruturado (multiplos campos/documentos) |
| **Interpretacao** | Objetiva, direta | Analitica (pode nao estar padronizada) |
| **Tecnologia** | Regras deterministas + comparacao | LLM + calculos + correlacao + reasoning |
| **Exemplos no edital** | 13 exemplos | 5 exemplos |
| **Volume anual** | 96.151.084 (validacoes) / 353.792.880 (analises) | 1.690.623 (validacoes) / 127.100.382 (analises) |
| **Preco unitario** | Menor | Maior |

---

## 5. VOLUMETRIA

### 5.1 Volume de Validacoes (Servicos Isolados)

| Servico | Volume Anual |
|---------|-------------|
| **Validacao de regras simples** | **96.151.084** |
| **Validacao de regras compostas** | **1.690.623** |
| **TOTAL de validacoes** | **97.841.707** |

### 5.2 Volume de Analises (por Demanda)

| Servico | Volume Anual |
|---------|-------------|
| Analises demandas com regras Simples | **353.792.880** |
| Analises demandas com regras Compostas | **127.100.382** |
| **TOTAL de analises** | **~480.893.262** |

### 5.3 Interpretacao dos Dois Niveis de Volume

| Nivel | Significado | Exemplo |
|-------|-----------|---------|
| **Validacoes** (97,8M) | Numero de vezes que o servico "Validacao de regras" e acionado como servico isolado na proposta comercial | Uma demanda aciona "Validacao de regras simples" para verificar 5 campos → conta 5 validacoes |
| **Analises** (480,9M) | Numero total de itens de analise individuais executados dentro das demandas | Uma demanda com 20 regras simples + 3 compostas = 23 analises individuais |

### 5.4 Metricas Derivadas

| Metrica | Calculo | Valor |
|---------|---------|-------|
| Media de regras simples por validacao | 353.792.880 / 96.151.084 | **~3,7 regras por validacao** |
| Media de regras compostas por validacao | 127.100.382 / 1.690.623 | **~75 analises por validacao** |
| Proporcao simples vs. compostas (analises) | 353,8M / 480,9M | **73,6% simples / 26,4% compostas** |
| Regras simples por segundo (pico) | 96.151.084 / (250 x 12h x 3600s) | **~8,9 /segundo** |
| Media diaria (validacoes simples) | 96.151.084 / 365 | **~263.428 /dia** |
| Media diaria (validacoes compostas) | 1.690.623 / 365 | **~4.631 /dia** |

> **Alerta de escala:** 96 milhoes de validacoes simples por ano = ~263 mil por dia = ~22 mil por hora no pico. Exige automacao total e alta performance.

---

## 6. REGRAS POR LINHA DE NEGOCIO

### 6.1 Mapeamento de Regras Tipicas por Processo

| Processo | Regras Simples Tipicas | Regras Compostas Tipicas |
|----------|----------------------|------------------------|
| **Abertura de Conta** | Idade >= 18, CPF valido, nome confere, doc dentro da validade, tipo confere, endereco confere | Poderes de abertura de conta (PJ), verificacao de restricoes |
| **Concessao Habitacional** | Tipo doc confere, assinatura presente, IPTU quitado, registro CREA valido, data emissao em 90 dias | Margem consignavel, onus/impedimentos na matricula, valor imovel vs. teto programa x faixa renda, laudo vs. financiamento |
| **Agronegocio** | Tipo doc confere, DAP/CAF validos, licenciamento vigente, registro sanitario ativo | Conformidade de financiamento agricola (6 sub-verificacoes), elegibilidade de bem + fornecedor |
| **Concessao Comercial PJ** | CNPJ ativo, razao social confere, doc constitutivo atualizado, NF autentica | Poderes de representacao, quadro societario vs. RG dos socios, analise de endividamento |
| **Garantia Habitacional** | Matricula confere, apolice vigente, CAIXA como beneficiaria, valor segurado adequado | Onus na matricula, cruzamento laudo vs. contrato vs. matricula, clausulas da apolice |
| **Garantias Comerciais PJ** | Matricula confere, certidoes negativas validas, CNPJ ativo | Onus na matricula, poderes de oferecimento de garantia, cruzamento multi-doc |
| **Conta Digital / Onboarding** | Idade >= 18, CPF ativo na RF, nome confere, selfie match | (Poucas regras compostas — processo simplificado) |
| **Programa Pe de Meia** | Tipo doc confere, biometria OK | (Minimas — processo muito simples) |

### 6.2 Complexidade por Processo

| Processo | Volume | Regras Simples/Demanda (est.) | Regras Compostas/Demanda (est.) | Complexidade |
|----------|--------|------------------------------|-------------------------------|-------------|
| Programa Pe de Meia | 97.293 | 2–3 | 0 | MUITO BAIXA |
| Conta Digital | 4.704.706 | 3–5 | 0–1 | BAIXA |
| Abertura de Conta | 3.510.402 | 5–8 | 1–2 | MEDIA |
| Concessao Comercial PJ | 325.802 | 8–12 | 3–5 | ALTA |
| Concessao Habitacional | 1.839.620 | 10–15 | 5–10 | MUITO ALTA |
| Agronegocio | 460.607 | 10–15 | 5–8 | MUITO ALTA |
| Garantia Habitacional | 278.657 | 8–12 | 5–8 | MUITO ALTA |

---

## 7. RELACAO COM OUTROS SERVICOS

### 7.1 Posicao no Pipeline

```
[Documento tratado + classificado + dados extraidos + autenticidade validada]
         |
         v
  +--------------------------------------------------+
  | APLICACAO DE REGRAS NEGOCIAIS                     |  <-- ESTE SERVICO
  |                                                  |
  | +-------------------+  +----------------------+  |
  | | REGRAS SIMPLES    |  | REGRAS COMPOSTAS     |  |
  | | (96M validacoes)  |  | (1,7M validacoes)    |  |
  | |                   |  |                      |  |
  | | - Campo >= valor  |  | - Margem consignavel |  |
  | | - Campo == base   |  | - Onus na matricula  |  |
  | | - Presenca elem.  |  | - Poderes societarios|  |
  | | - Tipo confere    |  | - Conformidade agro  |  |
  | +--------+----------+  +----------+-----------+  |
  |          |                        |               |
  |          v                        v               |
  |   +--------------------------------------+        |
  |   | CONSOLIDACAO DO CHECKLIST             |        |
  |   | (todos os itens da demanda)           |        |
  |   +--------------------------------------+        |
  +--------------------------------------------------+
         |
         v
  [Resultado: CONFORME / NAO CONFORME / PENDENTE]
         |
    +----|----+---------+
    |         |         |
    v         v         v
 [Aprovado] [Rejeitado] [Revisao
                        Humana]
```

### 7.2 Dependencias Upstream

| Servico | Relacao | Critico? |
|---------|--------|---------|
| **Extracao de dados** | Fornece os campos que serao validados pelas regras (custo NAO remunerado separadamente) | SIM — sem extracao, nao ha regra |
| **Classificacao documental** | Define qual checklist de regras aplicar (por tipo + processo) | SIM — classificacao errada = regras erradas |
| **Validacao de autenticidade** | Score de fraude pode ser input para regras compostas | PARCIAL — regras podem rodar sem score |
| **Consulta em bases externas** | Dados de bases para cruzamento (RF, SEFAZ, cartorios) | PARCIAL — depende da regra |

### 7.3 Dependencias Downstream

| Servico | Como Usa o Resultado |
|---------|---------------------|
| **Decisao da demanda** | Resultado do checklist determina aprovacao, rejeicao ou revisao |
| **Rejeicao de documento** | Item de regra "NAO CONFORME" pode rejeitar o documento |
| **Rejeicao de dossie** | Regras criticas nao atendidas podem rejeitar o dossie inteiro |
| **Operacao assistida** | Itens "PENDENTE" ou inconclusivos escalados para revisao humana |
| **Dashboard** | Estatisticas de conformidade por regra, por processo, por agencia |

### 7.4 Extracao de Dados como Custo Embutido

> **Alerta financeiro:** Toda extracao de dados executada como etapa preparatoria para regras negociais **NAO e remunerada separadamente** (TR 2.3.2.3). O custo de OCR/IA necessario para extrair os campos que alimentam 96M de regras simples e 1,7M de regras compostas e absorvido no preco das regras.

---

## 8. MOTOR DE REGRAS — ARQUITETURA

### 8.1 Componentes do Motor

```
+------------------------------------------------------------------+
|                    MOTOR DE REGRAS NEGOCIAIS                     |
|                                                                  |
|  +-------------------+  +---------------------+                  |
|  | REPOSITORIO DE    |  | DADOS EXTRAIDOS     |                  |
|  | REGRAS (YAML/JSON)|  | (do documento)      |                  |
|  | - por processo    |  +----------+----------+                  |
|  | - por tipo doc    |             |                              |
|  | - por fila        |  +----------+----------+                  |
|  +---------+---------+  | DADOS LOGICOS       |                  |
|            |            | (da CAIXA/demanda)   |                  |
|            |            +----------+----------+                  |
|            |                       |                              |
|            v                       v                              |
|  +------------------------------------------+                    |
|  | ENGINE DE EXECUCAO                        |                    |
|  |                                          |                    |
|  | [Regras Simples]     [Regras Compostas]  |                    |
|  |  - Comparacao        - Encadeamento      |                    |
|  |  - Threshold         - Calculo           |                    |
|  |  - Presenca          - LLM reasoning     |                    |
|  |  - Match             - Multi-doc         |                    |
|  +------------------------------------------+                    |
|            |                                                      |
|            v                                                      |
|  +------------------------------------------+                    |
|  | RESULTADO POR ITEM                        |                    |
|  | CONFORME | NAO_CONFORME | INCONCLUSIVO    |                    |
|  +------------------------------------------+                    |
+------------------------------------------------------------------+
```

### 8.2 Tipos de Engine por Complexidade

| Engine | Complexidade | Uso | Tecnologia |
|--------|-------------|-----|-----------|
| **Rule Engine determinista** | Baixa | Regras simples (comparacao, threshold, presenca) | If/then/else, Python rules engine, Drools |
| **Calculo Engine** | Media | Regras compostas com calculo (margem, somatorio) | Python math, pandas, formulas parametrizaveis |
| **Cruzamento Engine** | Media-Alta | Cruzamento multi-documento, multi-campo | Join de datasets, fuzzy matching entre documentos |
| **LLM Reasoning Engine** | Alta | Interpretacao semantica (onus na matricula, poderes no contrato social) | Claude, GPT-4 com prompt engenharia especializado |
| **Workflow Engine** | Alta | Regras compostas com sub-verificacoes encadeadas (agro) | Orquestracao de etapas, DAG de verificacoes |

### 8.3 Parametrizacao Low-Code (Requisito do TR)

O TR exige que a CAIXA tenha **autonomia** para criar, editar e parametrizar fluxos sem intervencao tecnica (secao 2.10.2). Para regras negociais, isso significa:

| Capacidade | Descricao |
|-----------|----------|
| **Criacao de regra simples** | CAIXA define: campo do documento + operador (==, >=, <=, contem, presente) + valor esperado |
| **Criacao de regra composta** | CAIXA define: sequencia de etapas + condicoes logicas (E, OU, SE/ENTAO) + fontes de dados |
| **Edicao de checklist** | CAIXA adiciona/remove regras de um processo sem deploy tecnico |
| **Parametrizacao de thresholds** | CAIXA ajusta valores de corte (ex: mudar de 90 para 120 dias) |
| **Linguagem natural** | CAIXA descreve a regra em portugues e o sistema traduz para execucao (via IA) |

---

## 9. SLAs E QUALIDADE

### 9.1 Niveis de Servico por Fila

| Fila | SLA Total (horas) | Tempo Estimado para Regras |
|------|-------------------|---------------------------|
| Programa Pe de Meia | **1h** | < 5 segundos (2-3 regras simples) |
| Abertura Conta Agencia/CCA | **1h** | < 15 segundos (5-8 simples + 1-2 compostas) |
| Garantias Comerciais PJ | **18h** | < 10 minutos (regras compostas com matricula) |
| Concessao Comercial PJ | **18h** | < 10 minutos |
| Concessao Habitacional | **24h** | < 15 minutos (dossie grande + onus + margem) |
| Agronegocio | **24h** | < 15 minutos (conformidade com 6 sub-verificacoes) |

### 9.2 Metricas de Qualidade

| Metrica | Meta | Justificativa |
|---------|------|--------------|
| **Acuracia regras simples** | >= 99% | Comparacoes objetivas devem ter erro proximo de zero |
| **Acuracia regras compostas** | >= 95% | Interpretacao semantica tem margem de erro maior |
| **Completude do checklist** | 100% | Todos os itens devem ser avaliados (nenhum ignorado) |
| **Taxa de "inconclusivo"** | <= 5% | Maximo de itens sem resultado definido |
| **Latencia regra simples (P95)** | < 500ms | Comparacao direta e rapida |
| **Latencia regra composta (P95)** | < 30 segundos | LLM + calculos + cruzamentos |

### 9.3 Penalidades

| Tipo | Formula |
|------|---------|
| Deducao por servico incorreto (VDSI) | `VDSI = 0,05% x SI x VSETF` |
| Teto de deducoes | **10% do VSETF** |

> **Risco:** Uma regra composta aplicada incorretamente (ex: onus na matricula nao detectado) pode gerar prejuizo financeiro direto para a CAIXA. A responsabilidade e da CONTRATADA.

---

## 10. MODELO DE DADOS DE SAIDA

### 10.1 Resultado por Demanda

```json
{
  "demanda_id": "DEM-2026-001234",
  "processo": "concessao_habitacional",
  "fila": "Concessao Habitacional",
  "timestamp": "2026-04-10T14:30:00Z",
  "resultado_consolidado": "NAO_CONFORME",
  "total_itens": 18,
  "itens_conformes": 16,
  "itens_nao_conformes": 1,
  "itens_inconclusivos": 1,
  "regras_simples": {
    "total": 12,
    "conformes": 12,
    "itens": [
      {"id": "RS-001", "descricao": "Titular possui idade >= 18 anos", "resultado": "CONFORME", "valor_encontrado": "35 anos", "valor_esperado": ">= 18"},
      {"id": "RS-002", "descricao": "Data emissao RG em 3600 dias", "resultado": "CONFORME", "valor_encontrado": "2024-03-15", "dias": 757},
      {"id": "RS-003", "descricao": "Nome no RG confere com dado logico", "resultado": "CONFORME", "similaridade": 1.0},
      {"id": "RS-004", "descricao": "IPTU quitado", "resultado": "CONFORME"},
      {"id": "RS-005", "descricao": "Registro CREA do engenheiro valido", "resultado": "CONFORME"},
      {"id": "RS-006", "descricao": "Assinatura do gerente preenchida", "resultado": "CONFORME"}
    ]
  },
  "regras_compostas": {
    "total": 6,
    "conformes": 4,
    "nao_conformes": 1,
    "inconclusivos": 1,
    "itens": [
      {
        "id": "RC-001",
        "descricao": "Margem consignavel suficiente",
        "resultado": "CONFORME",
        "detalhamento": {
          "remuneracao_liquida": 8500.00,
          "percentual_maximo": 0.35,
          "margem_disponivel": 2975.00,
          "parcela_pretendida": 2200.00,
          "resultado": "Parcela (R$ 2.200) <= Margem (R$ 2.975)"
        }
      },
      {
        "id": "RC-002",
        "descricao": "Onus ou impedimentos na matricula do imovel",
        "resultado": "NAO_CONFORME",
        "detalhamento": {
          "onus_encontrados": [
            {"tipo": "Hipoteca", "registro": "R-15", "favorecido": "Banco XYZ", "status": "ATIVO", "impacto": "Impede nova garantia"},
            {"tipo": "Penhora", "registro": "AV-22", "origem": "Justica do Trabalho", "status": "ATIVO", "impacto": "Impede alienacao"}
          ],
          "cancelamentos_posteriores": [],
          "conclusao": "Existem 2 onus ativos que impedem a aceitacao do imovel como garantia"
        }
      },
      {
        "id": "RC-003",
        "descricao": "Valor do imovel vs. limite do programa por faixa de renda",
        "resultado": "INCONCLUSIVO",
        "motivo": "Faixa de renda do proponente nao informada nos dados logicos"
      }
    ]
  }
}
```

---

## 11. CENARIOS DE TESTE

### 11.1 Cenarios Regras Simples

| # | Cenario | Input | Resultado |
|---|---------|-------|----------|
| 1 | Titular com 25 anos | Data nasc: 2001-01-15 | CONFORME (25 >= 18) |
| 2 | Titular com 17 anos | Data nasc: 2009-05-20 | NAO_CONFORME (17 < 18) |
| 3 | Doc emitido ha 89 dias | Data emissao: 2026-01-11 | CONFORME (89 < 90) |
| 4 | Doc emitido ha 91 dias | Data emissao: 2026-01-09 | NAO_CONFORME (91 > 90) |
| 5 | Nome confere exatamente | "JOSE DA SILVA" == "JOSE DA SILVA" | CONFORME |
| 6 | Nome com acentuacao diferente | "JOSE" vs "JOSÉ" | CONFORME (fuzzy match) |
| 7 | Nome divergente | "JOSE DA SILVA" vs "MARIA SANTOS" | NAO_CONFORME |
| 8 | Assinatura presente | Area preenchida | CONFORME |
| 9 | Assinatura ausente | Area vazia | NAO_CONFORME |
| 10 | CPF no doc confere com RF | "123.456.789-00" vs RF | CONFORME |

### 11.2 Cenarios Regras Compostas

| # | Cenario | Regra | Resultado |
|---|---------|-------|----------|
| 11 | Margem OK (parcela < margem) | Liquido R$ 10.000, 35%, parcela R$ 3.000 | CONFORME (3.000 < 3.500) |
| 12 | Margem insuficiente | Liquido R$ 5.000, 35%, parcela R$ 2.500 | NAO_CONFORME (2.500 > 1.750) |
| 13 | Matricula sem onus | Matricula limpa, nenhum registro de onus | CONFORME |
| 14 | Matricula com onus ativo | Hipoteca ativa em R-15 | NAO_CONFORME |
| 15 | Matricula com onus cancelado | Hipoteca em R-15, cancelada em AV-18 | CONFORME |
| 16 | Socio com poder de abertura | Clausula 5a: "socio A administra..." | CONFORME |
| 17 | Socio sem poder especifico | Clausula omissa sobre abertura de conta | NAO_CONFORME/INCONCLUSIVO |
| 18 | Somatorio holerite confere | Descontos: 500+200+100 = Total 800 | CONFORME |
| 19 | Somatorio holerite nao confere | Descontos: 500+200+100 != Total 900 | NAO_CONFORME |
| 20 | Conformidade agro (6 etapas OK) | Todas as 6 sub-verificacoes passam | CONFORME |
| 21 | Conformidade agro (fornecedor nao habilitado) | Etapa 3 falha | NAO_CONFORME |
| 22 | Volume de pico (1000 demandas simultaneas) | Misto de simples + compostas | SLA atendido |

---

## 12. PRECIFICACAO

### 12.1 Estrutura de Precos (Dois Itens Separados)

| Servico | Volume Anual | Unidade |
|---------|-------------|---------|
| **Validacao de regras simples** | 96.151.084 | Por validacao |
| **Validacao de regras compostas** | 1.690.623 | Por validacao |

### 12.2 Componentes de Custo

| Componente | Regras Simples | Regras Compostas |
|-----------|---------------|-----------------|
| Extracao de dados (embutida, NAO remunerada) | 1 campo/regra | 2-10 campos/regra |
| Consultas a bases externas | Ocasional | Frequente |
| Processamento computacional | Minimo (comparacao) | Alto (LLM, calculo, cruzamento) |
| LLM (para interpretacao semantica) | NAO necessario | NECESSARIO (onus, poderes, conformidade) |
| Motor de regras (manutencao) | Baixo | Alto (regras complexas, encadeamento) |
| Infraestrutura | Compartilhada | GPU para LLM |

### 12.3 Alerta de Precificacao

> **Regras simples:** Volume massivo (96M/ano) com custo unitario baixo. A margem vem do volume. O custo de extracao embutido e o principal fator — otimizar OCR para extracoes rapidas/parciais.
>
> **Regras compostas:** Volume menor (1,7M/ano) mas custo unitario MUITO mais alto. LLM (Claude/GPT) para interpretar onus na matricula ou poderes no contrato social custa ~R$ 0,05-0,50 por chamada. Precificar com margem generosa.
>
> **Volume real de analises:** O volume de 480M de analises individuais mostra que cada validacao contem em media 3,7 (simples) ou 75 (compostas) itens de analise. O motor de regras precisa ser extremamente performatico.

---

## 13. RISCOS ESPECIFICOS

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| 1 | **LLM interpreta errado onus na matricula** | Media | Garantia aceita com impedimento — prejuizo financeiro | Prompts especializados, validacao cruzada, threshold de confianca, escalacao para humano |
| 2 | **CAIXA cria regra complexa via low-code que nao funciona** | Alta | Resultados incorretos em producao | Validacao automatica de regras, ambiente de teste, rollback |
| 3 | **Custo de LLM para 1,7M regras compostas** | Certa | Erosao de margem (~R$ 85K-850K/ano so em LLM) | Otimizar prompts, cache de interpretacoes similares, modelos menores para casos padrao |
| 4 | **Regra simples com fuzzy match retorna falso positivo/negativo** | Media | Nome "JOSE DA SILVA" vs "JOSE D. SILVA" — confere ou nao? | Threshold parametrizavel de similaridade, normalizacao de nomes |
| 5 | **Volume de 96M regras simples em SLA de 1h** | Alta | Backlog se performance degradar | Pre-processamento batch, cache de resultados, auto-scaling |
| 6 | **Alteracao de regras pela CAIXA sem aviso previo** | Media | Sistema aplica regras desatualizadas | Versionamento de regras, auditoria de alteracoes, hot-reload |
| 7 | **Dados logicos inconsistentes fornecidos pela CAIXA** | Media | Regra retorna "inconclusivo" por falta de dado | Validacao de inputs, tratamento de dados ausentes, feedback a CAIXA |
| 8 | **Interpretacao de poderes societarios ambigua** | Alta | Socio considerado com/sem poderes erroneamente | LLM com exemplos few-shot do dominio, revisao por especialista juridico nos prompts |

---

## 14. CHECKLIST DE IMPLEMENTACAO

### Fase 1 — MVP (Regras Simples Deterministas)

- [ ] Motor de regras simples: comparacao (==, !=, >=, <=, contem)
- [ ] Suporte a tipos: numerico, texto, data, booleano (presenca)
- [ ] Comparacao com dado logico (fornecido pela CAIXA na demanda)
- [ ] Fuzzy match para nomes (Levenshtein/Jaro-Winkler com threshold)
- [ ] Validacao de CPF/CNPJ (digito verificador)
- [ ] Calculo de diferenca de datas (dias entre emissao e hoje)
- [ ] Presenca de elemento (assinatura, checkbox, campo preenchido)
- [ ] Retorno JSON com CONFORME/NAO_CONFORME/INCONCLUSIVO por item
- [ ] API REST documentada
- [ ] Logs com demanda_id, regra_id, resultado, latencia

### Fase 2 — Regras Compostas Basicas (Calculo + Cruzamento)

- [ ] Engine de calculo: somatorio, percentual, margem
- [ ] Cruzamento multi-documento (campo doc A vs. campo doc B)
- [ ] Validacao de margem consignavel (holerite + dados emprestimo)
- [ ] Conferencia de somatorios (proventos - descontos = liquido)
- [ ] Conferencia valor imovel vs. teto programa
- [ ] Cruzamento de dados do bem com apolice de seguro
- [ ] Encadeamento sequencial (SE etapa 1 OK, ENTAO executar etapa 2)
- [ ] Dashboard de resultados por regra, por processo

### Fase 3 — Regras Compostas Avancadas (LLM + Semantica)

- [ ] LLM para interpretacao de onus na matricula de imovel
- [ ] LLM para interpretacao de poderes no contrato social
- [ ] Conformidade agricola com 6 sub-verificacoes encadeadas
- [ ] Interface low-code para CAIXA criar/editar regras
- [ ] Parametrizacao via linguagem natural (IA traduz regra descrita em portugues)
- [ ] Versionamento de regras com historico e rollback
- [ ] Feedback loop: resultados de revisao humana retroalimentam LLM
- [ ] A/B testing de prompts para regras semanticas
- [ ] Auto-scaling para volume de pico (96M simples/ano)
- [ ] Cache de interpretacoes recorrentes (mesma clausula em diferentes matriculas)

---

## 15. REFERENCIAS NORMATIVAS

| Documento | Secao | Conteudo |
|-----------|-------|---------|
| Anexo I — TR | 2.7 | Definicao do servico de aplicacao de regras negociais |
| Anexo I — TR | 2.7.1 | 4 operacoes obrigatorias |
| Anexo I — TR | 2.7.2 | Regras compostas por Itens de Analise com diferenciacao na tarifacao |
| Anexo I — TR | 2.7.2.1 | **Regra Simples** — definicao + 8 caracteristicas (a-h) + 13 exemplos (a-m) |
| Anexo I — TR | 2.7.2.2 | Definicao de informacao externa |
| Anexo I — TR | 2.7.2.3 | **Regra Composta** — definicao + 8 caracteristicas (a-h) + 5 exemplos (a-e) |
| Anexo I — TR | 2.7.3 | Demandas podem conter itens simples E compostos |
| Anexo I — TR | 2.3.2.3 | Extracao de dados como etapa preparatoria NAO remunerada |
| Anexo I — TR | 2.10.2 | Low-code/no-code + linguagem natural para parametrizacao |
| Anexo I — TR | 5.2 | Formula de remuneracao |
| Anexo I — TR | 5.5 | Deducoes por servico incorreto |
| Anexo I-A | Definicoes | Itens de analises, itens simples, itens compostos, itens de precisao |
| Anexo I-B | Padrao Tecnologico | Formatos, protocolos, integracoes |
| Anexo I-C | Secao 5 | Volumes: 96.151.084 simples + 1.690.623 compostas |
| Anexo I-C | Secao 5.3 | Analises: 353.792.880 simples + 127.100.382 compostas |
| Anexo I-H | Filas | SLAs por fila (1h, 18h, 24h) |
