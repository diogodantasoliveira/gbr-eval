# Servico de Classificacao Documental
## Especificacao Completa — Edital BPO CAIXA

**Referencia:** Termo de Referencia, Secao 2.5 | Anexo I-A (Definicoes) | Anexo I-C (Volumetria) | Anexo I-H (Filas)
**Ultima atualizacao:** 2026-04-10

---

## 1. DEFINICAO FORMAL

> **Classificacao documental** — Identificacao do tipo de documento baseado na imagem submetida, que deve ser realizada conforme tipologia definida pela CAIXA junto a CONTRATADA.
>
> — Anexo I-A, Definicoes de Termos

O servico consiste em receber um documento digital (ja tratado ou nao) e **identificar automaticamente a que tipo documental ele pertence**, dentro de uma tipologia previamente definida e acordada com a CAIXA. O resultado da classificacao e retornado vinculado ao identificador da demanda.

**Objetivo central:** Permitir que o pipeline de processamento saiba qual tipo de documento esta sendo analisado, para que os servicos subsequentes (extracao de dados, validacao de autenticidade, aplicacao de regras) possam aplicar as rotinas corretas para aquele tipo especifico.

---

## 2. ESCOPO DETALHADO DO SERVICO

### 2.1 Operacoes Obrigatorias (TR 2.5.1)

O servico de classificacao documental consiste em:

| # | Operacao | Descricao Detalhada |
|---|----------|-------------------|
| 1 | **Classificar o documento** | Identificar o tipo do documento conforme tipologia previamente definida pela CAIXA |
| 2 | **Retornar a classificacao** | Retornar a CAIXA a classificacao da tipologia, vinculada ao identificador da demanda |

### 2.2 Implicacoes Nao Explicitas

Embora o TR descreva o servico de forma concisa (secao 2.5 e curta e direta), a classificacao documental tem implicacoes profundas:

| Implicacao | Descricao |
|-----------|----------|
| **Tipologia e definida pela CAIXA** | A contratada NAO define os tipos — a CAIXA define e a contratada implementa |
| **Tipologia pode mudar** | A CAIXA pode incluir, excluir ou alterar tipos documentais durante a vigencia do contrato |
| **Vinculacao obrigatoria ao ID** | Toda classificacao deve estar rastreavel ao identificador unico da demanda |
| **Alimenta toda a cadeia** | Uma classificacao errada propaga erros para extracao, validacao e regras negociais |
| **Uso de IA e obrigatorio** | O TR exige uso de IA para classificacao (secao 2.10.2 — Automacao Inteligente) |
| **Suporte a mosaico** | Quando o tratamento de arquivo digital separa um mosaico, cada sub-imagem precisa ser classificada individualmente |

---

## 3. TAXONOMIA DE DOCUMENTOS (TIPOLOGIA)

### 3.1 Catalogo Completo de Tipos Documentais

Extraido do Anexo I-C, secao 2 — estes sao os **32 tipos documentais** que o classificador precisa reconhecer:

| # | Tipo Documental | Descricao | Paginas (media) | Caracteristicas Visuais Distintivas |
|---|----------------|-----------|-----------------|-------------------------------------|
| 1 | Alvara de construcao | Documento municipal, geralmente 1 pagina com anexos | 1–3 | Brasao municipal, carimbo prefeitura, formato oficio |
| 2 | Apolice de Seguro | Condicoes gerais e certificado | 2–5 | Logo seguradora, tabelas de coberturas, numero apolice |
| 3 | Certidao da Matricula Imovel | Historico do imovel, extensao variavel | 2–20 | Numero da matricula, selo cartorial, carimbo registro |
| 4 | Certidao de Estado Civil | Nascimento, casamento, obito | 1 | Selo cartorial, brasao, formato padronizado |
| 5 | Certidao de onus de imovel | Geralmente 1 pagina | 1–2 | Selo cartorial, referencia a matricula |
| 6 | Certidoes (DAP/CAF/CCIR/ITR/CAR) | Conjunto de certidoes rurais/fiscais | 8–12 | Logos de orgaos federais (INCRA, RF, IBAMA) |
| 7 | Comprovante de Faturamento | Extratos, DRE, relatorios | 3–10 | Tabelas numericas, cabecalho contabil |
| 8 | Comprovante de constituicao de garantia | Termos e registros | 3–8 | Termos juridicos, assinaturas, carimbos |
| 9 | Contrato Comercial | Variavel conforme complexidade | 8–20 | Clausulas numeradas, assinaturas, testemunhas |
| 10 | Contrato Habitacional | Contrato e anexos padronizados CAIXA | 15–30 | Logo CAIXA, formato padronizado, muitas paginas |
| 11 | Contrato comercial registrado | Contrato + registro cartorial | 10–25 | Selo cartorio sobre contrato, carimbo registro |
| 12 | Contrato de arrendamento | Conforme prazo e clausulas | 5–15 | Clausulas de arrendamento, prazos, valores |
| 13 | Documento constitutivo | Contrato social e alteracoes | 5–20 | Junta Comercial, clausulas societarias, quadro de socios |
| 14 | Documento de licenciamento ambiental | Licenca, pareceres e anexos | 5–30 | Logo IBAMA/orgao ambiental, mapas, coordenadas |
| 15 | Documento de margem | Formulario de margem consignavel | 1–2 | Formato formulario, campos estruturados |
| 16 | Ficha de registro sanitario | Depende do orgao emissor | 1–4 | Logo ANVISA/orgao sanitario, numero registro |
| 17 | IPTU | Carne ou espelho | 1–3 | Codigo de barras, brasao municipal, valor venal |
| 18 | IRPF | Declaracao, recibo e anexos | 5–20 | Logo Receita Federal, CPF, tabelas de rendimentos |
| 19 | Identificacao (RG) | Documento de identidade | 1 | Foto 3x4, impressao digital, numero RG, orgao expedidor |
| 20 | Identificacao (CNH) | Carteira de habilitacao | 1–2 | Foto, categorias, numero registro, QR code |
| 21 | Laudo de Avaliacao do Imovel | Fotos, memorial e parecer | 15–40 | Fotos do imovel, planta, memorial descritivo, ART |
| 22 | Laudo de vistoria | Relatorio fotografico | 5–15 | Fotos sequenciais, checklist, assinatura responsavel |
| 23 | Modelo Padrao Caixa | Formularios internos — MO | 1–5 | Logo CAIXA, formato padronizado, campos estruturados |
| 24 | Nota fiscal | Documento fiscal | 1–2 | CNPJ, numero NF, impostos, descricao itens |
| 25 | CRLV | Certificado de registro de veiculo | 1 | Dados do veiculo, placa, chassi, logo DETRAN |
| 26 | Parecer Juridico | Depende da complexidade | 3–10 | Cabecalho escritorio/OAB, fundamentacao, conclusao |
| 27 | Plano de negocios | Documento estruturado | 10–30 | Sumario executivo, projecoes financeiras, graficos |
| 28 | Registro no CREA | Certidao simples | 1–3 | Logo CREA, numero registro, habilitacoes |
| 29 | Renda (Holerite) | Comprovante de rendimentos | 1–3 | Cabecalho empresa, valores discriminados, INSS/IRRF |
| 30 | Renda (Extrato bancario) | Movimentacao financeira | 3–10 | Logo banco, agencia/conta, lancamentos |
| 31 | Residencia | Conta de consumo (agua, luz, gas, telefone) | 1–3 | Logo concessionaria, endereco, codigo barras |
| 32 | Selfie | Foto do rosto do cliente | 1 | Foto frontal, sem documento, fundo variavel |

