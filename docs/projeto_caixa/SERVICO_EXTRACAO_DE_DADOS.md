# Servico de Extracao de Dados
## Especificacao Completa — Edital BPO CAIXA

**Referencia:** Termo de Referencia, Secao 2.3.2 | Anexo I-A (Definicoes) | Anexo I-C (Volumetria) | Anexo I-H (Filas)
**Ultima atualizacao:** 2026-04-10

---

## 1. DEFINICAO FORMAL

> **Atributo extraido** — Informacao textual presente em documento, com indicacao da presenca ou ausencia de algum elemento solicitado ou recorte de uma area especifica do documento.
>
> — Anexo I-A, Definicoes de Termos

O servico de extracao de atributos dos documentos e dados consiste em **identificar, localizar e capturar informacoes textuais e visuais** de documentos digitalizados, conforme a tipologia de cada documento e respeitando janelas temporais definidas para cada demanda.

**Objetivo central:** Transformar documentos nao-estruturados (PDFs, imagens de scans) em dados estruturados (campos com nome, valor, confianca e localizacao), prontos para alimentar os servicos de validacao, regras negociais e decisao.

---

## 2. ESCOPO DETALHADO DO SERVICO

### 2.1 Operacoes Obrigatorias (TR 2.3.2.1)

| # | Operacao | Descricao Detalhada |
|---|----------|-------------------|
| 1 | **Extrair atributos conforme tipologia** | Extrair atributos conforme a tipologia do documento, respeitando a janela temporal definida para cada demanda |
| 2 | **Indicar inexistencia de atributos** | Indicar a inexistencia de atributos previamente definidos quando nao presentes no documento analisado |
| 3 | **Verificar presenca/ausencia de elementos** | Verificar a presenca ou ausencia de elementos especificos no documento, conforme tipologia definida |
| 4 | **Capturar areas especificas** | Capturar areas especificas da imagem do documento, conforme tipologia estabelecida |
| 5 | **Retornar atributos vinculados ao ID** | Retornar a CAIXA os atributos extraidos, vinculados ao identificador da demanda |

### 2.2 Definicoes Ampliadas de "Atributo de Extracao"

O TR amplia o conceito de atributo extraido para incluir dois tipos distintos:

| Tipo de Atributo | Descricao | Exemplo |
|-----------------|----------|---------|
| **Presenca/ausencia de elemento** | Verificacao booleana de se um elemento especifico existe ou nao no documento | Campo de assinatura preenchido? Foto 3x4 presente? Carimbo do cartorio existe? |
| **Captura de area especifica** | Recorte de uma regiao da imagem do documento | Foto do titular no RG, area de assinatura em contrato, quadro societario em contrato social |

### 2.3 Regra Critica de Remuneracao (TR 2.3.2.2 e 2.3.2.3)

> **ALERTA FINANCEIRO:** O servico de extracao de dados so e remunerado quando a CAIXA demanda **expressamente** o recebimento dos dados extraidos como **produto final** do servico, em formato, estrutura e modelo por ela definidos.

> Quando a extracao e executada exclusivamente como **etapa preparatoria** para outros servicos (classificacao documental, aplicacao de regras negociais, validacoes, analises, conferencias), **NAO sera devida remuneracao especifica** pela extracao — ela esta compreendida no escopo do servico principal demandado.

**Implicacao direta para precificacao:**
- A extracao remunerada e apenas aquela solicitada como output autonomo
- A extracao interna (para alimentar regras e validacoes) e **custo operacional** da contratada, absorvido nos demais servicos
- Precificar os demais servicos (regras, validacao) ja embutindo o custo da extracao necessaria

---

## 3. TIPOS DE ATRIBUTOS POR DOCUMENTO

### 3.1 Catalogo de Campos por Tipo Documental

#### 3.1.1 Identificacao — RG

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Nome completo | Texto | Baixa | OCR direto |
| Numero RG | Texto numerico | Baixa | OCR direto |
| Data de nascimento | Data | Baixa | OCR + parsing de data |
| Filiacao (pai) | Texto | Media | Pode estar ausente em RGs antigos |
| Filiacao (mae) | Texto | Media | OCR direto |
| Naturalidade | Texto | Media | Cidade + UF |
| Orgao expedidor | Texto | Baixa | Sigla padronizada |
| Data de expedicao | Data | Baixa | OCR + parsing de data |
| CPF | Texto numerico | Baixa | Pode estar no verso |
| Foto 3x4 | Imagem (recorte) | Media | Captura de area especifica |
| Assinatura | Imagem (recorte) | Media | Captura de area especifica |
| Impressao digital | Presenca/ausencia | Baixa | Verificacao booleana |

#### 3.1.2 Identificacao — CNH

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Nome | Texto | Baixa | OCR direto |
| Numero registro | Texto numerico | Baixa | OCR direto |
| CPF | Texto numerico | Baixa | OCR direto |
| Data nascimento | Data | Baixa | OCR + parsing |
| Categorias | Texto | Baixa | A, B, AB, C, D, E |
| Validade | Data | Baixa | OCR + parsing |
| Primeira habilitacao | Data | Baixa | OCR + parsing |
| Filiacao | Texto | Media | OCR direto |
| Foto | Imagem (recorte) | Media | Captura de area |
| Local | Texto | Media | Cidade/UF |
| Observacoes | Texto | Alta | Pode conter restricoes medicas |

