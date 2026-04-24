# Servico de Validacao de Autenticidade Documental
## Especificacao Completa — Edital BPO CAIXA

**Referencia:** Termo de Referencia, Secao 2.4 | Anexo I-A (Definicoes) | Anexo I-C (Volumetria) | Anexo I-H (Filas)
**Ultima atualizacao:** 2026-04-10

---

## 1. DEFINICAO FORMAL

> **Avaliacao de autenticidade documental** — Verificacao do padrao de emissao de documentos por rotinas automaticas, que se utilizam de tecnologias de OCR e ou ICR e ou similares para a confrontacao de dados, alem do uso de tecnologias de reconhecimento facial e/ou validacao biometrica para confrontacao da imagem do documento com a base de padroes, sem qualquer interacao humana.
>
> — Anexo I-A, Definicoes de Termos

> **Score de risco de fraude** — Metrica utilizada pela CONTRATADA para aferir o grau de risco do documento (suporte e conteudo), para a existencia de sinais de adulteracao e/ou informacoes conflitantes, por meio de atribuicao de nota aos documentos avaliados, demonstrando de forma objetiva a probabilidade de ocorrencia de fraude.
>
> — Anexo I-A, Definicoes de Termos

O servico consiste em aplicar mecanismos automatizados para verificar se um documento e autentico — analisando tanto o **suporte** (a imagem/arquivo em si) quanto o **conteudo** (os dados presentes) — e retornar um score de fraude vinculado ao identificador da demanda.

**Objetivo central:** Reduzir o risco de fraude documental nos processos da CAIXA, detectando automaticamente documentos adulterados, falsificados ou com informacoes inconsistentes, **sem qualquer interacao humana** no processo de validacao.

---

## 2. ESCOPO DETALHADO DO SERVICO

### 2.1 Operacoes Obrigatorias (TR 2.4.1)