### 3.2 Agrupamento por Familia Documental

Para facilitar a arquitetura do classificador, os documentos podem ser agrupados em familias:

| Familia | Tipos Incluidos | Qtd |
|---------|----------------|-----|
| **Identificacao pessoal** | RG, CNH, Selfie | 3 |
| **Certidoes cartoriais** | Matricula imovel, Estado civil, Onus imovel, Certidoes rurais (DAP/CAF/CCIR/ITR/CAR) | 4 |
| **Contratos** | Comercial, Habitacional, Comercial registrado, Arrendamento | 4 |
| **Documentos societarios** | Documento constitutivo (contrato social), Parecer juridico | 2 |
| **Documentos fiscais** | Nota fiscal, CRLV, IPTU, IRPF | 4 |
| **Documentos de renda** | Holerite, Extrato bancario, Comprovante de faturamento | 3 |
| **Laudos e vistorias** | Laudo de avaliacao, Laudo de vistoria | 2 |
| **Documentos imobiliarios** | Alvara de construcao, Registro CREA | 2 |
| **Seguros e garantias** | Apolice de seguro, Comprovante de constituicao de garantia | 2 |
| **Documentos especiais** | Licenciamento ambiental, Ficha registro sanitario, Documento de margem, Plano de negocios | 4 |
| **Formularios internos** | Modelo Padrao Caixa | 1 |
| **Comprovante endereco** | Residencia (conta consumo) | 1 |

### 3.3 Nivel de Dificuldade de Classificacao

| Dificuldade | Tipos | Justificativa |
|------------|-------|--------------|
| **FACIL** — Layout muito padronizado, visualmente distinto | RG, CNH, Selfie, IPTU, Nota fiscal, CRLV, Modelo Padrao Caixa, Residencia | Formato visual muito reconhecivel, logos e layouts consistentes |
| **MEDIO** — Layout semi-padronizado, variacao entre emissores | Certidao estado civil, Certidao matricula, Certidao onus, Holerite, IRPF, Alvara, Registro CREA, Apolice, Extrato bancario | Layouts variam por cartorio/empresa/orgao, mas estrutura geral e reconhecivel |
| **DIFICIL** — Layout variavel, multipaginas, sobreposicao com outros tipos | Contrato comercial vs. Contrato registrado, Contrato habitacional, Documento constitutivo, Parecer juridico, Plano de negocios, Laudo avaliacao, Licenciamento ambiental | Documentos extensos, layouts variam muito, dificil distinguir subtipos de contrato, confusao entre parecer e laudo |
| **MUITO DIFICIL** — Ambiguidade semantica | Comprovante faturamento vs. Extrato vs. Holerite, Certidoes rurais (DAP vs. CAF vs. CCIR vs. ITR vs. CAR), Ficha registro sanitario, Documento de margem | Visualmente similares, diferenciacao depende do conteudo textual |

---

## 4. VOLUMETRIA

### 4.1 Volume Anual Estimado

| Metrica | Valor |
|---------|-------|
| **Classificacao documental** | **19.659.587 / ano** |
| Media mensal estimada | ~1.638.299 / mes |
| Media diaria estimada (dias uteis ~250) | ~78.638 / dia |
| Media diaria estimada (24x7 = 365 dias) | ~53.862 / dia |
| Media horaria estimada (pico 08h-20h) | ~6.553 / hora |
| Media por segundo (pico) | ~1,8 / segundo |