#### 3.1.3 Certidao de Matricula de Imovel

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Numero da matricula | Texto numerico | Baixa | Cabecalho do documento |
| Cartorio de registro | Texto | Baixa | Identificacao do cartorio |
| Comarca | Texto | Baixa | Cidade/UF |
| Descricao do imovel | Texto longo | Alta | Pode ocupar paragrafos inteiros, linguagem tecnica |
| Endereco do imovel | Texto | Media | Pode estar fragmentado na descricao |
| Area total | Numerico + unidade | Media | m2 ou hectares, pode ter formatos variados |
| Proprietario(s) atual(is) | Texto | Alta | Pode haver cadeia de proprietarios |
| CPF/CNPJ proprietario(s) | Texto numerico | Media | Vinculado ao proprietario |
| Onus e gravames | Texto longo | Muito alta | Hipotecas, penhoras, indisponibilidades — critico para regras compostas |
| Averbacoes | Texto longo | Muito alta | Historico de alteracoes |
| Data do registro | Data | Baixa | OCR + parsing |
| Valor venal/transacao | Numerico | Alta | Pode estar em diferentes registros |

#### 3.1.4 Documento Constitutivo (Contrato Social)

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Razao social | Texto | Media | OCR direto |
| CNPJ | Texto numerico | Baixa | Formato padronizado |
| Endereco sede | Texto | Media | Pode estar em clausula especifica |
| Objeto social | Texto longo | Alta | Descricao das atividades |
| Capital social | Numerico | Media | Valor + moeda |
| Quadro societario | Tabela/lista | Muito alta | Nomes, CPFs, % de participacao, cargos |
| Poderes de administracao | Texto longo | Muito alta | Quem pode assinar, limites de valor, representacao |
| Data de constituicao | Data | Baixa | OCR + parsing |
| Numero NIRE/Junta | Texto numerico | Media | Registro na Junta Comercial |
| Clausulas de decisao | Texto longo | Muito alta | Quorum, deliberacoes, assembleia |

#### 3.1.5 Holerite / Comprovante de Renda

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Nome do empregado | Texto | Baixa | OCR direto |
| CPF | Texto numerico | Baixa | OCR direto |
| Empregador (razao social) | Texto | Baixa | Cabecalho |
| CNPJ empregador | Texto numerico | Baixa | Cabecalho |
| Competencia (mes/ano) | Data | Baixa | OCR + parsing |
| Salario bruto | Numerico | Media | Valor com separadores |
| Total proventos | Numerico | Media | Soma dos creditos |
| Total descontos | Numerico | Media | INSS, IRRF, outros |
| Salario liquido | Numerico | Media | Proventos - Descontos |
| Cargo/funcao | Texto | Media | Pode estar ausente |
| Data de admissao | Data | Media | Nem sempre presente |

#### 3.1.6 IRPF (Declaracao de Imposto de Renda)

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Nome do declarante | Texto | Baixa | OCR direto |
| CPF | Texto numerico | Baixa | OCR direto |
| Ano-exercicio | Numerico | Baixa | Ex: 2024 |
| Ano-calendario | Numerico | Baixa | Ex: 2023 |
| Total rendimentos tributaveis | Numerico | Media | Valor com separadores |
| Total rendimentos isentos | Numerico | Media | Valor com separadores |
| Imposto devido | Numerico | Media | Calculado |
| Imposto pago/retido | Numerico | Media | Valor com separadores |
| Resultado (restituir/pagar) | Numerico | Media | Pode ser negativo |
| Bens e direitos | Tabela | Muito alta | Lista de bens com valores |
| Dividas e onus | Tabela | Alta | Lista de dividas |
| Dependentes | Lista | Media | Nomes e CPFs |
| Numero do recibo | Texto numerico | Baixa | Comprovante de entrega |

#### 3.1.7 Comprovante de Residencia (Conta de Consumo)

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Nome do titular | Texto | Baixa | OCR direto |
| Endereco completo | Texto | Media | Logradouro, numero, complemento, bairro, cidade, UF, CEP |
| CEP | Texto numerico | Baixa | 8 digitos |
| Tipo de servico | Texto | Baixa | Energia, agua, gas, telefone |
| Concessionaria | Texto | Baixa | Logo + nome |
| Mes de referencia | Data | Baixa | OCR + parsing |
| Valor | Numerico | Baixa | Valor da conta |
| Codigo de barras | Texto numerico | Baixa | OCR de barcode |

#### 3.1.8 Apolice de Seguro

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Numero da apolice | Texto numerico | Baixa | OCR direto |
| Seguradora | Texto | Baixa | Nome + CNPJ |
| Segurado | Texto | Baixa | Nome + CPF/CNPJ |
| Beneficiario | Texto | Media | Pode ser CAIXA |
| Vigencia (inicio/fim) | Data | Baixa | Duas datas |
| Objeto segurado | Texto | Media | Descricao do bem |
| Valor segurado | Numerico | Media | Importancia segurada |
| Premio | Numerico | Media | Valor pago |
| Coberturas | Tabela/lista | Alta | Tipos e valores por cobertura |
| Clausula beneficiaria CAIXA | Presenca/ausencia | Alta | Critico para garantia |

#### 3.1.9 Laudo de Avaliacao de Imovel

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Engenheiro responsavel | Texto | Baixa | Nome + CREA |
| Numero ART/RRT | Texto numerico | Media | Registro profissional |
| Endereco do imovel | Texto | Media | Completo |
| Tipo do imovel | Texto | Baixa | Casa, apartamento, terreno |
| Area construida | Numerico + unidade | Media | m2 |
| Area do terreno | Numerico + unidade | Media | m2 |
| Valor de avaliacao | Numerico | Media | Valor de mercado |
| Valor de liquidacao | Numerico | Media | Valor forcada |
| Estado de conservacao | Texto | Media | Classificacao |
| Idade do imovel | Numerico | Media | Anos |
| Memorial fotografico | Imagens (recortes) | Alta | Fotos internas e externas |
| Coordenadas | Texto | Media | Lat/Long quando presente |