| # | Operacao | Descricao Detalhada |
|---|----------|-------------------|
| 1 | **Verificacao de padroes graficos** | Aplicar mecanismos automatizados para verificacao de padroes graficos do documento (layout, fontes, logos, selos, marcas d'agua, elementos de seguranca) |
| 2 | **Cruzamento de dados em bases** | Cruzamento de dados em bases internas e externas, podendo incluir batimento com documentos complementares do mesmo dossie |
| 3 | **Validacao biometrica** | Realizar validacao por padroes e/ou biometria (facial e/ou impressao digital), comparando elementos do documento com bancos de padroes e dados biometricos disponiveis |
| 4 | **Retorno de score de fraude** | Retornar a CAIXA o score de indicio de fraude documental (nivel de autenticidade), vinculado ao identificador da demanda |

### 2.2 Tecnologias Incluidas no Escopo (TR 2.4.1)

O TR explicita que o servico **inclui todas as atividades necessarias** para validar os documentos, citando especificamente:

| Tecnologia | Papel na Validacao |
|-----------|--------------------|
| **OCR** | Extrair texto do documento para cruzamento de dados |
| **ICR** | Reconhecer texto manuscrito para verificacao de assinaturas e campos manuscritos |
| **Extracao de Dados** | Obter campos estruturados para cruzamento com bases |
| **IA** | Deteccao de padroes de fraude, analise de imagem, biometria facial |

> **Ponto critico:** A extracao de dados realizada como parte da validacao de autenticidade **NAO e remunerada separadamente** (TR 2.3.2.3). Todo o custo de OCR, ICR e extracao necessarios para validar autenticidade esta embutido neste servico.

### 2.3 Conceito de "Sem Qualquer Interacao Humana"

A definicao formal do Anexo I-A enfatiza que a validacao deve ocorrer **sem qualquer interacao humana**. Isso significa:

- O processo deve ser **100% automatizado**
- Nao ha etapa de revisao manual no fluxo de validacao
- O score e gerado por algoritmos, nao por analistas
- A decisao de encaminhar para revisao humana (via Operacao Assistida) so ocorre **apos** o score ser gerado, nunca durante

---

## 3. DIMENSOES DA VALIDACAO

### 3.1 Validacao de Suporte (Documento Fisico/Digital)

Analisa se o **arquivo em si** (imagem, PDF) apresenta sinais de adulteracao:

| Verificacao | Descricao | Tecnologia |
|------------|----------|-----------|
| **Consistencia de fontes** | Documento usa fontes diferentes do padrao esperado para aquele tipo | Analise tipografica por IA |
| **Edicao de imagem** | Deteccao de areas editadas (Photoshop, corte/colagem) | Error Level Analysis (ELA), deteccao de artefatos JPEG |
| **Metadados do arquivo** | Analise de metadados (EXIF, XMP) para detectar manipulacao | Parsing de metadados |
| **Resolucao inconsistente** | Areas do documento com resolucao diferente (indica insercao) | Analise de frequencia espacial |
| **Marcas d'agua e selos** | Verificacao da presenca e integridade de marcas de seguranca | Template matching, deteccao de objetos |
| **Padrao de impressao** | Verificacao se o padrao grafico corresponde ao emissor oficial | Comparacao com templates de referencia |
| **Bordas de recorte** | Deteccao de bordas artificiais indicando composicao de imagens | Edge detection, analise de gradiente |
| **Consistencia de iluminacao** | Sombras e iluminacao consistentes em toda a imagem | Analise de luminosidade por regioes |

### 3.2 Validacao de Conteudo (Dados do Documento)

Analisa se os **dados contidos** no documento sao consistentes e veridicos:

| Verificacao | Descricao | Base de Dados |
|------------|----------|--------------|
| **CPF valido** | Digito verificador correto, CPF ativo na RF | Receita Federal (base externa) |
| **CNPJ valido** | Digito verificador, situacao cadastral | Receita Federal (base externa) |
| **Nome vs. CPF** | Nome no documento confere com nome vinculado ao CPF | Receita Federal / Serasa / bases CAIXA |
| **Data de nascimento vs. base** | Data no documento confere com dados oficiais | Receita Federal |
| **Data de emissao plausivel** | Documento nao emitido em data futura ou impossivel | Regra logica |
| **Validade do documento** | Documento dentro do prazo de validade | Regra logica |
| **Orgao emissor real** | Orgao expedidor existe e emite aquele tipo de documento | Base de referencia |
| **Numero de registro valido** | Formato e sequencia conforme padrao do emissor | Regex + base de referencia |
| **Cruzamento entre documentos** | Dados em um documento conferem com dados em outro do mesmo dossie | Dados extraidos de outros documentos do dossie |
| **Endereco consistente** | CEP corresponde a cidade/UF/logradouro | Base de CEPs (Correios) |

### 3.3 Validacao Biometrica

Analisa elementos biometricos do documento comparando com bases de referencia:

| Verificacao | Descricao | Tecnologia |
|------------|----------|-----------|
| **Reconhecimento facial — Doc vs. Selfie** | Comparar foto do documento de identificacao com selfie do cliente | Face matching (1:1), liveness detection |
| **Reconhecimento facial — Doc vs. Base** | Comparar foto do documento com foto em banco de dados biometrico | Face matching (1:N) |
| **Validacao de impressao digital** | Comparar impressao digital do documento com base biometrica | Fingerprint matching |
| **Liveness detection** | Verificar que a selfie e de uma pessoa viva (nao foto de foto) | Anti-spoofing: texture analysis, depth, motion |
| **Qualidade da foto** | Verificar se a foto do documento atende requisitos minimos | Face quality assessment |
| **Consistencia facial** | Verificar se a foto e de uma pessoa real, nao gerada por IA | Deepfake detection |

### 3.4 Score de Risco de Fraude

O resultado final e um **score unico** que agrega todas as dimensoes de validacao:

| Componente do Score | Peso Sugerido | Descricao |
|--------------------|--------------|----------|
| Score de suporte (integridade da imagem) | 25% | Sem adulteracao grafica detectada |
| Score de conteudo (dados consistentes) | 35% | Dados conferem com bases internas e externas |
| Score biometrico (face match) | 25% | Foto do documento corresponde a selfie/base |
| Score de cruzamento (documentos do dossie) | 15% | Dados consistentes entre documentos do mesmo dossie |
| **Score final composto** | **100%** | **Indice de autenticidade do documento** |

> **Nota:** O TR nao define a composicao exata do score — apenas exige que seja um score de indicio de fraude retornado de forma objetiva. A composicao acima e uma recomendacao de produto.

---

## 4. VOLUMETRIA

### 4.1 Volume Anual Estimado

| Metrica | Valor |
|---------|-------|
| **Avaliacao de autenticidade documental** | **14.418.118 / ano** |
| Media mensal | ~1.201.510 / mes |
| Media diaria (dias uteis ~250) | ~57.673 / dia |
| Media diaria (24x7 = 365) | ~39.502 / dia |
| Media horaria (pico 08h-20h) | ~4.806 / hora |

### 4.2 Relacao com Volume Total de Documentos

| Metrica | Valor | % |
|---------|-------|---|
| Total de documentos tratados/classificados/extraidos | 19.659.587 | 100% |
| Documentos que passam por validacao de autenticidade | 14.418.118 | **73,3%** |
| Documentos que NAO passam por validacao | 5.241.469 | 26,7% |

> **Insight:** Aproximadamente **3 em cada 4 documentos** recebem validacao de autenticidade. Os 26,7% restantes provavelmente sao tipos documentais onde autenticidade e menos critica (formularios internos CAIXA, modelos padrao, documentos de baixo risco).

### 4.3 Estimativa de Volume por Tipo de Validacao

| Tipo de Validacao | Volume Estimado/Ano | Justificativa |
|-------------------|--------------------|--------------| 
| Verificacao de padroes graficos | ~14.418.118 (100%) | Aplicada em todos os documentos validados |
| Cruzamento de dados em bases | ~10.000.000 (~70%) | Documentos com dados verificaveis (CPF, CNPJ) |
| Validacao biometrica (facial) | ~5.500.000 (~38%) | RG + CNH + Selfie — processos com biometria |
| Cruzamento entre documentos do dossie | ~8.000.000 (~55%) | Dossies com 2+ documentos |

### 4.4 Distribuicao por Processo

| Processo | Demandas/Ano | Autenticidade Critica? | Volume Estimado |
|----------|-------------|----------------------|----------------|
| ONBOARDING FGTS | 6.829.602 | Media (docs simples) | ~4.000.000 |
| Conta Digital | 4.704.706 | Alta (abertura remota) | ~3.500.000 |
| Abertura de Conta | 3.510.402 | Alta (KYC) | ~2.500.000 |
| Concessao Habitacional | 1.839.620 | Muito alta (valor alto) | ~1.800.000 |
| Dossie CCA | 1.134.461 | Alta (credito) | ~1.000.000 |
| Agronegocio | 460.607 | Muito alta (multi-doc) | ~450.000 |
| Garantias Comerciais PJ | 382.962 | Muito alta (garantia) | ~380.000 |
| Concessao Comercial PJ | 325.802 | Alta (credito PJ) | ~320.000 |
| Garantia Habitacional CIP | 278.657 | Muito alta (imovel) | ~270.000 |
| Programa Pe de Meia | 97.293 | Media (docs simples) | ~80.000 |

---

## 5. REGRAS DE NEGOCIO

### 5.1 Automatizacao Total

- A validacao de autenticidade e **100% automatizada** — sem interacao humana (Anexo I-A)
- OCR, ICR, IA e biometria sao ferramentas do processo automatizado
- O resultado e um score numerico objetivo, nao uma opiniao

### 5.2 Score de Fraude — Definicao

O score deve:
- Aferir o grau de risco do **suporte** (imagem/arquivo) e do **conteudo** (dados)
- Detectar sinais de **adulteracao** e/ou **informacoes conflitantes**
- Ser expresso como **nota atribuida ao documento**
- Demonstrar de forma **objetiva a probabilidade de ocorrencia de fraude**
- Estar **vinculado ao identificador da demanda**

### 5.3 Batimento com Documentos Complementares

O servico pode incluir **batimento com documentos complementares** do mesmo dossie:
- Nome no RG vs. nome no holerite
- CPF no RG vs. CPF na declaracao de IRPF
- Endereco na conta de consumo vs. endereco no contrato
- Foto no RG vs. selfie do cliente

### 5.4 Remuneracao

| Item | Valor |
|------|-------|
| Nome do servico na proposta | Avaliacao de autenticidade documental |
| Quantidade anual | 14.418.118 |
| Unidade de cobranca | Por documento validado |
| Inclui | OCR, ICR, extracao de dados e IA necessarios |

> **Alerta:** O custo de OCR/extracao necessario para a validacao esta **embutido** neste servico. NAO ha cobranca separada de extracao quando usada como etapa da validacao.

### 5.5 Consultas em Bases Externas

O cruzamento de dados pode exigir consultas em bases externas (publicas e privadas):
- **Bases publicas** (gratuitas): Receita Federal (CPF/CNPJ), Correios (CEP), TSE
- **Bases privadas** (com custo): Serasa, bureaus de credito, bases biometricas
- Custos de bases privadas sao da **CONTRATADA** (nao ressarcidos como custo indireto, pois ja embutidos no servico)

### 5.6 Relacao com Consulta em Bases (Servico 2.6)

O servico de "Consulta e disponibilizacao de dados e documentos" (TR 2.6) e um servico SEPARADO com remuneracao propria. A diferenca:

| Aspecto | Validacao de Autenticidade (2.4) | Consulta em Bases (2.6) |
|---------|----------------------------------|------------------------|
| Objetivo | Verificar se documento e autentico | Obter informacoes/certidoes de bases |
| Consulta a base | Ferramenta interna do processo | Produto final entregue a CAIXA |
| Remuneracao da consulta | Embutida no servico | Remunerada separadamente |
| Output | Score de fraude | Dado/documento obtido |

---

## 6. TIPOS DE FRAUDE A DETECTAR

### 6.1 Fraudes de Suporte (Documento Fisico)

| Tipo de Fraude | Descricao | Indicadores | Dificuldade |
|---------------|----------|------------|------------|
| **Documento falsificado** | Documento inteiro fabricado (nao emitido pelo orgao oficial) | Layout incorreto, fontes erradas, selos falsos, qualidade de impressao | Media |
| **Documento adulterado** | Documento real com campos alterados (nome, data, valores) | Inconsistencia de fontes na area editada, artefatos de edicao, resolucao diferente | Alta |
| **Foto substituida** | Foto original do documento trocada por outra | Bordas de recorte na area da foto, diferenca de resolucao, sombras inconsistentes | Alta |
| **Montagem/composicao** | Partes de diferentes documentos combinadas | Bordas visiveis, inconsistencia de iluminacao, metadados de edicao | Media |
| **Documento digital manipulado** | PDF editado digitalmente | Metadados de edicao (Adobe Acrobat), camadas de edicao, fonts embedadas inconsistentes | Media |
| **Impressao de documento digital** | Screenshot ou foto de tela printada como se fosse scan | Padrao de pixel, ausencia de textura de papel, moire pattern | Baixa |

### 6.2 Fraudes de Conteudo (Dados)

| Tipo de Fraude | Descricao | Indicadores | Dificuldade |
|---------------|----------|------------|------------|
| **CPF de terceiro** | Documento com CPF de outra pessoa | Nome nao confere com CPF na Receita Federal | Baixa |
| **Dados inventados** | Campos com dados ficticios | CPF invalido (digito verificador), orgao inexistente, endereco inexistente | Baixa |
| **Renda inflada** | Holerite com valores alterados para cima | Total proventos - descontos != liquido, valores incompativeis com cargo/empresa | Alta |
| **Matricula manipulada** | Onus removidos ou adicionados na certidao | Dados nao conferem com registro cartorial (se consultado) | Muito alta |
| **Contrato social alterado** | Quadro societario ou poderes modificados | Dados nao conferem com Junta Comercial (se consultado) | Muito alta |
| **Certidao vencida** | Certidao fora do prazo de validade apresentada como atual | Data de emissao fora do periodo exigido | Baixa |
| **Documento de terceiro** | Documento real de outra pessoa utilizado por fraude | Foto nao corresponde a selfie (face matching falha) | Baixa |

### 6.3 Fraudes Biometricas

| Tipo de Fraude | Descricao | Indicadores | Dificuldade |
|---------------|----------|------------|------------|
| **Foto de foto** | Selfie tirada de uma foto impressa | Textura de papel, reflexos, ausencia de profundidade | Media |
| **Foto de tela** | Selfie tirada de uma tela de computador/celular | Padrao de pixel, moire, reflexo de tela | Media |
| **Mascara 3D** | Pessoa usando mascara facial realista | Textura anomala, falta de micro-expressoes | Alta |
| **Deepfake** | Video/imagem gerada por IA | Artefatos de geracao, inconsistencias em bordas do rosto | Muito alta |
| **Identidade sintetica** | Combinacao de dados reais e ficticios em uma identidade nova | CPF real com nome diferente, historico inconsistente | Muito alta |

---

## 7. DETALHAMENTO POR TIPO DOCUMENTAL

### 7.1 Matriz de Validacao por Tipo

| Tipo Documental | Padrao Grafico | Cruzamento Dados | Biometria Facial | Cruzamento Dossie | Risco de Fraude |
|----------------|---------------|-----------------|-----------------|-------------------|----------------|
| **RG** | Template do estado, brasao, fontes | CPF, nome, data nasc. vs. RF | Foto vs. selfie | Nome vs. outros docs | ALTO |
| **CNH** | Template DETRAN, hologramas, QR | CPF, nome, validade, categorias | Foto vs. selfie | Nome vs. outros docs | ALTO |
| **Selfie** | N/A (nao e documento) | N/A | Liveness + face match com doc | N/A | MEDIO (spoofing) |
| **Holerite** | Layout da empresa | Valores: proventos-descontos=liquido | N/A | Renda vs. IRPF, nome vs. RG | ALTO |
| **IRPF** | Template Receita Federal | CPF, rendimentos, recibo vs. RF | N/A | Renda vs. holerite | MEDIO |
| **Certidao Matricula** | Selo cartorial, formato | Numero matricula vs. cartorio | N/A | Proprietario vs. contrato | MUITO ALTO |
| **Contrato Social** | Formato Junta Comercial | CNPJ, socios vs. Junta | N/A | Socios vs. RG, poderes | MUITO ALTO |
| **Residencia** | Layout concessionaria | CEP vs. endereco, titular | N/A | Endereco vs. outros docs | BAIXO |
| **Nota Fiscal** | Layout padrao NF-e | Chave acesso vs. SEFAZ, CNPJ | N/A | Valor vs. contrato | MEDIO |
| **Apolice** | Layout seguradora | Numero apolice vs. seguradora | N/A | Beneficiario = CAIXA? | MEDIO |
| **Laudo Avaliacao** | ART/RRT do engenheiro | CREA do profissional, endereco | N/A | Valor vs. financiamento | ALTO |
| **Certidao Estado Civil** | Selo cartorial | Dados vs. cartorio (se possivel) | N/A | Nome vs. outros docs | BAIXO |

### 7.2 Documentos de Maior Risco

| Prioridade de Fraude | Documentos | Justificativa |
|---------------------|-----------|--------------|
| **CRITICO** | Matricula de Imovel, Contrato Social | Determinam garantias de alto valor, onus e poderes de representacao |
| **ALTO** | RG, CNH, Holerite, Laudo de Avaliacao | Identidade do cliente, renda declarada, valor de garantia |
| **MEDIO** | IRPF, Nota Fiscal, Apolice | Complementam analise financeira |
| **BAIXO** | Residencia, Certidao Estado Civil, Modelo CAIXA | Documentos simples com menor potencial de dano |

---

## 8. RELACAO COM OUTROS SERVICOS

### 8.1 Posicao no Pipeline

```
[Documento tratado + classificado + dados extraidos]
         |
         v
  +------------------------------------------+
  | VALIDACAO DE AUTENTICIDADE DOCUMENTAL     |  <-- ESTE SERVICO
  |                                          |
  | +-------+  +----------+  +-----------+  |
  | |Padrao |  |Cruzamento|  |Biometria  |  |
  | |Grafico|  |de Dados  |  |Facial     |  |
  | +---+---+  +----+-----+  +-----+-----+  |
  |     |           |              |          |
  |     v           v              v          |
  |  +------------------------------------+  |
  |  | COMPOSICAO DO SCORE DE FRAUDE       |  |
  |  +------------------------------------+  |
  +------------------------------------------+
         |
         v
  [Score de fraude + ID demanda]
         |
    +----|----+
    |         |
    v         v
 [Score OK] [Score ruim]
    |         |
    v         v
 [Regras    [Rejeicao /
  Negociais] Revisao
             Humana]
```

### 8.2 Dependencias Upstream

| Servico | Relacao |
|---------|--------|
| **Tratamento de arquivo digital** | Imagem limpa — qualidade impacta deteccao de adulteracao |
| **Classificacao documental** | Define QUAL tipo de documento, determinando quais validacoes aplicar |
| **Extracao de dados** | Fornece campos estruturados para cruzamento com bases (custo embutido) |

### 8.3 Dependencias Downstream

| Servico | Como Usa o Score |
|---------|-----------------|
| **Regras negociais** | Score de fraude pode ser input para regras compostas |
| **Rejeicao de documento** | Score abaixo do threshold gera rejeicao |
| **Rejeicao de dossie** | Multiplos documentos com score ruim rejeitam o dossie inteiro |
| **Operacao assistida** | Documentos com score em zona cinzenta encaminhados para revisao humana |
| **Dashboard/relatorios** | Estatisticas de fraude por tipo, por agencia, por periodo |

### 8.4 Interacao com Biometria (Selfie)

```
[Selfie do cliente]              [RG/CNH do cliente]
       |                                |
       v                                v
  [Liveness check]              [Extracao da foto 3x4]
       |                                |
       v                                v
  [Face encoding]               [Face encoding]
       |                                |
       +---------> FACE MATCH <---------+
                      |
                      v
              [Score biometrico]
                      |
                      v
              [Compoe score final de autenticidade]
```

---

## 9. DEFINICOES TECNICAS RELACIONADAS

### 9.1 Avaliacao de Autenticidade Documental (Anexo I-A)
Verificacao do padrao de emissao de documentos por rotinas automaticas, que se utilizam de tecnologias de OCR e ou ICR e ou similares para a confrontacao de dados, alem do uso de tecnologias de reconhecimento facial e/ou validacao biometrica para confrontacao da imagem do documento com a base de padroes, sem qualquer interacao humana.

### 9.2 Score de Risco de Fraude (Anexo I-A)
Metrica utilizada pela CONTRATADA para aferir o grau de risco do documento (suporte e conteudo), para a existencia de sinais de adulteracao e/ou informacoes conflitantes, por meio de atribuicao de nota aos documentos avaliados, demonstrando de forma objetiva a probabilidade de ocorrencia de fraude.

### 9.3 Cruzamento de Dados (Anexo I-A)
Validacao de veracidade das informacoes obtidas de documentos por meio de sua comparacao com bases de dados e ou campos de formularios a que se tenha acesso, sem qualquer interacao humana.

### 9.4 OCR / ICR (Anexo I-A)
Tecnologias de reconhecimento de caracteres utilizadas como ferramentas dentro do processo de validacao — nao como servico isolado.

---

## 10. SLAs E QUALIDADE

### 10.1 Niveis de Servico por Fila

| Fila | SLA Total (horas) | Tempo Estimado para Validacao |
|------|-------------------|-------------------------------|
| Programa Pe de Meia | **1h** | < 15 segundos (doc simples + selfie) |
| Abertura Conta Agencia/CCA | **1h** | < 30 segundos (RG/CNH + selfie + cruzamento) |
| Garantias Comerciais PJ | **18h** | < 5 minutos (docs complexos + consultas externas) |
| Dossie CCA-Comercial/Consignado | **18h** | < 5 minutos |
| Concessao Comercial PJ | **18h** | < 5 minutos |
| Demais filas | **24h** | < 10 minutos (dossies com multiplos documentos) |

### 10.2 Disponibilidade

| Metrica | Valor |
|---------|-------|
| Disponibilidade minima | **99,5%** |
| Regime de operacao | **24x7x365** |

### 10.3 Metricas de Qualidade Recomendadas

| Metrica | Meta | Justificativa |
|---------|------|--------------|
| **True Positive Rate (sensibilidade)** | >= 95% | Detectar 95% dos documentos fraudulentos |
| **True Negative Rate (especificidade)** | >= 98% | Nao rejeitar indevidamente documentos legitimos |
| **False Positive Rate** | <= 2% | Maximo de 2% de documentos legitimos flagrados como fraude |
| **False Negative Rate** | <= 5% | Maximo de 5% de documentos fraudulentos nao detectados |
| **Acuracia de face matching (1:1)** | >= 99% | Padrao de mercado para verificacao facial |
| **Liveness detection accuracy** | >= 97% | Detectar 97% das tentativas de spoofing |
| **Latencia P95 (doc simples + biometria)** | < 5 segundos | SLA de 1h nas filas prioritarias |
| **Latencia P95 (doc complexo + consulta base)** | < 30 segundos | Consultas externas adicionam latencia |

### 10.4 Penalidades

| Tipo | Formula | Descricao |
|------|---------|----------|
| Deducao por indisponibilidade (DI) | `DI = VSETF x FAIDS` | Servico indisponivel |
| Deducao por servico incorreto (VDSI) | `VDSI = 0,05% x SI x VSETF` | Validacao incorreta (fraude nao detectada ou falso positivo) |
| Teto de deducoes | **10% do VSETF** | Limite maximo |

> **Risco critico:** Um documento fraudulento nao detectado (falso negativo) pode gerar prejuizo financeiro para a CAIXA muito superior a penalidade contratual. A responsabilidade por prejuizos e da CONTRATADA (TR 7.12.6).

---

## 11. REQUISITOS TECNICOS DE IMPLEMENTACAO

### 11.1 Stack Tecnologico

| Camada | Tecnologia | Finalidade |
|--------|-----------|-----------|
| **Analise de suporte** | Error Level Analysis (ELA), metadata parsing, frequency analysis | Detectar adulteracao de imagem |
| **OCR/ICR** | Azure DI, Tesseract, PaddleOCR | Extrair texto para cruzamento |
| **Face detection** | MTCNN, RetinaFace, BlazeFace | Detectar rostos em documentos e selfies |
| **Face matching** | ArcFace, FaceNet, InsightFace | Comparacao 1:1 entre faces |
| **Liveness detection** | iBeta certified SDK, deteccao de profundidade | Anti-spoofing |
| **Deepfake detection** | CNN treinada em deepfakes, frequency analysis | Detectar faces geradas por IA |
| **Consulta a bases** | APIs REST/SOAP (Receita Federal, Serasa, SEFAZ) | Cruzamento de dados |
| **Motor de score** | Modelo ML (XGBoost, LightGBM) ou rede neural | Composicao do score final |
| **Template matching** | Siamese networks, SIFT/SURF features | Comparacao com templates de referencia por tipo |

### 11.2 Arquitetura de Validacao

```
[Documento + Metadados + Tipo]
         |
    +----+----+
    |         |
    v         v
[ANALISE DE  [ANALISE DE
 SUPORTE]     CONTEUDO]
    |         |
    |    +----+----+
    |    |         |
    |    v         v
    | [CRUZAMENTO [CRUZAMENTO
    |  BASES]      DOSSIE]
    |    |         |
    +----+---------+
         |
    +----+----+
    |         |
    v         v
[BIOMETRIA]  [COMPOSICAO
(se aplic.)   DO SCORE]
    |         |
    +----+----+
         |
         v
  [SCORE FINAL]
  0.0 -------- 1.0
  (fraude)  (autentico)
```

### 11.3 Faixas de Score Recomendadas

| Faixa | Score | Classificacao | Acao |
|-------|-------|-------------|------|
| **Verde** | 0.85 – 1.00 | Autenticidade confirmada | Seguir para regras negociais |
| **Amarelo** | 0.60 – 0.84 | Suspeita moderada | Flag para revisao humana (Operacao Assistida) |
| **Vermelho** | 0.00 – 0.59 | Alta probabilidade de fraude | Rejeitar documento + alertar |

> Os thresholds sao parametrizaveis pela CAIXA e podem variar por tipo de documento e processo.

### 11.4 Padroes Tecnologicos Obrigatorios (Anexo I-B)

| Item | Especificacao |
|------|--------------|
| Integracao | Web Services SOAP e REST |
| Formatos de dados | JSON, XML |
| Protocolo | HTTPS (TLS 1.3) |
| API | Segura e documentada |
| Idioma | Portugues do Brasil |

---

## 12. CENARIOS DE TESTE E VALIDACAO

### 12.1 Cenarios por Tipo de Fraude

| # | Cenario | Tipo de Fraude | Resultado Esperado |
|---|---------|---------------|-------------------|
| 1 | RG autentico, boa qualidade | Nenhuma | Score > 0.85 (verde) |
| 2 | RG com foto substituida (Photoshop) | Adulteracao | Score < 0.60 (vermelho) |
| 3 | RG com nome editado digitalmente | Adulteracao | Score < 0.60, flag: "inconsistencia tipografica" |
| 4 | CNH totalmente falsificada | Falsificacao | Score < 0.60, flag: "layout nao confere com template" |
| 5 | Selfie real vs. foto do RG | Nenhuma | Face match > 0.95, liveness OK |
| 6 | Selfie de foto impressa (spoofing) | Biometrica | Liveness check falha, score biometrico < 0.30 |
| 7 | Selfie de tela (spoofing) | Biometrica | Liveness check falha |
| 8 | RG de terceiro com selfie do fraudador | Identidade | Face match < 0.50, flag: "faces nao correspondem" |
| 9 | Holerite com valor alterado para cima | Conteudo | Score < 0.70, flag: "calculo proventos-descontos inconsistente" |
| 10 | IRPF com CPF invalido | Conteudo | Score < 0.60, flag: "CPF invalido" |
| 11 | Certidao matricula adulterada (onus removido) | Adulteracao | Score < 0.70, flag: "area com resolucao inconsistente" |
| 12 | Contrato social com quadro societario alterado | Conteudo | Score < 0.70, flag: "dados divergem da Junta Comercial" |
| 13 | Documento autentico mas vencido | Conteudo | Score > 0.85 mas flag: "documento fora da validade" |
| 14 | Nome no RG diferente do holerite | Cruzamento | Score reduzido, flag: "nomes divergentes entre documentos" |
| 15 | CPF no RG nao confere com RF | Cruzamento base | Score < 0.60, flag: "CPF nao confere com base RF" |
| 16 | Documento com metadados de edicao (Adobe) | Digital | Score < 0.70, flag: "metadados indicam edicao" |
| 17 | Deepfake sofisticado como selfie | Biometrica | Score biometrico reduzido, flag: "artefatos de geracao detectados" |
| 18 | Documento digitalizado com boa qualidade | Nenhuma | Score > 0.85 (sem falso positivo) |
| 19 | Documento scan de baixa qualidade (sem fraude) | Nenhuma | Score > 0.70 com flag: "qualidade baixa, confianca reduzida" |
| 20 | Volume de pico (1000 validacoes simultaneas) | N/A | Processamento sem degradacao de SLA |

### 12.2 Metricas de Aceitacao

| Metrica | Valor Minimo |
|---------|-------------|
| True Positive Rate (fraude detectada) | >= 95% |
| True Negative Rate (autentico confirmado) | >= 98% |
| False Positive Rate | <= 2% |
| Face match accuracy (1:1) | >= 99% |
| Liveness detection accuracy | >= 97% |
| Latencia P95 (doc simples) | < 5 segundos |
| Latencia P95 (doc complexo + consultas) | < 30 segundos |

---

## 13. MODELO DE DADOS DE SAIDA

### 13.1 Estrutura do Retorno

```json
{
  "demanda_id": "DEM-2026-001234",
  "documento_id": "DOC-5678",
  "tipo_documental": "RG",
  "timestamp_validacao": "2026-04-10T14:30:00Z",
  "score_final": 0.92,
  "classificacao": "verde",
  "componentes": {
    "suporte": {
      "score": 0.95,
      "verificacoes": [
        {"tipo": "consistencia_fontes", "resultado": "ok", "confianca": 0.97},
        {"tipo": "deteccao_edicao", "resultado": "ok", "confianca": 0.94},
        {"tipo": "metadados", "resultado": "ok", "confianca": 0.99},
        {"tipo": "selos_marcas", "resultado": "ok", "confianca": 0.90}
      ]
    },
    "conteudo": {
      "score": 0.88,
      "verificacoes": [
        {"tipo": "cpf_valido", "resultado": "ok", "base": "receita_federal"},
        {"tipo": "nome_vs_cpf", "resultado": "ok", "base": "receita_federal"},
        {"tipo": "data_nascimento_vs_base", "resultado": "ok", "base": "receita_federal"},
        {"tipo": "data_emissao_plausivel", "resultado": "ok", "regra": "logica"}
      ]
    },
    "biometria": {
      "score": 0.96,
      "verificacoes": [
        {"tipo": "face_match_doc_selfie", "resultado": "ok", "similaridade": 0.97},
        {"tipo": "liveness", "resultado": "ok", "confianca": 0.99}
      ]
    },
    "cruzamento_dossie": {
      "score": 0.90,
      "verificacoes": [
        {"tipo": "nome_rg_vs_holerite", "resultado": "ok", "similaridade": 1.0},
        {"tipo": "cpf_rg_vs_irpf", "resultado": "ok", "match": true}
      ]
    }
  },
  "alertas": [],
  "latencia_ms": 2340
}
```

### 13.2 Exemplo com Fraude Detectada

```json
{
  "demanda_id": "DEM-2026-005678",
  "documento_id": "DOC-9012",
  "tipo_documental": "Holerite",
  "score_final": 0.42,
  "classificacao": "vermelho",
  "componentes": {
    "suporte": {"score": 0.85},
    "conteudo": {
      "score": 0.30,
      "verificacoes": [
        {"tipo": "calculo_proventos_descontos", "resultado": "falha",
         "detalhe": "Total proventos (R$ 15.230,00) - Total descontos (R$ 3.450,00) != Liquido informado (R$ 14.780,00). Diferenca: R$ 3.000,00"}
      ]
    },
    "biometria": {"score": null, "motivo": "nao_aplicavel_holerite"},
    "cruzamento_dossie": {
      "score": 0.45,
      "verificacoes": [
        {"tipo": "renda_holerite_vs_irpf", "resultado": "divergente",
         "detalhe": "Renda mensal holerite (R$ 14.780) x 12 = R$ 177.360 incompativel com rendimentos IRPF (R$ 98.400)"}
      ]
    }
  },
  "alertas": [
    {"severidade": "critica", "tipo": "inconsistencia_valores", "mensagem": "Calculo de proventos-descontos nao confere com liquido"},
    {"severidade": "critica", "tipo": "cruzamento_divergente", "mensagem": "Renda declarada no holerite incompativel com IRPF"}
  ]
}
```

---

## 14. PRECIFICACAO

### 14.1 Estrutura de Preco

| Item | Valor |
|------|-------|
| **Nome do servico na proposta** | Avaliacao de autenticidade documental |
| **Quantidade anual** | 14.418.118 |
| **Unidade de cobranca** | Por documento validado |

### 14.2 Componentes de Custo

| Componente | Descricao | Peso no Custo |
|-----------|----------|--------------|
| **OCR/ICR embutido** | Extracao de dados necessaria para cruzamento — NAO remunerada separadamente | ALTO |
| **Face matching API** | SDK ou API de biometria facial (custo por comparacao) | ALTO |
| **Liveness detection** | SDK anti-spoofing (custo por verificacao) | MEDIO |
| **Consultas em bases externas** | Receita Federal, bureaus, SEFAZ (custo por consulta) | ALTO |
| **GPU para analise de imagem** | Modelos de deteccao de adulteracao, deepfake | MEDIO |
| **Template database** | Manutencao de templates de referencia por tipo documental | BAIXO |
| **ML model training** | Treinamento e atualizacao dos modelos de fraude | MEDIO |
| **Infraestrutura** | Redundancia 99,5%, auto-scaling, monitoramento | MEDIO |

### 14.3 Alerta de Precificacao

> **Este e um dos servicos mais caros de operar** pois combina: OCR (embutido), biometria facial (SDK caro), consultas a bases externas (custo por query), e modelos de IA para deteccao de fraude (GPU). O valor unitario deve refletir essa complexidade.
>
> **Referencia de mercado:** Solucoes de validacao de identidade custam entre R$ 0,50 e R$ 5,00 por verificacao, dependendo dos componentes ativados (face match + liveness + consulta bases).

---

## 15. RISCOS ESPECIFICOS DO SERVICO

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| 1 | **Fraude nao detectada (falso negativo)** | Media | Prejuizo financeiro para a CAIXA, responsabilidade da CONTRATADA | Modelos com alta sensibilidade, multiplas camadas de validacao |
| 2 | **Excesso de falsos positivos** | Media | Clientes legitimos rejeitados, insatisfacao, perda de negocios | Threshold ajustavel por tipo/processo, zona amarela com revisao humana |
| 3 | **Custo de consultas externas** | Alta | Erosao de margem se volume de consultas alto | Otimizar quais consultas sao essenciais por tipo de documento |
| 4 | **Deepfakes cada vez mais sofisticados** | Crescente | Modelos desatualizados nao detectam fraudes novas | Atualizacao continua de modelos, integracao com feeds de ameacas |
| 5 | **Bases externas indisponiveis** | Media | Cruzamento incompleto, score menos confiavel | Fallback com score parcial + flag de indisponibilidade de base |
| 6 | **Novos tipos de documentos** | Media | Sem templates de referencia para validar suporte | Pipeline de criacao de templates, modelo zero-shot para anomalias |
| 7 | **Biometria facial com vies** | Media | Acuracia menor para determinados grupos demograficos | SDK com certificacao de fairness, testes com dataset diverso |
| 8 | **Latencia de consultas externas** | Alta | Impacta SLA das filas prioritarias (1h) | Cache de consultas recentes, pre-fetch em paralelo, timeout com fallback |
| 9 | **LGPD e dados biometricos** | Alta | Dados biometricos sao sensiveis pela LGPD | Armazenamento minimo, eliminacao em 90 dias, criptografia AES 128+ |
| 10 | **Custo de OCR embutido nao remunerado** | Certa | 14,4M extracoes OCR sem receita propria | Embutir no preco da validacao, otimizar com OCR parcial (nao full) |

---

## 16. CHECKLIST DE IMPLEMENTACAO

### Fase 1 — MVP (Suporte + Biometria Basica)

- [ ] Analise de suporte: deteccao de edicao (ELA), metadados, consistencia de fontes
- [ ] Face detection e extraction de documentos (foto 3x4)
- [ ] Face matching 1:1 (foto documento vs. selfie)
- [ ] Liveness detection basico (foto de foto, foto de tela)
- [ ] Score composto basico (suporte + biometria)
- [ ] API REST com retorno de score + alertas + ID demanda
- [ ] Logs estruturados com rastreabilidade completa
- [ ] Templates de referencia para RG, CNH (modelos mais comuns)

### Fase 2 — Completo (Cruzamento + Bases)

- [ ] Cruzamento com Receita Federal (CPF/CNPJ, nome, situacao)
- [ ] Cruzamento entre documentos do mesmo dossie
- [ ] Validacao de calculos (proventos-descontos, somas de tabelas)
- [ ] Verificacao de validade de documentos (data de emissao vs. prazo)
- [ ] Verificacao de formatos (CPF/CNPJ digito verificador, CEP vs. endereco)
- [ ] Templates de referencia para todos os 32 tipos documentais
- [ ] Score composto com 4 componentes (suporte + conteudo + biometria + cruzamento dossie)
- [ ] Thresholds parametrizaveis por tipo e por processo (pela CAIXA)
- [ ] Dashboard de fraude: taxa de deteccao, falsos positivos, distribuicao de scores

### Fase 3 — Avancado (IA + Deepfake + Escala)

- [ ] Deepfake detection em selfies
- [ ] Deteccao de identidade sintetica
- [ ] Consultas a bases privadas (Serasa, SEFAZ para NF-e)
- [ ] Impressao digital matching (se base disponivel)
- [ ] Modelo ML treinado em historico de fraudes reais da CAIXA
- [ ] Anti-fraude adaptativo (modelo aprende com novos padroes de fraude)
- [ ] Auto-scaling para absorver picos
- [ ] Feedback loop: resultados de Operacao Assistida retroalimentam modelos
- [ ] Metricas de bias/fairness em biometria facial
- [ ] Relatorio mensal de fraudes detectadas por tipo e processo

---

## 17. REFERENCIAS NORMATIVAS

| Documento | Secao | Conteudo Relevante |
|-----------|-------|-------------------|
| Anexo I — TR | 2.4 | Definicao do servico de validacao de autenticidade |
| Anexo I — TR | 2.4.1 | 4 operacoes obrigatorias (padroes graficos, cruzamento, biometria, score) |
| Anexo I — TR | 2.3.2.3 | Extracao de dados como etapa preparatoria NAO remunerada |
| Anexo I — TR | 2.6 | Servico separado de consulta a bases (distinto da validacao) |
| Anexo I — TR | 5.2 | Formula de remuneracao |
| Anexo I — TR | 5.5 | Deducoes por servico incorreto |
| Anexo I — TR | 7.3.5 | Dados exclusivos para servicos contratados |
| Anexo I — TR | 7.12.6 | Responsabilidade por prejuizos |
| Anexo I-A | Definicoes | Avaliacao de autenticidade, score de risco de fraude, cruzamento de dados |
| Anexo I-B | Padrao Tecnologico | Formatos, protocolos, integracoes |
| Anexo I-C | Secao 5 | Volume: 14.418.118 avaliacoes/ano |
| Anexo I-G | Seguranca | LGPD, protecao de dados biometricos |
| Anexo I-H | Filas | SLAs por fila (1h, 18h, 24h) |