### 4.2 Distribuicao por Processo de Origem

O volume de classificacoes se distribui pelos processos, proporcional ao numero de documentos em cada dossie:

| Processo | Demandas/Ano | Docs por Dossie (est.) | Classificacoes Estimadas |
|----------|-------------|----------------------|------------------------|
| ONBOARDING FGTS | 6.829.602 | 1–2 | ~8.200.000 |
| Conta Digital | 4.704.706 | 1–2 | ~5.600.000 |
| ONBOARDING | 4.558.404 | 1–2 | ~5.500.000 |
| Abertura de Conta | 3.510.402 | 3–4 | ~12.000.000 |
| Concessao Habitacional | 1.839.620 | 8–12 | ~18.400.000 |
| Dossie CCA | 1.134.461 | 3–5 | ~4.500.000 |
| Agronegocio | 460.607 | 10–14 | ~5.500.000 |
| Garantias Comerciais PJ | 382.962 | 4–6 | ~1.900.000 |
| Concessao Comercial PJ | 325.802 | 5–7 | ~2.000.000 |
| Garantia Habitacional CIP | 278.657 | 5–8 | ~1.800.000 |
| Programa Pe de Meia | 97.293 | 1–2 | ~150.000 |

> **Nota:** O total de classificacoes (19.659.587) e identico ao volume de tratamento de arquivo digital e extracao de atributos, indicando que **cada documento tratado e classificado e tem seus atributos extraidos**.

### 4.3 Distribuicao Estimada por Tipo Documental

Com base na composicao dos dossies e volumes por processo:

| Tipo Documental | Volume Estimado/Ano | % do Total |
|----------------|--------------------|-----------| 
| Identificacao (RG/CNH) | ~5.500.000 | ~28% |
| Selfie | ~3.000.000 | ~15% |
| Residencia | ~2.000.000 | ~10% |
| Renda (holerite/extrato) | ~1.800.000 | ~9% |
| Certidao de Estado Civil | ~1.500.000 | ~8% |
| Certidao Matricula Imovel | ~1.200.000 | ~6% |
| IRPF | ~800.000 | ~4% |
| Contrato Habitacional | ~700.000 | ~4% |
| Documento Constitutivo | ~600.000 | ~3% |
| Demais (20+ tipos) | ~2.559.587 | ~13% |

> **Alerta:** Identificacao + Selfie + Residencia respondem por ~53% do volume. O classificador deve ter acuracia maxima nesses tipos de alta frequencia.

---

## 5. REGRAS DE NEGOCIO

### 5.1 Definicao da Tipologia

- A **tipologia e definida pela CAIXA** em conjunto com a CONTRATADA (Anexo I-A)
- A CAIXA pode **alterar a tipologia** (incluir, excluir, renomear tipos) durante a vigencia contratual
- A contratada deve ter capacidade de **adaptar o classificador** a novas tipologias sem indisponibilidade

### 5.2 Vinculacao ao Identificador

- Toda classificacao retornada deve estar **vinculada ao identificador da demanda**
- O identificador permite rastrear: qual documento, de qual dossie, em qual fila, recebeu qual classificacao

### 5.3 Relacao com Tratamento de Arquivo Digital

- Quando o servico de tratamento de arquivo digital separa um **mosaico** (multiplos documentos em uma imagem), cada sub-imagem resultante deve ser classificada individualmente
- A classificacao pode ocorrer **antes ou depois** do tratamento, conforme a jornada definida pela CAIXA
- Quando a CAIXA define classificacao para mosaicos, imagens que nao correspondem a tipologia solicitada devem ser desconsideradas (TR 2.8.2)

### 5.4 Classificacao como Etapa do Pipeline

A classificacao documental funciona como **roteador logico** dentro do pipeline de processamento. Dependendo do tipo identificado, o sistema deve acionar:

| Tipo Classificado | Proximo Servico Acionado |
|------------------|------------------------|
| Identificacao (RG/CNH) | Extracao de dados pessoais + Validacao de autenticidade (biometria facial) |
| Contrato social | Extracao de quadro societario + Regra composta (poderes de representacao) |
| Matricula imovel | Extracao de dados do imovel + Regra composta (onus e gravames) |
| Holerite | Extracao de valores + Regra composta (margem consignavel) |
| Selfie | Validacao biometrica (comparacao com foto do RG/CNH) |
| IRPF | Extracao de rendimentos + Regras de validacao fiscal |
| Certidao | Extracao de dados + Validacao de vigencia |
| Contrato Habitacional | Extracao de clausulas + Regras de conformidade |

### 5.5 Remuneracao

| Item | Valor |
|------|-------|
| Nome do servico na proposta | Classificacao documental |
| Quantidade anual | 19.659.587 |
| Unidade de cobranca | Por documento classificado |
| Formula | Quantidade executada x Valor Unitario |

### 5.6 Tratamento de Incerteza

O TR nao detalha explicitamente como tratar classificacoes com baixa confianca. Recomendacao de produto:

| Confianca | Acao |
|-----------|------|
| >= 95% | Classificar automaticamente |
| 70%–95% | Classificar com flag de revisao |
| < 70% | Encaminhar para revisao humana (Operacao Assistida) |
| Tipo nao reconhecido | Retornar como "nao classificado" com motivo |