#### 3.1.10 Nota Fiscal

| Campo | Tipo | Complexidade | Observacao |
|-------|------|-------------|-----------|
| Numero NF | Texto numerico | Baixa | OCR direto |
| Serie | Texto | Baixa | OCR direto |
| Data emissao | Data | Baixa | OCR + parsing |
| Emitente (razao social) | Texto | Baixa | Cabecalho |
| CNPJ emitente | Texto numerico | Baixa | Formato padronizado |
| Destinatario | Texto | Baixa | Nome + CPF/CNPJ |
| Descricao itens | Tabela | Media | Lista de produtos/servicos |
| Valor total | Numerico | Baixa | Valor final |
| Impostos | Tabela | Media | ICMS, IPI, ISS, PIS, COFINS |
| Chave de acesso NFe | Texto numerico | Baixa | 44 digitos |

### 3.2 Tipos de Dados Extraidos — Consolidado

| Tipo de Dado | Exemplos | Tecnica Principal |
|-------------|----------|------------------|
| **Texto curto** | Nome, CPF, numero RG, CNPJ | OCR direto + regex |
| **Texto longo** | Descricao de imovel, clausulas, objeto social | OCR + NLP/LLM |
| **Numerico** | Valores monetarios, areas, percentuais | OCR + parsing numerico |
| **Data** | Nascimento, expedicao, validade, competencia | OCR + date parsing (multiplos formatos) |
| **Tabela** | Quadro societario, coberturas seguro, bens IRPF | Table extraction (IA) |
| **Booleano (presenca/ausencia)** | Assinatura preenchida? Carimbo existe? | Deteccao de objeto/regiao |
| **Imagem (recorte)** | Foto 3x4, area assinatura, carimbo | Crop de regiao especifica |

---

## 4. VOLUMETRIA

### 4.1 Volume Anual Estimado

| Metrica | Valor |
|---------|-------|
| **Extracao de atributos dos documentos** | **19.659.587 / ano** |
| Media mensal | ~1.638.299 / mes |
| Media diaria (dias uteis ~250) | ~78.638 / dia |
| Media diaria (24x7 = 365 dias) | ~53.862 / dia |
| Media horaria (pico 08h-20h) | ~6.553 / hora |

### 4.2 Volume Real vs. Remunerado

| Categoria | Estimativa | Observacao |
|-----------|-----------|-----------|
| Extracoes remuneradas (produto final) | 19.659.587/ano | Volume da proposta comercial |
| Extracoes nao remuneradas (etapa preparatoria) | Potencialmente maior | Toda regra simples (96M) e composta (1,7M) exige extracao previa nao remunerada |
| Volume REAL de extracoes na plataforma | **Muito superior a 19,6M** | A plataforma executara muito mais extracoes do que sera paga |

> **Alerta critico de produto:** A plataforma precisa ser dimensionada para o volume REAL de extracoes (incluindo as preparatorias), nao apenas as 19,6M remuneradas. O custo computacional de OCR/IA e proporcional ao volume real, nao ao volume faturado.

### 4.3 Estimativa de Campos por Tipo Documental

| Tipo Documental | Campos Medios por Doc | Volume Docs Estimado | Total Campos/Ano |
|----------------|----------------------|---------------------|-----------------|
| Identificacao (RG/CNH) | 10–12 | ~5.500.000 | ~60.000.000 |
| Selfie | 0 (biometria, nao extracao) | ~3.000.000 | — |
| Residencia | 6–8 | ~2.000.000 | ~14.000.000 |
| Renda (holerite/extrato) | 10–15 | ~1.800.000 | ~22.000.000 |
| Certidao Estado Civil | 5–8 | ~1.500.000 | ~10.000.000 |
| Certidao Matricula Imovel | 10–20 | ~1.200.000 | ~18.000.000 |
| IRPF | 15–30 | ~800.000 | ~18.000.000 |
| Contrato Habitacional | 15–25 | ~700.000 | ~14.000.000 |
| Documento Constitutivo | 10–20 | ~600.000 | ~9.000.000 |
| Demais tipos | 5–15 | ~2.559.587 | ~25.000.000 |
| **TOTAL ESTIMADO** | — | **~19.659.587** | **~190.000.000 campos/ano** |

> Aproximadamente **190 milhoes de campos individuais** extraidos por ano, com media de ~10 campos por documento.

---

## 5. REGRAS DE NEGOCIO

### 5.1 Janela Temporal

- Cada demanda tem uma **janela temporal** definida (prazo em minutos somados ao horario de comunicacao)
- A extracao deve respeitar essa janela — atrasos impactam o SLA da fila
- A janela temporal e um **parametro de execucao** enviado na solicitacao

### 5.2 Formato de Retorno

- Os atributos extraidos devem ser retornados em **formato, estrutura e modelo definidos pela CAIXA** (TR 2.3.2.2)
- O formato e definido previamente pela CONTRATANTE
- Os dados devem permitir a execucao das operacoes pertinentes nos sistemas internos da CAIXA (TR 1.1.5)

### 5.3 Indicacao de Ausencia

- Quando um atributo **previamente definido** nao esta presente no documento, o servico deve **indicar explicitamente** sua ausencia (TR 2.3.2.1)
- NAO e aceitavel retornar campo vazio sem sinalizacao — a ausencia deve ser declarada
- A diferenca entre "campo nao encontrado" e "campo vazio" deve ser explicita

### 5.4 Remuneracao — Regra Dual

| Cenario | Remunerado? | Referencia |
|---------|-----------|-----------|
| CAIXA solicita extracao como produto final | **SIM** — valor unitario da proposta | TR 2.3.2.2 |
| Extracao como etapa para classificacao | **NAO** — absorvido no servico de classificacao | TR 2.3.2.3 |
| Extracao como etapa para regras negociais | **NAO** — absorvido no servico de regras | TR 2.3.2.3 |
| Extracao como etapa para validacao de autenticidade | **NAO** — absorvido no servico de validacao | TR 2.3.2.3 |
| Extracao como etapa para analises ou conferencias | **NAO** — absorvido no servico correlato | TR 2.3.2.3 |

### 5.5 Vinculacao ao Identificador

- Todo resultado de extracao deve estar **vinculado ao identificador da demanda**
- O ID permite rastrear: qual documento, de qual dossie, em qual fila, quais campos foram extraidos, com qual confianca

### 5.6 Dados Exclusivos para Servicos Contratados

- Os dados extraidos **devem ser utilizados exclusivamente para execucao dos servicos contratados** (TR 7.3.5)
- **Vedada** sua utilizacao para qualquer outro fim sem autorizacao expressa da CAIXA

---

## 6. RELACAO COM OUTROS SERVICOS

### 6.1 Posicao no Pipeline

```
[Documento tratado e classificado]
         |
         v
  +-------------------------------+
  | EXTRACAO DE DADOS             |  <-- ESTE SERVICO
  | (OCR + IA + NLP)              |
  +-------------------------------+
         |
    +----|----+---------+---------+---------+
    |         |         |         |         |
    v         v         v         v         v
 [Produto  [Valida-  [Regras   [Regras   [Opera-
  Final]    cao de    Simples]  Compos-   cao
            autent.]            tas]      Assist.]
```

### 6.2 Dependencias Upstream

| Servico | Relacao |
|---------|--------|
| **Tratamento de arquivo digital** | Imagem limpa e orientada — qualidade impacta diretamente a acuracia do OCR |
| **Classificacao documental** | Define QUAL tipo de documento e, determinando QUAIS campos extrair |

### 6.3 Dependencias Downstream

| Servico | Como Usa os Dados Extraidos |
|---------|---------------------------|
| **Validacao de autenticidade** | Compara dados extraidos com bases internas/externas para detectar fraude |
| **Regras simples** (96M/ano) | Valida um campo isolado (ex: idade >= 18, data em 90 dias) — **exige extracao previa** |
| **Regras compostas** (1,7M/ano) | Cruza multiplos campos (ex: margem consignavel, onus em matricula) — **exige extracao previa** |
| **Operacao assistida** | Apresenta dados extraidos ao operador para revisao |
| **Consulta em bases externas** | Usa dados extraidos (CPF, CNPJ) como chave de busca |
| **Arquivamento** | Dados extraidos sao metadados do documento arquivado |

### 6.4 Volume de Extracoes Preparatorias (Nao Remuneradas)

| Servico Downstream | Volume Anual | Extracoes Necessarias |
|-------------------|-------------|----------------------|
| Validacao de regras simples | 96.151.084 | Cada validacao exige pelo menos 1 campo extraido |
| Validacao de regras compostas | 1.690.623 | Cada validacao exige 2+ campos extraidos |
| Avaliacao de autenticidade | 14.418.118 | Exige campos para cruzamento |
| Avaliacao de demandas | 2.412.466 | Exige campos para avaliar |

> **A extracao e o SERVICO MAIS EXECUTADO da plataforma**, mas grande parte nao e remunerada diretamente. E o motor silencioso que alimenta toda a cadeia.

---

## 7. DEFINICOES TECNICAS RELACIONADAS

### 7.1 Atributo Extraido (Anexo I-A)
Informacao textual presente em documento, com indicacao da presenca ou ausencia de algum elemento solicitado ou recorte de uma area especifica do documento.

### 7.2 OCR — Optical Character Recognition (Anexo I-A)
Tecnologia para reconhecer caracteres a partir de um arquivo de imagem ou mapa de bits, sejam eles digitalizados, escritos a mao, datilografados ou impressos. Por meio do OCR e possivel obter um arquivo de texto editavel.

### 7.3 ICR — Intelligent Character Recognition (Anexo I-A)
Sistema avancado de reconhecimento de manuscrito que permite que fontes e estilos diferentes de escritas a mao sejam aprendidos pelo computador durante o processamento, para melhorar os niveis de precisao e reconhecimento.

### 7.4 Janela Temporal (Anexo I-A)
Prazo definido para execucao do servico e recepcao de dados, baseado em minutos somados ao horario de comunicacao para envio da solicitacao.

### 7.5 Parametros de Execucao (Anexo I-A)
Parametros necessarios a execucao do servico, encaminhados na solicitacao realizada para o webservice disponibilizado. Exemplo: a indicacao da janela temporal esperada para retorno das informacoes de extracao de dados.

### 7.6 Area Util do Documento (Anexo I-A)
Area da imagem representativa do documento a ser manipulado, contendo os dados para extracao, limitado pelas bordas limites e/ou caracteristicas especificas de cada tipo de documento.

### 7.7 Itens de Precisao (Anexo I-A)
Definicao dos itens obrigatorios em cada servico/demanda. Para extracao, os itens de precisao definem quais campos DEVEM ser extraidos com sucesso.