---

## 6. RELACAO COM DOSSIES POR LINHA DE NEGOCIO

### 6.1 Composicao de Dossies e Tipos Esperados

O classificador precisa saber quais tipos sao **esperados** em cada processo, pois isso aumenta a acuracia (prior probability):

| Processo | Tipos Documentais Esperados no Dossie |
|----------|--------------------------------------|
| **Abertura de Conta** | Certidao de Estado Civil, Documento de Identificacao, Documentos de Renda, Residencia |
| **Agronegocio** | Apolice de Seguro, Certidao de Estado Civil, Certidao de Onus de Imovel, Certidoes DAP/CAF/CCIR/ITR/CAR, Contrato Comercial Registrado, Contrato de Arrendamento, Documento Constitutivo, Documento de Licenciamento Ambiental, Ficha de Registro Sanitario, Identificacao, Laudo de Vistoria, Plano de Negocios |
| **Concessao Comercial PJ** | Certidao da Matricula Imovel, Contrato Comercial Registrado, Documento Constitutivo, Modelo Padrao Caixa, Nota Fiscal ou CRLV, Parecer Juridico |
| **Concessao Habitacional** | Alvara de Construcao, Certidao de Estado Civil, Certidoes DAP/CAF/CCIR/ITR/CAR, Documento Constitutivo, IPTU, Declaracao de IRPF, Documentos de Identificacao, Laudo de Avaliacao do Imovel, Registro no CREA, Renda |
| **Garantia Habitacional** | Apolice de Seguro, Certidao da Matricula Imovel, Contrato Habitacional, Contrato Comercial Registrado, Laudo de Avaliacao do Imovel, Nota Fiscal ou CRLV, Parecer Juridico |
| **Garantias Comerciais PJ** | Certidao da Matricula Imovel, Certidoes DAP/CAF/CCIR/ITR/CAR, Contrato Comercial Registrado, Documento Constitutivo |
| **Programa Pe de Meia** | Identificacao, Selfie |

### 6.2 Classificacao Contextual

> **Insight de produto:** Se o sistema sabe que a demanda pertence ao processo "Programa Pe de Meia", o classificador so precisa distinguir entre Identificacao e Selfie — tarefa trivial. Ja para "Agronegocio", precisa distinguir 12+ tipos — tarefa complexa. O **contexto do processo deve ser usado como input** para aumentar a acuracia.

---

## 7. DEFINICOES TECNICAS RELACIONADAS

Termos do Anexo I-A diretamente aplicaveis:

### 7.1 Classificacao Documental
Identificacao do tipo de documento baseado na imagem submetida, que deve ser realizada conforme tipologia definida pela CAIXA junto a CONTRATADA.

### 7.2 Extensao de Arquivo
Formato do arquivo computacional a ser transitado entre sistemas. Ex: pdf, png, bmp, etc. O classificador deve operar independentemente do formato de entrada.

### 7.3 Area Util do Documento
Area da imagem representativa do documento a ser manipulado, contendo os dados para extracao, limitado pelas bordas limites e/ou caracteristicas especificas de cada tipo de documento. A classificacao usa a area util como input principal.

### 7.4 Mosaico
Presenca de mais de um documento digitalizado em uma unica imagem. Cada documento separado do mosaico deve ser classificado individualmente.

### 7.5 Atributo Extraido
Informacao textual presente em documento. O classificador pode usar atributos extraidos (via OCR parcial) como features auxiliares para classificacao.

---

## 8. OPERACOES TECNICAS DETALHADAS

### 8.1 Pipeline de Classificacao

```
[Documento digital recebido]
         |
         v
  +----------------------------+
  | PRE-PROCESSAMENTO          |
  | (resize, normalize, grayscale)|
  +----------------------------+
         |
         v
  +----------------------------+
  | FEATURE EXTRACTION         |
  | Visual: CNN/ViT features   |
  | Textual: OCR parcial       |
  | Layout: spatial features   |
  +----------------------------+
         |
         v
  +----------------------------+
  | CLASSIFICACAO MULTIMODAL   |
  | Visual + Textual + Layout  |
  | + Contexto do processo     |
  +----------------------------+
         |
         v
  +----------------------------+
  | POS-PROCESSAMENTO          |
  | Score de confianca         |
  | Validacao de consistencia  |
  | Fallback para revisao      |
  +----------------------------+
         |
         v
  [Tipo documental + confianca + ID demanda]
```

### 8.2 Abordagens de Classificacao

| Abordagem | Descricao | Quando Usar |
|-----------|----------|------------|
| **Visual (CNN/ViT)** | Classificacao baseada no layout visual da imagem (logos, disposicao de elementos, formato) | Primeira camada — funciona bem para documentos com layout padronizado (RG, CNH, NF) |
| **Textual (NLP sobre OCR)** | OCR parcial do documento + classificacao baseada em palavras-chave e padroes textuais | Segunda camada — diferencia documentos com layouts similares mas conteudo distinto (tipos de certidao, tipos de contrato) |
| **Layout Analysis** | Analise da estrutura espacial: tabelas, colunas, cabecalhos, blocos de texto, areas de assinatura | Complemento — ajuda a distinguir formularios de textos corridos |
| **Multimodal** | Combinacao das tres abordagens em um modelo unico (ex: LayoutLMv3, Donut) | Ideal — melhor acuracia, mas maior custo computacional |
| **Contextual** | Usar informacao do processo/fila como prior para restringir classes possiveis | Otimizacao — reduz espaco de classes e aumenta acuracia |

### 8.3 Detalhamento por Tipo de Documento

#### 8.3.1 Documentos de Identificacao (RG/CNH/Selfie)

| Aspecto | Detalhamento |
|---------|-------------|
| **Features visuais** | Foto 3x4 (RG/CNH), formato carteira, cores padronizadas, brasao |
| **Features textuais** | "Republica Federativa do Brasil", "Registro Geral", "Carteira Nacional de Habilitacao", orgao expedidor |
| **Desafio principal** | Distinguir RG de CNH; detectar documentos antigos vs. novos modelos |
| **Separacao RG frente/verso** | O classificador deve identificar se e frente ou verso quando recebe separadamente |
| **Selfie** | Ausencia de documento — apenas rosto frontal, sem moldura ou formato padronizado |

#### 8.3.2 Certidoes (Cartoriais e Fiscais)

| Aspecto | Detalhamento |
|---------|-------------|
| **Features visuais** | Selos cartoriais, carimbos, brasoes, formato oficio |
| **Features textuais** | "Matricula", "Certidao", "Registro", "Cartorio", "Tabeliao" |
| **Desafio principal** | Distinguir entre os 5+ tipos de certidao (matricula vs. estado civil vs. onus vs. DAP vs. CAF vs. CCIR vs. ITR vs. CAR) |
| **Certidoes rurais** | Cada uma tem orgao emissor diferente (INCRA, IBAMA, RF) — usar logo como feature |

#### 8.3.3 Contratos

| Aspecto | Detalhamento |
|---------|-------------|
| **Features visuais** | Documentos extensos, clausulas numeradas, paginas de assinatura |
| **Features textuais** | "Contrato", "clausula", "partes", "objeto", "vigencia" |
| **Desafio principal** | Distinguir Contrato Comercial vs. Habitacional vs. Registrado vs. Arrendamento vs. Documento Constitutivo |
| **Contrato CAIXA** | Contratos habitacionais da CAIXA tem formato padronizado — usar template matching |
| **Contrato registrado** | Diferenca: presenca de selos e carimbos cartoriais sobre o contrato |

#### 8.3.4 Documentos Fiscais e Renda

| Aspecto | Detalhamento |
|---------|-------------|
| **Features visuais** | Tabelas numericas, codigos de barras, logos de orgaos/empresas |
| **Features textuais** | Valores monetarios, CNPJ, aliquotas, "rendimentos", "proventos", "descontos" |
| **Desafio principal** | Distinguir Holerite vs. Extrato bancario vs. Comprovante de faturamento vs. IRPF |
| **IRPF** | Logo Receita Federal, CPF, formato muito padronizado — facil de identificar |

---

## 9. SLAs E QUALIDADE

### 9.1 Niveis de Servico por Fila

O servico de classificacao herda os SLAs da fila onde a demanda esta alocada. O tempo de classificacao e apenas uma fracao do SLA total (que cobre todo o pipeline):

| Fila | SLA Total (horas) | Tempo Estimado para Classificacao |
|------|-------------------|----------------------------------|
| Programa Pe de Meia | **1h** | < 5 segundos |
| Abertura Conta Agencia/CCA | **1h** | < 5 segundos |
| Garantias Comerciais PJ | **18h** | < 30 segundos |
| Dossie CCA-Comercial/Consignado | **18h** | < 30 segundos |
| Concessao Comercial PJ | **18h** | < 30 segundos |
| Demais filas | **24h** | < 30 segundos |

> **Nota critica:** Com SLA de 1h para as duas primeiras filas e considerando que a classificacao e apenas uma das 4-5 etapas do pipeline, o tempo disponivel para classificacao e de **poucos segundos**. A classificacao precisa ser automatica e instantanea.

### 9.2 Disponibilidade

| Metrica | Valor |
|---------|-------|
| Disponibilidade minima | **99,5%** |
| Regime de operacao | **24x7x365** |
| Monitoramento | Continuo com alertas automaticos |

### 9.3 Criterios de Qualidade

O servico e considerado **conforme** quando:

- [ ] O tipo documental retornado corresponde ao tipo real do documento
- [ ] A classificacao esta vinculada ao identificador correto da demanda
- [ ] O tempo de resposta esta dentro do SLA da fila
- [ ] Documentos nao reconhecidos sao sinalizados corretamente (nao classificados erroneamente)
- [ ] Novas tipologias adicionadas pela CAIXA sao reconhecidas apos a parametrizacao

### 9.4 Metricas de Acuracia Recomendadas

| Metrica | Meta | Justificativa |
|---------|------|--------------|
| **Acuracia geral (top-1)** | >= 95% | Padrao de mercado para classificacao documental |
| **Acuracia por familia** | >= 93% | Algumas familias (contratos) sao mais dificeis |
| **Acuracia para alta frequencia** (RG, CNH, Selfie, Residencia) | >= 98% | Representam 53% do volume — erros aqui tem alto impacto |
| **Taxa de "nao classificado"** | <= 3% | Documentos que nao se encaixam em nenhum tipo |
| **Taxa de falsos positivos** (tipo errado com alta confianca) | <= 1% | Erros com alta confianca nao sao interceptados e propagam pela cadeia |
| **Latencia P95** | < 2 segundos | Para nao impactar SLA de 1h das filas prioritarias |
| **Latencia P99** | < 5 segundos | Incluindo documentos complexos multipaginas |