---

## 8. OPERACOES TECNICAS DETALHADAS

### 8.1 Pipeline de Extracao

```
[Documento classificado + tipo documental]
         |
         v
  +-------------------------------------------+
  | 1. SELECAO DO SCHEMA DE EXTRACAO          |
  |    (quais campos extrair para esse tipo)  |
  +-------------------------------------------+
         |
         v
  +-------------------------------------------+
  | 2. OCR / ICR COMPLETO                     |
  |    Texto corrido + posicoes (bounding box)|
  +-------------------------------------------+
         |
         v
  +-------------------------------------------+
  | 3. EXTRACAO ESTRUTURADA                   |
  |    Campos especificos do texto OCR        |
  |    - Regex para campos padronizados       |
  |    - NLP/LLM para campos semanticos       |
  |    - Table extraction para tabelas        |
  |    - Object detection para recortes       |
  +-------------------------------------------+
         |
         v
  +-------------------------------------------+
  | 4. VALIDACAO E NORMALIZACAO               |
  |    - Formato de CPF/CNPJ/datas            |
  |    - Score de confianca por campo         |
  |    - Indicacao de campos ausentes         |
  +-------------------------------------------+
         |
         v
  +-------------------------------------------+
  | 5. RETORNO ESTRUTURADO                    |
  |    JSON com campos + valores + confianca   |
  |    + bounding boxes + ID demanda          |
  +-------------------------------------------+
```

### 8.2 Tecnicas de Extracao por Complexidade

| Tecnica | Complexidade | Quando Usar | Exemplos |
|---------|-------------|------------|---------|
| **OCR + Regex** | Baixa | Campos com formato fixo e posicao previsivel | CPF, CNPJ, datas, numeros de documento |
| **OCR + Template Matching** | Baixa-Media | Documentos padronizados com layout fixo | RG, CNH, IRPF (Receita Federal), NF-e |
| **OCR + NLP (Named Entity Recognition)** | Media | Campos textuais em posicoes variaveis | Nomes, enderecos, razao social |
| **Table Extraction** | Media-Alta | Tabelas de dados com linhas e colunas | Quadro societario, coberturas seguro, itens NF |
| **Document Understanding (LayoutLM/Donut)** | Alta | Documentos semi-estruturados com layout variavel | Contratos, certidoes, laudos |
| **LLM (Large Language Model)** | Muito alta | Campos semanticos em texto corrido | Onus em matricula, poderes em contrato social, clausulas |
| **Object Detection / Segmentation** | Media | Captura de areas especificas da imagem | Foto 3x4, assinatura, carimbo, selo |

### 8.3 Detalhamento por Familia Documental

#### 8.3.1 Documentos de Identificacao (RG/CNH) — OCR + Template

| Aspecto | Detalhamento |
|---------|-------------|
| **Abordagem** | Template matching — layout e muito padronizado |
| **OCR** | Texto completo + bounding boxes por palavra |
| **Mapeamento** | Zonas pre-definidas no template: zona do nome, zona CPF, zona foto |
| **Desafio** | Multiplos modelos de RG (antigo vs. novo) e CNH (papel vs. digital) |
| **Recortes** | Foto 3x4, area de assinatura, impressao digital |
| **Validacao** | CPF valido (digito verificador), data no formato correto |

#### 8.3.2 Certidao de Matricula — OCR + LLM

| Aspecto | Detalhamento |
|---------|-------------|
| **Abordagem** | OCR completo + LLM para interpretacao semantica do texto |
| **Desafio principal** | Texto juridico corrido, sem tabelas, informacoes encadeadas em registros sequenciais |
| **Onus e gravames** | Requer compreensao semantica para identificar hipotecas, penhoras, indisponibilidades |
| **Cadeia dominial** | Sequencia de proprietarios com datas — LLM para parsing |
| **Variacao** | Cada cartorio tem formato ligeiramente diferente |
| **Campos criticos** | Onus ativos, proprietario atual, area, matricula — erros aqui geram impacto financeiro |

#### 8.3.3 Holerite — OCR + Table Extraction

| Aspecto | Detalhamento |
|---------|-------------|
| **Abordagem** | OCR + deteccao de tabela + mapeamento de colunas |
| **Estrutura** | Cabecalho (dados empresa/empregado) + tabela (proventos/descontos) + rodape (totais) |
| **Desafio** | Cada empresa tem layout proprio de holerite |
| **Campos numericos** | Valores com virgula, ponto, R$ — normalizacao necessaria |
| **Validacao** | Total proventos - Total descontos = Salario liquido |

#### 8.3.4 Contrato Social — OCR + NLP + LLM

| Aspecto | Detalhamento |
|---------|-------------|
| **Abordagem** | OCR + NLP para entidades + LLM para clausulas |
| **Quadro societario** | Tabela ou lista de socios com nome, CPF, %, cargo — table extraction |
| **Poderes** | Clausulas de administracao — LLM para interpretar quem pode fazer o que |
| **Desafio** | Documentos longos (5-20 pag.), alteracoes contratuais empilhadas, linguagem juridica |
| **Validacao** | Soma dos % = 100%, CPFs validos, CNPJ valido |

---

## 9. SLAs E QUALIDADE

### 9.1 Niveis de Servico por Fila