### 9.5 Penalidades

| Tipo | Formula | Descricao |
|------|---------|----------|
| Deducao por indisponibilidade (DI) | `DI = VSETF x FAIDS` | Quando o servico fica indisponivel |
| Deducao por servico incorreto (VDSI) | `VDSI = 0,05% x SI x VSETF` | Para cada classificacao incorreta identificada |
| Teto de deducoes | **10% do VSETF** | Limite maximo |

> **Impacto cascata:** Uma classificacao incorreta pode gerar erros em extracao, validacao e regras — gerando multiplas deducoes de VDSI de servicos downstream. A acuracia da classificacao tem **efeito multiplicador** nas penalidades.

---

## 10. RELACAO COM OUTROS SERVICOS

### 10.1 Posicao no Pipeline

```
[Documento digitalizado recebido]
         |
         v
  +-------------------------------+
  | TRATAMENTO DE ARQUIVO DIGITAL |
  | (correcao, rotacao, recorte)  |
  +-------------------------------+
         |
         v
  +-------------------------------+
  | CLASSIFICACAO DOCUMENTAL      |  <-- ESTE SERVICO
  | (identificar tipo do doc)     |
  +-------------------------------+
         |
    +----|----+---------+---------+
    |         |         |         |
    v         v         v         v
 [Extracao] [Autent.] [Regras]  [Recusa]
 de dados   docum.    negociais  (tipo
                                 invalido)
```

### 10.2 Dependencias Upstream

| Servico | Relacao |
|---------|--------|
| **Tratamento de arquivo digital** | Fornece imagem limpa, orientada e recortada — qualidade impacta acuracia |
| **Separacao de mosaico** | Quando o tratamento separa mosaicos, cada sub-imagem e classificada individualmente |

### 10.3 Dependencias Downstream

| Servico | Como Usa a Classificacao |
|---------|------------------------|
| **Extracao de dados** | Seleciona o schema de extracao correto (campos diferentes por tipo de documento) |
| **Validacao de autenticidade** | Seleciona os padroes de validacao corretos (templates de fraude por tipo) |
| **Aplicacao de regras negociais** | Seleciona o checklist de regras correto (regras diferentes por tipo + processo) |
| **Arquivamento** | Organiza o armazenamento por tipo documental |
| **Rejeicao** | Tipo nao correspondente ao esperado na demanda gera rejeicao do documento |
| **Operacao assistida** | Classificacoes com baixa confianca podem ser escaladas para revisao humana |

### 10.4 Importancia Critica

> **A classificacao documental e o ROTEADOR LOGICO de todo o pipeline.** Ela determina qual caminho o documento segue. Um RG classificado como CNH pode gerar extracao de campos errados, validacao com template errado, e regras negociais inaplicaveis. O investimento em acuracia deste servico tem o **maior ROI** de toda a cadeia.

---

## 11. REQUISITOS TECNICOS DE IMPLEMENTACAO

### 11.1 Tecnologias Recomendadas

| Camada | Tecnologia | Finalidade |
|--------|-----------|-----------|
| **Modelo visual** | EfficientNet, ResNet, ViT | Classificacao baseada em layout e aparencia visual |
| **Modelo textual** | BERT, RoBERTa (pt-BR) | Classificacao baseada em texto extraido via OCR parcial |
| **Modelo multimodal** | LayoutLMv3, Donut, DiT | Combina visual + textual + layout em um unico modelo |
| **OCR parcial** | Tesseract, PaddleOCR, Azure Read API | Extrair texto para features textuais (nao extracao completa) |
| **Pre-processamento** | OpenCV, Pillow | Resize, normalize, augmentation |
| **Serving** | ONNX Runtime, TensorRT, Triton | Inferencia otimizada para latencia < 2s |
| **Treinamento** | PyTorch, HuggingFace Transformers | Fine-tuning em dataset de documentos brasileiros |

### 11.2 Estrategia de Modelo

| Estrategia | Descricao | Vantagem | Desvantagem |
|-----------|----------|----------|-------------|
| **Modelo unico (32 classes)** | Um modelo classifica todos os 32 tipos | Simples de manter | Dificuldade com classes ambiguas |
| **Hierarquico (2 niveis)** | Nivel 1: Familia (12 classes) → Nivel 2: Tipo especifico dentro da familia | Melhor acuracia em subtipos | Mais complexo, latencia maior |
| **Ensemble (visual + textual)** | Modelo visual + modelo textual votam juntos | Robusto a variacao | Custo computacional dobrado |
| **Contextual** | Modelo base + prior do processo para restringir classes | Acuracia maxima por processo | Requer integracao com metadata da demanda |

**Recomendacao:** Modelo hierarquico com contexto do processo.
- Nivel 1: Classificar na familia (12 opcoes) — modelo visual
- Nivel 2: Classificar no tipo especifico — modelo textual (OCR parcial + NLP)
- Contexto: Filtrar classes possiveis com base no processo/dossie

### 11.3 Padroes Tecnologicos Obrigatorios (Anexo I-B)

| Item | Especificacao |
|------|--------------|
| Integracao | Web Services SOAP e REST |
| Formatos de dados | JSON, XML |
| Protocolo | HTTPS (TLS 1.3) |
| API | Segura e documentada |
| Idioma | Portugues do Brasil |

### 11.4 Requisitos de Infraestrutura

| Requisito | Especificacao |
|-----------|--------------|
| Ambiente | Homologacao + Producao segregados |
| GPU | Necessaria para inferencia de modelos deep learning |
| Disponibilidade | 99,5% — 24x7x365 |
| Auto-scaling | Absorver picos sem degradacao |
| Logs | document_id, tipo_classificado, confianca, latencia, modelo_versao |
| Trilha de auditoria | Cada classificacao rastreavel |
| Cache | Cache de modelos em memoria para latencia minima |

---

## 12. GESTAO DA TIPOLOGIA

### 12.1 Ciclo de Vida de um Tipo Documental

```
[CAIXA define novo tipo]
         |
         v
[Comunicacao a CONTRATADA]
         |
         v
[Coleta de amostras do novo tipo]
         |
         v
[Treinamento/fine-tuning do modelo]
         |
         v
[Validacao em ambiente de homologacao]
         |
         v
[Deploy em producao]
         |
         v
[Monitoramento de acuracia]
```

### 12.2 Requisitos de Adaptabilidade

| Cenario | Requisito |
|---------|----------|
| **Novo tipo adicionado** | Modelo deve ser retreinado/atualizado sem indisponibilidade do servico |
| **Tipo removido** | Classificador deve parar de retornar o tipo removido |
| **Tipo renomeado** | Atualizar labels sem retreinar modelo |
| **Subtipo criado** | Ex: "Certidao" se divide em "Certidao Positiva" e "Certidao Negativa" — requer novo treinamento |
| **Novo formato de documento** | Ex: novo modelo de CNH digital — requer amostras e retreinamento |

### 12.3 Monitoramento Continuo

| Metrica | Frequencia | Acao se Degradar |
|---------|-----------|-----------------|
| Acuracia por tipo | Semanal | Investigar e retreinar |
| Taxa de "nao classificado" | Diaria | Verificar se ha novos tipos nao mapeados |
| Distribuicao de classes | Semanal | Detectar drift na composicao de documentos |
| Confianca media | Diaria | Queda indica degradacao do modelo |
| Latencia P95 | Continuo | Otimizar ou escalar infra |

---

## 13. CENARIOS DE TESTE E VALIDACAO

### 13.1 Cenarios Minimos para Homologacao

| # | Cenario | Entrada | Resultado Esperado |
|---|---------|---------|-------------------|
| 1 | RG frente | Imagem RG modelo novo | Tipo: "Identificacao — RG" |
| 2 | CNH digital | Imagem CNH novo modelo | Tipo: "Identificacao — CNH" |
| 3 | Selfie | Foto frontal sem documento | Tipo: "Selfie" |
| 4 | Holerite | Comprovante de rendimentos | Tipo: "Renda — Holerite" |
| 5 | IRPF | Declaracao completa PDF | Tipo: "IRPF" |
| 6 | Matricula imovel simples | Certidao 2 paginas | Tipo: "Certidao Matricula Imovel" |
| 7 | Matricula imovel longa | Certidao 20 paginas | Tipo: "Certidao Matricula Imovel" |
| 8 | Contrato social | Documento constitutivo PJ | Tipo: "Documento Constitutivo" |
| 9 | Contrato habitacional | Contrato padrao CAIXA | Tipo: "Contrato Habitacional" |
| 10 | Conta de luz | Comprovante endereco | Tipo: "Residencia" |
| 11 | Nota fiscal | NF de produto | Tipo: "Nota Fiscal" |
| 12 | Documento desconhecido | Documento fora da tipologia | Tipo: "Nao classificado" + motivo |
| 13 | Documento ilegivel | Scan muito degradado | Tipo: "Nao classificado" + motivo |
| 14 | Mosaico separado | Sub-imagem de mosaico | Classificacao correta da sub-imagem |
| 15 | Contexto abertura conta | RG com contexto processo | Tipo: "Identificacao — RG" (confianca elevada pelo contexto) |
| 16 | Certidao DAP | Certidao rural especifica | Tipo: "Certidao DAP" (e nao generico "Certidao") |
| 17 | Laudo avaliacao | PDF 30 paginas com fotos | Tipo: "Laudo de Avaliacao do Imovel" |
| 18 | Parecer juridico | Documento com analise legal | Tipo: "Parecer Juridico" (e nao "Contrato") |
| 19 | Volume de pico | 1000 classificacoes simultaneas | Processamento sem degradacao |
| 20 | Novo tipo adicionado | Documento de tipo recentemente incluido | Classificacao correta apos parametrizacao |

### 13.2 Dataset de Treinamento e Validacao

| Requisito | Especificacao |
|-----------|--------------|
| Amostras por tipo (minimo) | 200+ para tipos frequentes, 50+ para tipos raros |
| Diversidade de emissores | Multiplos cartorios, empresas, orgaos para o mesmo tipo |
| Variacao de qualidade | Alta, media e baixa qualidade de scan |
| Formatos | PDF, TIFF, PNG, JPEG |
| Balanceamento | Refletir distribuicao real de volume por tipo |
| Dataset de validacao | 20% holdout, estratificado por tipo |
| Dataset de teste | Amostras nunca vistas no treinamento |

---

## 14. PRECIFICACAO

### 14.1 Estrutura de Preco

| Item | Valor |
|------|-------|
| **Nome do servico na proposta** | Classificacao documental |
| **Quantidade anual** | 19.659.587 |
| **Unidade de cobranca** | Por documento classificado |

### 14.2 Componentes de Custo