| Fila | SLA Total (horas) | Tempo Estimado para Extracao |
|------|-------------------|------------------------------|
| Programa Pe de Meia | **1h** | < 10 segundos (docs simples: RG + selfie) |
| Abertura Conta Agencia/CCA | **1h** | < 30 segundos (3-4 docs) |
| Garantias Comerciais PJ | **18h** | < 5 minutos (docs complexos: matricula, contrato) |
| Dossie CCA-Comercial/Consignado | **18h** | < 5 minutos |
| Concessao Comercial PJ | **18h** | < 5 minutos |
| Demais filas | **24h** | < 10 minutos (dossies grandes: habitacional, agro) |

### 9.2 Disponibilidade

| Metrica | Valor |
|---------|-------|
| Disponibilidade minima | **99,5%** |
| Regime de operacao | **24x7x365** |

### 9.3 Metricas de Qualidade Recomendadas

| Metrica | Meta | Justificativa |
|---------|------|--------------|
| **Acuracia de campo (Character Error Rate)** | <= 2% CER | Padrao de mercado para OCR de qualidade |
| **Field-level accuracy** | >= 95% | Campo extraido corresponde ao valor real |
| **Completude (campos obrigatorios extraidos)** | >= 98% | Itens de precisao devem ser atendidos |
| **Taxa de indicacao correta de ausencia** | >= 99% | Campos ausentes corretamente sinalizados |
| **Taxa de falsos positivos** (campo errado sem flag) | <= 1% | Campos com valor errado e alta confianca |
| **Latencia P95 por documento simples** (1-3 pag.) | < 5 segundos | Para nao comprometer SLA de 1h |
| **Latencia P95 por documento complexo** (10+ pag.) | < 60 segundos | Matriculas, contratos, laudos |

### 9.4 Penalidades

| Tipo | Formula | Descricao |
|------|---------|----------|
| Deducao por indisponibilidade (DI) | `DI = VSETF x FAIDS` | Servico indisponivel |
| Deducao por servico incorreto (VDSI) | `VDSI = 0,05% x SI x VSETF` | Campo extraido incorretamente |
| Teto de deducoes | **10% do VSETF** | Limite maximo |

> **Nota:** Um campo extraido erroneamente pode gerar penalidade na extracao E nos servicos downstream (regra que falhou por dado errado). A acuracia da extracao tem **efeito multiplicador** similar ao da classificacao.

---

## 10. MODELO DE DADOS DE SAIDA

### 10.1 Estrutura Recomendada por Campo

```json
{
  "demanda_id": "DEM-2026-001234",
  "documento_id": "DOC-5678",
  "tipo_documental": "RG",
  "timestamp_extracao": "2026-04-10T14:30:00Z",
  "campos": [
    {
      "nome": "nome_completo",
      "valor": "JOSE DA SILVA SANTOS",
      "confianca": 0.98,
      "bounding_box": {"x": 120, "y": 85, "w": 340, "h": 25},
      "pagina": 1,
      "status": "extraido"
    },
    {
      "nome": "cpf",
      "valor": "123.456.789-00",
      "confianca": 0.99,
      "bounding_box": {"x": 120, "y": 115, "w": 180, "h": 20},
      "pagina": 1,
      "status": "extraido",
      "validacao": "digito_verificador_ok"
    },
    {
      "nome": "filiacao_pai",
      "valor": null,
      "confianca": null,
      "bounding_box": null,
      "pagina": null,
      "status": "ausente",
      "motivo": "campo_nao_presente_no_documento"
    }
  ],
  "recortes": [
    {
      "nome": "foto_3x4",
      "tipo": "imagem",
      "bounding_box": {"x": 30, "y": 50, "w": 100, "h": 130},
      "pagina": 1,
      "formato": "png",
      "status": "extraido"
    }
  ],
  "metricas": {
    "total_campos_solicitados": 12,
    "campos_extraidos": 10,
    "campos_ausentes": 2,
    "confianca_media": 0.96,
    "latencia_ms": 1850
  }
}
```

### 10.2 Status Possiveis por Campo

| Status | Descricao |
|--------|----------|
| `extraido` | Campo encontrado e valor extraido com sucesso |
| `ausente` | Campo nao presente no documento (indicacao explicita conforme TR 2.3.2.1) |
| `ilegivel` | Campo presente mas impossivel de ler (baixa qualidade de imagem) |
| `baixa_confianca` | Campo extraido mas com confianca abaixo do threshold |
| `formato_invalido` | Valor extraido mas nao atende ao formato esperado (ex: CPF com 10 digitos) |

---

## 11. REQUISITOS TECNICOS DE IMPLEMENTACAO

### 11.1 Stack Tecnologico

| Camada | Tecnologia | Finalidade |
|--------|-----------|-----------|
| **OCR Engine** | Azure AI Document Intelligence, Mistral OCR, Tesseract, PaddleOCR | Reconhecimento de texto completo com bounding boxes |
| **ICR** | Azure AI Handwriting, Google Cloud Vision | Reconhecimento de texto manuscrito |
| **Table Extraction** | Azure Layout, Camelot, img2table | Deteccao e parsing de tabelas |
| **NER (Named Entity Recognition)** | spaCy pt-BR, BERTimbau | Deteccao de entidades (nomes, datas, valores) |
| **Document Understanding** | LayoutLMv3, Donut, DiT | Extracao multimodal (visual + textual + layout) |
| **LLM para interpretacao** | Claude, GPT-4 | Extracao semantica de campos em texto corrido |
| **Object Detection** | YOLO, Faster-RCNN | Deteccao de foto, assinatura, carimbo, selo |
| **Validacao** | Regex, CPF/CNPJ validators | Verificacao de formato e digitos |

### 11.2 Estrategia Multi-Engine