| Componente | Descricao |
|-----------|----------|
| GPU para inferencia | NVIDIA T4/A10 para modelos deep learning em producao |
| Armazenamento de modelos | Multiplas versoes de modelo para rollback |
| OCR parcial | Custo de OCR para features textuais (se usar API externa) |
| Treinamento/retreinamento | GPU para fine-tuning periodico |
| Anotacao de dados | Custo de anotar amostras para novos tipos |
| Monitoramento | Ferramentas de observabilidade de ML (MLflow, Weights & Biases) |
| Mao de obra ML | Data scientists e ML engineers para manter modelos |
| Infraestrutura | Redundancia para 99,5% de disponibilidade |

### 14.3 Alerta de Precificacao

> O volume de 19,6M classificacoes/ano exige **processamento em escala**. O custo unitario deve refletir inferencia batch (nao one-by-one). Modelos otimizados com ONNX/TensorRT reduzem custo de GPU significativamente. Considerar que ~53% do volume sao 3 tipos faceis (RG/CNH, Selfie, Residencia) — um modelo leve pode resolver a maioria dos casos, reservando modelos pesados para os 47% restantes.

---

## 15. RISCOS ESPECIFICOS DO SERVICO

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| 1 | **Acuracia insuficiente entre subtipos de contrato** | Alta | Extracao e regras erradas | Modelo hierarquico + features textuais para distinguir subtipos |
| 2 | **Novos modelos de documento (ex: CNH digital)** | Media | Classificacao errada de documentos validos | Monitoramento de drift + pipeline de retreinamento agil |
| 3 | **CAIXA adiciona tipos com frequencia** | Media | Necessidade de retreinamento constante | Few-shot learning ou model-in-the-loop com anotadores |
| 4 | **Erro de classificacao em cascata** | Alta | Penalidades multiplicadas em servicos downstream | Threshold de confianca + fallback humano |
| 5 | **Documentos de baixa qualidade** | Alta | Modelo nao consegue classificar | Denoising pre-classificacao + flag de qualidade insuficiente |
| 6 | **Variacao entre emissores** | Alta | RG de SP diferente de RG de MG, certidoes de cartorios diferentes | Dataset diversificado regionalmente |
| 7 | **Confusao Selfie vs. Foto do RG** | Media | Selfie classificada como RG ou vice-versa | Feature especifica: presenca de moldura de documento |
| 8 | **Latencia em documentos multipaginas** | Media | SLA de 1h comprometido | Classificar pela primeira pagina + confirmacao com paginas adicionais |

---

## 16. CHECKLIST DE IMPLEMENTACAO

### Fase 1 — MVP (Tipos de Alta Frequencia)

- [ ] Classificador para os 10 tipos mais frequentes (~87% do volume): RG, CNH, Selfie, Residencia, Holerite, Extrato, Certidao Estado Civil, Certidao Matricula, IRPF, IPTU
- [ ] Modelo visual basico (EfficientNet ou ResNet fine-tuned)
- [ ] API REST com entrada de imagem e retorno de tipo + confianca + ID demanda
- [ ] Fallback "nao classificado" para tipos nao reconhecidos
- [ ] Logs estruturados
- [ ] Latencia < 2s P95

### Fase 2 — Completo (Todos os 32 Tipos)

- [ ] Expansao para todos os 32 tipos documentais
- [ ] Modelo hierarquico (familia → tipo)
- [ ] Features textuais via OCR parcial para desambiguacao
- [ ] Classificacao contextual (usar processo/fila como prior)
- [ ] Tratamento de documentos multipaginas
- [ ] Tratamento de sub-imagens de mosaico
- [ ] Dashboard de monitoramento de acuracia por tipo
- [ ] Mecanismo de threshold com escalacao para revisao humana

### Fase 3 — Maturidade

- [ ] Modelo multimodal (LayoutLMv3 ou similar)
- [ ] Pipeline de retreinamento automatizado (amostras novas → fine-tune → deploy)
- [ ] Few-shot learning para novos tipos com poucas amostras
- [ ] A/B testing de modelos em producao
- [ ] Feedback loop: correcoes humanas retroalimentam treinamento
- [ ] Auto-scaling baseado em fila (GPU sob demanda)

---

## 17. REFERENCIAS NORMATIVAS

| Documento | Secao | Conteudo Relevante |
|-----------|-------|-------------------|
| Anexo I — TR | 2.5 | Definicao do servico de classificacao documental |
| Anexo I — TR | 2.5.1 | Operacoes: classificar + retornar tipologia |
| Anexo I — TR | 2.8.2 | Tratamento de mosaico com classificacao |
| Anexo I — TR | 2.10.2 | Automacao inteligente com IA para classificacao |
| Anexo I — TR | 5.2 | Formula de remuneracao |
| Anexo I — TR | 5.4.3 | Inconsistencias documentais |
| Anexo I — TR | 5.5 | Deducoes por servico incorreto |
| Anexo I-A | Definicoes | Classificacao documental, area util, mosaico, extensao |
| Anexo I-B | Padrao Tecnologico | Formatos, protocolos, integracoes |
| Anexo I-C | Secao 2 | 32 tipos documentais com descricao e paginas |
| Anexo I-C | Secao 3 | Composicao de dossies por processo |
| Anexo I-C | Secao 5 | Volume: 19.659.587 classificacoes/ano |
| Anexo I-H | Filas | SLAs por fila (1h, 18h, 24h) |