| Tipo de Documento | Engine Principal | Engine Complementar |
|------------------|-----------------|-------------------|
| RG, CNH, NF (template fixo) | Azure Document Intelligence / Template | Regex para validacao |
| Holerite, IRPF (semi-estruturado) | Azure + Table Extraction | NER para cabecalho |
| Matricula, Contrato Social (texto corrido) | OCR + LLM (Claude/GPT) | NLP para entidades |
| Selfie | Nao aplica (biometria) | — |
| Documentos manuscritos | ICR (Azure Handwriting) | LLM como fallback |

### 11.3 Padroes Tecnologicos Obrigatorios (Anexo I-B)

| Item | Especificacao |
|------|--------------|
| Integracao | Web Services SOAP e REST |
| Formatos de dados | JSON, XML |
| Protocolo | HTTPS (TLS 1.3) |
| API | Segura e documentada |
| Idioma | Portugues do Brasil |

---

## 12. CENARIOS DE TESTE E VALIDACAO

### 12.1 Cenarios por Tipo Documental

| # | Cenario | Tipo Doc | Resultado Esperado |
|---|---------|----------|-------------------|
| 1 | RG novo modelo, boa qualidade | RG | Todos os 12 campos extraidos, confianca > 95% |
| 2 | RG antigo, escaneado | RG | Campos extraidos com confianca variavel, foto recortada |
| 3 | CNH digital | CNH | Todos os campos, QR code detectado |
| 4 | Holerite padrao | Holerite | Tabela completa, total conferido |
| 5 | Holerite de empresa desconhecida | Holerite | Campos extraidos mesmo com layout novo |
| 6 | Matricula imovel simples (2 pag.) | Matricula | Proprietario, area, onus identificados |
| 7 | Matricula imovel complexa (20 pag.) | Matricula | Cadeia dominial, todos os onus, averbacoes |
| 8 | Contrato social com alteracoes | Doc. Constitutivo | Quadro societario ATUAL (considerando alteracoes) |
| 9 | IRPF completa | IRPF | Rendimentos, bens, dividas, resultado |
| 10 | Conta de luz como residencia | Residencia | Endereco completo, titular, referencia |
| 11 | Documento com campo ausente | Qualquer | Campo ausente corretamente sinalizado com status "ausente" |
| 12 | Documento ilegivel (scan ruim) | Qualquer | Campos ilegveis sinalizados, demais extraidos |
| 13 | Nota fiscal eletronica | NF | Chave de acesso, itens, impostos, valores |
| 14 | Laudo de avaliacao (30 pag.) | Laudo | Valor, area, engenheiro, memorial |
| 15 | Apolice com clausula CAIXA | Apolice | Deteccao da clausula beneficiaria CAIXA |
| 16 | Documento em lote (1000 docs) | Misto | SLA atendido, sem degradacao |
| 17 | Documento manuscrito parcial | Qualquer | ICR nos trechos manuscritos |
| 18 | Documento com tabela complexa | Contrato/IRPF | Tabela corretamente parseada |
| 19 | Extracao + regra simples em cascata | RG + validacao | Extracao alimenta regra sem cobranca dupla |
| 20 | Multiplos formatos de data | Qualquer | dd/mm/aaaa, dd.mm.aaaa, por extenso — todos normalizados |

### 12.2 Metricas de Aceitacao

| Metrica | Valor Minimo |
|---------|-------------|
| Field-level accuracy (docs simples) | >= 97% |
| Field-level accuracy (docs complexos) | >= 92% |
| Completude de campos obrigatorios | >= 98% |
| Taxa de ausencia corretamente sinalizada | >= 99% |
| CER (Character Error Rate) medio | <= 2% |
| Latencia P95 (doc simples) | < 5 segundos |
| Latencia P95 (doc complexo) | < 60 segundos |

---

## 13. PRECIFICACAO

### 13.1 Estrutura de Preco

| Item | Valor |
|------|-------|
| **Nome do servico na proposta** | Extracao de atributos dos documentos |
| **Quantidade anual** | 19.659.587 |
| **Unidade de cobranca** | Por documento com atributos extraidos |

### 13.2 Componentes de Custo

| Componente | Descricao | Peso no Custo |
|-----------|----------|--------------|
| **OCR Engine (API)** | Azure DI, Mistral, etc. — custo por pagina processada | ALTO |
| **LLM para interpretacao** | Claude/GPT para campos semanticos — custo por token | ALTO (para docs complexos) |
| **GPU para modelos locais** | LayoutLM, YOLO, NER — inferencia local | MEDIO |
| **Extracoes nao remuneradas** | OCR executado para regras/validacoes sem cobranca | ALTO (custo oculto) |
| **Armazenamento temporario** | Imagens + resultados por 90 dias | BAIXO |
| **Mao de obra ML** | Data scientists, ML engineers | MEDIO |
| **Monitoramento** | Acuracia, latencia, drift | BAIXO |

### 13.3 Alerta Critico de Precificacao

> **O custo real de extracao e MUITO MAIOR que o volume remunerado.** A plataforma executara extracoes para cada validacao de regra simples (96M/ano) e composta (1,7M/ano), alem das 19,6M remuneradas. O valor unitario da extracao remunerada deve subsidiar o custo total da extracao na plataforma.
>
> **Calculo de referencia:** Se cada regra simples exige ~1 campo extraido, e cada regra composta ~3 campos, o volume real de extracoes pode atingir **~100M+ operacoes de OCR/ano** — 5x o volume remunerado.

---

## 14. RISCOS ESPECIFICOS DO SERVICO

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| 1 | **Custo de OCR/LLM nao remunerado** | Certa | Margem negativa se nao precificado corretamente | Embutir custo de extracoes preparatorias nos precos dos demais servicos |
| 2 | **Variacao de layout entre emissores** | Alta | Extracao falha em layouts desconhecidos | Modelos adaptativos (Document Understanding), retraining continuo |
| 3 | **Documentos escaneados com baixa qualidade** | Alta | CER alto, campos ilegveis | Pre-processamento (binarizacao, denoising) + thresholds de qualidade |
| 4 | **Texto juridico corrido (matricula, contrato)** | Alta | LLM necessario, custo elevado | Otimizar prompts, cache de interpretacoes similares, modelos especializados |
| 5 | **Formatos de data brasileiros variados** | Alta | Parsing incorreto (12/01 = jan ou dez?) | Library de parsing com contexto pt-BR, validacao cruzada |
| 6 | **Tabelas complexas (IRPF, holerite)** | Media | Colunas misturadas, valores trocados | Table extraction especializado + validacao de somas |
| 7 | **Manuscritos parciais** | Media | ICR com baixa acuracia | Fallback para revisao humana (Operacao Assistida) |
| 8 | **Volume de pico em SLA de 1h** | Alta | Fila de extracao com backlog | Auto-scaling, pre-alocacao de recursos para filas prioritarias |
| 9 | **Mudanca de formato pela CAIXA** | Media | Schema de extracao desatualizado | Versionamento de schemas, deploy sem downtime |
| 10 | **Campos extraidos com acento/encoding errado** | Media | Dados corrompidos downstream | Normalizacao UTF-8 rigorosa em todo o pipeline |

---

## 15. CHECKLIST DE IMPLEMENTACAO

### Fase 1 — MVP (Documentos Simples + OCR)

- [ ] OCR engine configurado (Azure DI ou Mistral)
- [ ] Schema de extracao para os 5 tipos mais frequentes: RG, CNH, Residencia, Holerite, Certidao Estado Civil
- [ ] Extracao por template (zonas pre-mapeadas) para RG e CNH
- [ ] Extracao por OCR + regex para campos padronizados (CPF, CNPJ, datas)
- [ ] Indicacao explicita de campos ausentes
- [ ] Retorno em JSON estruturado com confianca por campo
- [ ] API REST documentada
- [ ] Logs com document_id, tipo, campos, confianca, latencia
- [ ] Latencia < 5s P95 para docs simples

### Fase 2 — Completo (Todos os Tipos + IA)

- [ ] Schemas para todos os 32 tipos documentais
- [ ] Table extraction para holerite, IRPF, quadro societario
- [ ] NER (Named Entity Recognition) para nomes, enderecos, valores
- [ ] Document Understanding (LayoutLM) para docs semi-estruturados
- [ ] Object detection para recortes (foto, assinatura, carimbo)
- [ ] LLM integration para extracao semantica (matricula, contrato social)
- [ ] Validacao automatica (digito CPF, soma de tabelas, formato de datas)
- [ ] Normalizacao de todos os campos (UTF-8, formatos padronizados)
- [ ] Suporte a documentos multipaginas (ate 40 paginas)
- [ ] Dashboard de acuracia por tipo e por campo

### Fase 3 — Otimizacao e Escala

- [ ] Cache de OCR para documentos re-processados
- [ ] Modelo de custo por documento (roteamento para engine mais custo-eficiente)
- [ ] Auto-scaling baseado em fila prioritaria
- [ ] Pipeline de retreinamento com correcoes humanas (feedback loop)
- [ ] Batch processing para extracoes preparatorias (otimizacao de custo)
- [ ] Metricas de custo real vs. remunerado por fila
- [ ] ICR para documentos com trechos manuscritos
- [ ] A/B testing de engines OCR por tipo documental

---

## 16. REFERENCIAS NORMATIVAS

| Documento | Secao | Conteudo Relevante |
|-----------|-------|-------------------|
| Anexo I — TR | 2.3.2 | Definicao completa do servico de extracao de dados |
| Anexo I — TR | 2.3.2.1 | 5 operacoes obrigatorias |
| Anexo I — TR | 2.3.2.2 | Remuneracao so quando produto final |
| Anexo I — TR | 2.3.2.3 | Extracao preparatoria NAO remunerada |
| Anexo I — TR | 1.1.5 | Resultado em formato estruturado definido pela CAIXA |
| Anexo I — TR | 2.7.2.1 | Exemplos de regras simples que dependem de extracao |
| Anexo I — TR | 2.7.2.3 | Exemplos de regras compostas que dependem de extracao |
| Anexo I — TR | 2.10.2 | Automacao inteligente com IA para extracao |
| Anexo I — TR | 5.2 | Formula de remuneracao |
| Anexo I — TR | 5.4.3 | Inconsistencias documentais |
| Anexo I — TR | 5.5 | Deducoes por servico incorreto |
| Anexo I — TR | 7.3.5 | Dados exclusivos para servicos contratados |
| Anexo I-A | Definicoes | Atributo extraido, OCR, ICR, janela temporal, area util, itens de precisao |
| Anexo I-B | Padrao Tecnologico | Formatos (JSON, XML), protocolos (REST, SOAP) |
| Anexo I-C | Secao 2 | 32 tipos documentais com paginas medias |
| Anexo I-C | Secao 5 | Volume: 19.659.587 extracoes/ano |
| Anexo I-H | Filas | SLAs por fila (1h, 18h, 24h) |
