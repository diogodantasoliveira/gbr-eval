# Servico de Tratamento de Arquivo Digital
## Especificacao Completa — Edital BPO CAIXA

**Referencia:** Termo de Referencia, Secao 2.8 | Anexo I-A (Definicoes) | Anexo I-C (Volumetria)
**Ultima atualizacao:** 2026-04-10

---

## 1. DEFINICAO FORMAL

> **Tratamento de arquivo digital** — Arquivo digital contendo imagem de um ou mais documentos fisicos digitalizados, podendo estar disposto em uma unica imagem ou em um documento com multiplas paginas.
>
> — Anexo I-A, Definicoes de Termos

O servico consiste em receber arquivos digitalizados de documentos fisicos e ajusta-los para garantir **qualidade e conformidade**, de modo que possam ser utilizados como insumo para processos de extracao de informacoes por motores OCR, ICR e outros, alem de permitir comparacoes, calculos, validacoes e aplicacao de regras negociais.

**Objetivo central:** Garantir maior eficiencia operacional nos processos internos da CAIXA que manipulam documentos digitalizados.

---

## 2. ESCOPO DETALHADO DO SERVICO

### 2.1 Operacoes Obrigatorias (TR 2.8.2)

O servico de tratamento do arquivo digital consiste em:

| # | Operacao | Descricao Detalhada |
|---|----------|-------------------|
| 1 | **Correcao de posicao** | Endireitar documentos digitalizados que estejam inclinados (deskew) |
| 2 | **Separacao de mosaicos** | Quando ha mais de um documento digitalizado em uma unica imagem, separar cada documento individualmente |
| 3 | **Rotacao** | Corrigir a orientacao do documento (ex: documentos escaneados de cabeca para baixo ou na lateral) |
| 4 | **Remocao de bordas** | Eliminar bordas pretas, sombras ou areas de scanner que nao fazem parte do documento |
| 5 | **Eliminacao de areas nao uteis** | Recortar a area util do documento, removendo qualquer excesso que nao contenha informacao relevante |
| 6 | **Tratamento de mosaicos com classificacao** | Quando houver composicao em mosaico E classificacao definida pela CAIXA, desconsiderar imagens que nao correspondam a tipologia solicitada, tratando-as como areas sobressalentes |
| 7 | **Avaliacao de conformidade** | Avaliar cada documento encaminhado e, caso nao atenda aos requisitos definidos, **recusar a execucao do servico informando o motivo** |
| 8 | **Retorno do arquivo tratado** | Retornar a CAIXA um novo arquivo contendo os documentos tratados e ajustados (rotacao, remocao de bordas, eliminacao de areas sobressalentes), vinculado ao identificador da demanda |
| 9 | **Respeito a extensao de arquivo** | Respeitar a extensao do arquivo especificada pela CAIXA ou, na ausencia de definicao, manter a extensao original |
| 10 | **Documentos multipaginados** | Para documentos com multiplas paginas, atender a solicitacao da CAIXA quanto ao retorno em arquivo unico (.TIFF ou .PDF) ou imagens separadas vinculadas ao mesmo identificador |

### 2.2 Tratamento Especifico para Cheques (TR 2.8.2.1)

Para documentos do tipo **cheque**, o tratamento deve obedecer aos padroes exigidos pelas seguintes normas:

| Norma | Assunto |
|-------|---------|
| **Resolucao CMN n. 5.071/2023** | Normas sobre compensacao de cheques e outros papeis |
| **Circular BACEN n. 3.535/2011** | Procedimentos para a apresentacao, compensacao e liquidacao interbancaria de cheques |
| **Lei n. 7.357/1985** | Lei do Cheque — disposicoes sobre emissao e pagamento de cheques |

---

## 3. DEFINICOES TECNICAS RELACIONADAS

Termos definidos no Anexo I-A diretamente aplicaveis a este servico:

### 3.1 Area Util do Documento
Area da imagem representativa do documento a ser manipulado, contendo os dados para extracao, limitado pelas bordas limites e/ou caracteristicas especificas de cada tipo de documento.

### 3.2 Mosaico
Presenca de mais de um documento digitalizado em uma unica imagem. O servico deve ser capaz de identificar e separar cada documento individualmente.

### 3.3 Recorte de Area Util
Retirada de area da imagem nao relacionada ao documento em analise, encaminhada como excesso, de forma que cada documento possa ser visualizado apenas com sua area util.

### 3.4 Recorte de Imagem
Retirada de area especifica da imagem base utilizada como retorno ou na identificacao da presenca de algum elemento especifico. Exemplos:
- A foto da pessoa em um documento de identificacao
- A area da assinatura em um contrato ou documento financeiro

### 3.5 Extensao de Arquivo
Formato do arquivo computacional a ser transitado entre sistemas. Exemplos: pdf, png, bmp, tiff, etc.

### 3.6 Atributo Extraido
Informacao textual presente em documento, com indicacao da presenca ou ausencia de algum elemento solicitado ou recorte de uma area especifica do documento.

---

## 4. VOLUMETRIA

### 4.1 Volume Anual Estimado

| Metrica | Valor |
|---------|-------|
| **Tratamento do arquivo digital** | **19.659.587 / ano** |
| Media mensal estimada | ~1.638.299 / mes |
| Media diaria estimada (dias uteis) | ~78.638 / dia |
| Media diaria estimada (24x7) | ~53.862 / dia |

### 4.2 Contextualizacao do Volume

O servico de tratamento de arquivo digital e aplicado na **mesma escala** que os servicos de classificacao documental e extracao de atributos (todos com 19.659.587/ano), pois tipicamente todo documento que entra no pipeline passa por tratamento antes de ser classificado e ter seus dados extraidos.

### 4.3 Relacao com Demandas por Processo

O tratamento de arquivo digital e acionado em **todos os processos** que envolvem documentos digitalizados:

| Processo | Volume Anual de Demandas | Documentos Tipicos que Requerem Tratamento |
|----------|-------------------------|-------------------------------------------|
| ONBOARDING FGTS | 6.829.602 | Identificacao, selfie |
| Conta Digital | 4.704.706 | Identificacao, comprovante residencia |
| ONBOARDING | 4.558.404 | Identificacao, documentos diversos |
| Abertura de Conta | 3.510.402 | RG/CNH, comprovante residencia, renda |
| Concessao Habitacional | 1.839.620 | Matricula imovel, laudo avaliacao, IRPF, certidoes |
| Dossie CCA | 1.134.461 | Identificacao, renda, documentos de credito |
| Agronegocio | 460.607 | Contratos, certidoes, licenciamento ambiental |
| Garantias Comerciais PJ | 382.962 | Matricula, certidoes, contrato social |
| Concessao Comercial PJ | 325.802 | Contrato social, matricula, parecer juridico |
| Garantia Habitacional CIP | 278.657 | Apolice, matricula, laudo, contrato |
| Programa Pe de Meia | 97.293 | Identificacao, selfie |

### 4.4 Complexidade por Tipo de Documento

| Complexidade do Tratamento | Tipos de Documento | Paginas | Desafios Tipicos |
|----------------------------|-------------------|---------|-----------------|
| **BAIXA** | Selfie, RG/CNH, IPTU, Nota Fiscal, Residencia | 1-3 | Rotacao, bordas |
| **MEDIA** | Certidoes, IRPF, Contrato Social, Holerites | 3-20 | Mosaico, multipaginas, qualidade variavel |
| **ALTA** | Laudo de Avaliacao, Contrato Habitacional, Licenciamento Ambiental | 15-40 | Mosaico complexo, scans de baixa qualidade, multiplas paginas com orientacoes distintas |

---

## 5. REGRAS DE NEGOCIO

### 5.1 Quando o Servico e Acionado

O tratamento de arquivo digital e acionado como **etapa preparatoria** dentro da jornada de processamento de documentos. Ele pode ser:

1. **Servico autonomo** — quando a CAIXA solicita especificamente o tratamento como produto final (ex: correcao de scans para arquivo)
2. **Etapa do pipeline** — quando precede a classificacao, extracao ou validacao de autenticidade

### 5.2 Remuneracao

- O servico de tratamento de arquivo digital **possui valor unitario proprio** na tabela de precos da proposta comercial (Anexo II)
- Volume anual para precificacao: **19.659.587 unidades**
- A remuneracao e por **quantidade de servicos efetivamente executados**

### 5.3 Recusa de Documentos

A contratada **pode e deve recusar** documentos que nao atendam aos requisitos definidos, informando o motivo da recusa. Isto gera o servico de **"Rejeicao de documento"** (787.170/ano) ou **"Rejeicao de dossie"** (1.467.493/ano), que tambem possuem remuneracao propria.

Motivos de recusa incluem:
- Arquivo corrompido ou ilegivel
- Formato nao suportado ou fora dos padroes tecnologicos
- Impossibilidade de leitura por mecanismos automatizados ou por operador humano
- Documento fora dos padroes tecnologicos estabelecidos

### 5.4 Inconsistencias Documentais (TR 5.4.3)

Consideram-se inconsistencias nos documentos digitais aqueles arquivos recepcionados e recusados por estarem:
- Fora dos padroes tecnologicos estabelecidos
- Impossibilitados de leitura ou interpretacao, seja por mecanismos automatizados, seja por operador humano

### 5.5 Vinculacao ao Identificador

Todo arquivo tratado deve ser retornado **vinculado ao identificador da demanda** original. Isto e critico para rastreabilidade e para que os servicos subsequentes (classificacao, extracao, validacao) possam operar sobre o documento correto.

---

## 6. FORMATOS DE ENTRADA E SAIDA

### 6.1 Formatos de Entrada Esperados

Com base nos padroes tecnologicos (Anexo I-B) e na definicao do servico:

| Formato | Extensao | Observacao |
|---------|----------|-----------|
| PDF | .pdf | Formato predominante para documentos multipaginados |
| TIFF | .tiff, .tif | Formato de alta qualidade para imagens escaneadas |
| PNG | .png | Imagens individuais |
| BMP | .bmp | Imagens bitmap (legado) |
| JPEG | .jpg, .jpeg | Fotos, selfies, capturas de celular |

### 6.2 Formatos de Saida

| Formato | Quando Usar |
|---------|------------|
| **TIFF** | Quando especificado pela CAIXA para documentos multipaginados em arquivo unico |
| **PDF** | Quando especificado pela CAIXA para documentos multipaginados em arquivo unico |
| **Imagens separadas** | Quando a CAIXA solicitar paginas individuais, vinculadas ao mesmo identificador |
| **Extensao original** | Na ausencia de especificacao pela CAIXA, manter o formato original |

### 6.3 Regra de Ouro

> A extensao do arquivo de saida e **definida pela CAIXA**. Na ausencia de definicao, manter a extensao original. A contratada NAO decide o formato — apenas executa conforme parametrizado.

---

## 7. OPERACOES TECNICAS DETALHADAS

### 7.1 Correcao de Posicao (Deskew)

**O que e:** Corrigir a inclinacao de documentos escaneados que ficaram tortos no scanner.

**Entrada:** Imagem com angulo de inclinacao != 0
**Saida:** Imagem com texto alinhado horizontalmente

**Requisitos tecnicos:**
- Deteccao automatica do angulo de inclinacao
- Rotacao sub-pixel para evitar perda de qualidade
- Preservacao da resolucao original
- Funcionar com documentos de qualquer orientacao de texto

**Cenarios comuns:**
- Documento colocado levemente torto no scanner
- Foto tirada com celular em angulo
- Scan de documento dobrado

---

### 7.2 Separacao de Mosaicos

**O que e:** Identificar e separar multiplos documentos que foram digitalizados juntos em uma unica imagem.

**Entrada:** Uma imagem contendo 2+ documentos (ex: RG frente + verso escaneados juntos)
**Saida:** N imagens individuais, uma por documento identificado

**Requisitos tecnicos:**
- Deteccao de bordas entre documentos
- Separacao sem perda de conteudo nas margens
- Classificacao de qual sub-imagem corresponde a qual documento (quando ha tipologia definida)
- Descarte de areas sobressalentes (imagens que nao correspondem a tipologia solicitada)

**Cenarios comuns:**
- RG frente e verso no mesmo scan
- Multiplos comprovantes em uma unica pagina
- Holerites de meses diferentes digitalizados juntos
- CNH + comprovante de residencia na mesma folha

---

### 7.3 Rotacao

**O que e:** Corrigir a orientacao do documento para a posicao correta de leitura.

**Entrada:** Documento em orientacao incorreta (90, 180, 270 graus)
**Saida:** Documento na orientacao correta para leitura

**Requisitos tecnicos:**
- Deteccao automatica da orientacao correta
- Rotacao em incrementos de 90 graus (e intermediarios quando necessario)
- Sem perda de qualidade na rotacao
- Funcionar tanto para texto quanto para documentos com fotos/graficos

**Cenarios comuns:**
- Documento escaneado de cabeca para baixo
- Pagina em modo paisagem quando deveria ser retrato
- Foto de documento tirada com celular na horizontal

---

### 7.4 Remocao de Bordas

**O que e:** Eliminar bordas escuras, sombras de scanner, ou areas de fundo que nao fazem parte do conteudo do documento.

**Entrada:** Imagem com bordas pretas, sombras ou excesso de fundo
**Saida:** Imagem limpa contendo apenas a area util do documento

**Requisitos tecnicos:**
- Deteccao automatica de bordas nao-documentais
- Preservacao total do conteudo do documento
- Sem corte acidental de informacoes nas margens
- Tratamento de sombras parciais (ex: lombada de livro)

**Cenarios comuns:**
- Bordas pretas de scanner flatbed
- Sombras nas laterais de documentos grossos
- Excesso de mesa/fundo visivel na digitalizacao
- Documentos menores que a area do scanner

---

### 7.5 Recorte de Area Util

**O que e:** Isolar apenas a area do documento que contem informacao relevante, removendo todo o excesso.

**Entrada:** Imagem com areas inuteis ao redor do conteudo principal
**Saida:** Imagem recortada contendo apenas a area util

**Requisitos tecnicos:**
- Identificacao precisa dos limites do documento
- Recorte sem perda de margens internas do documento
- Adaptacao a diferentes tamanhos e formatos de documentos
- Considerar as bordas limites e/ou caracteristicas especificas de cada tipo de documento

---

### 7.6 Recorte de Imagem Especifica

**O que e:** Extrair uma regiao especifica de dentro do documento para uso como retorno ou verificacao.

**Entrada:** Documento completo + coordenadas ou tipo de regiao solicitada
**Saida:** Recorte da area especifica

**Exemplos de uso:**
- Foto 3x4 extraida de um RG ou CNH
- Area de assinatura extraida de um contrato
- Carimbo ou selo extraido de uma certidao
- Quadro societario extraido de contrato social

---

## 8. TRATAMENTO ESPECIAL PARA CHEQUES

### 8.1 Normas Aplicaveis

O tratamento de cheques possui regulamentacao especifica do sistema financeiro:

**Resolucao CMN n. 5.071/2023:**
- Define padroes para compensacao de cheques
- Estabelece requisitos de imagem para trafego interbancario
- Define resolucao minima e formato

**Circular BACEN n. 3.535/2011:**
- Procedimentos para apresentacao e compensacao interbancaria
- Requisitos de captura de imagem
- Padroes de qualidade da digitalizacao

**Lei n. 7.357/1985 (Lei do Cheque):**
- Requisitos legais de validade do cheque
- Elementos obrigatorios que devem estar visiveis na imagem tratada

### 8.2 Requisitos Especificos para Cheques

| Requisito | Descricao |
|-----------|----------|
| Resolucao | Atender resolucao minima definida pelo BACEN para compensacao |
| Frente e verso | Captura e tratamento de ambos os lados |
| Legibilidade | Todos os campos obrigatorios do cheque devem estar legiveis apos tratamento |
| Integridade | A imagem tratada deve preservar todos os elementos de seguranca visiveis |
| Conformidade | O arquivo de saida deve estar em conformidade com os padroes de trafego interbancario |

---

## 9. SLAs E QUALIDADE

### 9.1 Niveis de Servico por Fila

O servico de tratamento de arquivo digital esta inserido nas filas de atendimento e herda os SLAs da fila em que a demanda esta alocada:

| Fila | SLA (horas) | Meta NS | Meta NQ |
|------|------------|---------|---------|
| Programa Pe de Meia | **1h** | 95% | 90% |
| Abertura Conta Agencia/CCA | **1h** | 95% | 90% |
| Garantias Comerciais PJ | **18h** | 95% | 90% |
| Dossie CCA-Comercial/Consignado | **18h** | 95% | 90% |
| Concessao Comercial PJ | **18h** | 95% | 90% |
| Demais filas | **24h** | 95% | 90% |

### 9.2 Disponibilidade

| Metrica | Valor |
|---------|-------|
| Disponibilidade minima | **99,5%** |
| Regime de operacao | **24x7x365** |
| Monitoramento | Continuo com alertas automaticos |

### 9.3 Criterios de Qualidade

O tratamento e considerado **conforme** quando:

- [ ] A imagem de saida esta na orientacao correta
- [ ] As bordas inuteis foram removidas sem perda de conteudo
- [ ] Os mosaicos foram corretamente separados
- [ ] A inclinacao foi corrigida
- [ ] A extensao de arquivo respeita a especificacao da CAIXA
- [ ] O arquivo de saida esta vinculado ao identificador correto da demanda
- [ ] Para documentos multipaginados, o formato de retorno esta conforme solicitacao (arquivo unico ou imagens separadas)
- [ ] Para cheques, as normas regulatorias foram atendidas

### 9.4 Penalidades

| Tipo | Formula | Descricao |
|------|---------|----------|
| Deducao por indisponibilidade (DI) | `DI = VSETF x FAIDS` | Aplicada quando o servico fica indisponivel |
| Deducao por servico incorreto (VDSI) | `VDSI = 0,05% x SI x VSETF` | Para cada tratamento inconforme identificado |
| Teto de deducoes | **10% do VSETF** | Limite maximo do somatorio de deducoes |

---

## 10. RELACAO COM OUTROS SERVICOS

### 10.1 Posicao no Pipeline de Processamento

```
[Documento digitalizado recebido]
         |
         v
  +-------------------------------+
  | TRATAMENTO DE ARQUIVO DIGITAL |  <-- ESTE SERVICO
  | (correcao, rotacao, recorte)  |
  +-------------------------------+
         |
         v
  +-------------------------------+
  | CLASSIFICACAO DOCUMENTAL      |
  | (identificar tipo do doc)     |
  +-------------------------------+
         |
         v
  +-------------------------------+
  | EXTRACAO DE DADOS             |
  | (OCR/ICR dos atributos)       |
  +-------------------------------+
         |
         v
  +-------------------------------+
  | VALIDACAO DE AUTENTICIDADE    |
  | (score de fraude)             |
  +-------------------------------+
         |
         v
  +-------------------------------+
  | APLICACAO DE REGRAS NEGOCIAIS |
  | (simples e compostas)         |
  +-------------------------------+
         |
         v
  [Resultado retornado a CAIXA]
```

### 10.2 Dependencias Upstream (quem envia para este servico)

| Origem | Descricao |
|--------|----------|
| Canais CAIXA (WEB/APP) | Documentos digitalizados pelos clientes ou agencias |
| Portal da CONTRATADA | Documentos recebidos via integracao |
| Operacao Assistida | Documentos recebidos via atendimento ao cliente |

### 10.3 Dependencias Downstream (quem consome o resultado)

| Destino | Por que precisa do tratamento |
|---------|------------------------------|
| **Classificacao documental** | Precisa de imagem limpa e orientada para classificar corretamente |
| **Extracao de dados (OCR/ICR)** | Qualidade da imagem impacta diretamente a acuracia do OCR |
| **Validacao de autenticidade** | Precisa de imagem fiel ao original para deteccao de fraude |
| **Arquivamento** | Documentos tratados sao armazenados por ate 90 dias |
| **Recorte de imagem** | Areas especificas (foto, assinatura) dependem do tratamento previo |

### 10.4 Impacto na Cadeia

> **O tratamento de arquivo digital e o PRIMEIRO servico da cadeia.** Se ele falha ou entrega imagens de baixa qualidade, TODOS os servicos subsequentes sao impactados — OCR perde acuracia, classificacao erra, validacao de autenticidade gera falsos positivos/negativos.

---

## 11. REQUISITOS TECNICOS DE IMPLEMENTACAO

### 11.1 Tecnologias Necessarias

| Capacidade | Tecnologia / Abordagem |
|-----------|----------------------|
| Deteccao de inclinacao | Algoritmos de Hough Transform, projecao de histograma |
| Rotacao de imagem | Rotacao bilinear/bicubica com preservacao de qualidade |
| Deteccao de bordas | Edge detection (Canny, Sobel), contour detection |
| Separacao de mosaico | Object detection, segmentacao semantica |
| Deteccao de orientacao | Deep learning (CNN) para classificacao de orientacao |
| Recorte inteligente | Deteccao de contorno do documento (document boundary detection) |
| Binarizacao | Algoritmos adaptativos (Otsu, Sauvola) para melhoria de contraste |
| Denoising | Filtros de reducao de ruido para scans de baixa qualidade |

### 11.2 Padroes Tecnologicos Obrigatorios (Anexo I-B)

| Item | Especificacao |
|------|--------------|
| Integracao online | Web Services SOAP e REST |
| Formatos de dados | JSON, XML |
| Protocolo | HTTPS (TLS 1.3) |
| API | Segura e documentada |
| Idioma | Portugues do Brasil em todas as interfaces e logs |

### 11.3 Requisitos de Infraestrutura

| Requisito | Especificacao |
|-----------|--------------|
| Ambiente | Homologacao + Producao segregados |
| Disponibilidade | 99,5% — 24x7x365 |
| Escalabilidade | Absorver picos sem degradacao |
| Logs | Estruturados com document_id, operacao, latencia, status |
| Trilha de auditoria | Tipo de evento, autor, data/hora, endereco logico |
| Monitoramento | Alertas automaticos de indisponibilidade |

---

## 12. CENARIOS DE TESTE E VALIDACAO

### 12.1 Cenarios Minimos para Homologacao

| # | Cenario | Entrada | Resultado Esperado |
|---|---------|---------|-------------------|
| 1 | Documento reto | PDF de 1 pagina, sem inclinacao | Retorno identico ao original |
| 2 | Documento inclinado | Imagem com 5-15 graus de inclinacao | Imagem corrigida, texto horizontal |
| 3 | Documento rotacionado 180 | PDF de cabeca para baixo | PDF orientado corretamente |
| 4 | Documento com bordas pretas | Scan com bordas escuras laterais | Imagem limpa sem bordas |
| 5 | Mosaico 2 documentos | RG frente + verso em uma imagem | 2 imagens separadas |
| 6 | Mosaico com classificacao | 3 docs em 1 imagem, tipologia pede apenas 1 | 1 imagem do tipo solicitado, 2 descartadas |
| 7 | Multipaginas para TIFF | PDF de 5 paginas | 1 arquivo TIFF multipaginado |
| 8 | Multipaginas para separadas | PDF de 5 paginas | 5 imagens individuais vinculadas ao mesmo ID |
| 9 | Formato preservado | PNG sem especificacao de formato de saida | PNG mantido |
| 10 | Cheque | Imagem de cheque | Tratamento conforme CMN 5.071/2023 |
| 11 | Documento ilegivel | Scan completamente preto/branco | Recusa com motivo informado |
| 12 | Scan de baixa qualidade | Documento muito escuro ou borrado | Tratamento com melhoria de qualidade ou recusa justificada |
| 13 | Documento com foto | CNH com foto 3x4 | Possibilidade de extrair area da foto como recorte |
| 14 | Volume de pico | 1000 documentos simultaneos | Processamento sem degradacao de SLA |

### 12.2 Metricas de Aceitacao

| Metrica | Valor Minimo |
|---------|-------------|
| Taxa de acerto na correcao de inclinacao | >= 95% |
| Taxa de acerto na separacao de mosaico | >= 95% |
| Taxa de acerto na deteccao de orientacao | >= 98% |
| Tempo de processamento por documento (simples) | Compativel com SLA da fila |
| Taxa de falsos positivos na recusa | < 2% |
| Preservacao de qualidade (resolucao de saida vs entrada) | >= 95% |

---

## 13. PRECIFICACAO

### 13.1 Estrutura de Preco

| Item | Valor |
|------|-------|
| **Nome do servico na proposta** | Tratamento do arquivo digital |
| **Quantidade anual para precificacao** | 19.659.587 |
| **Unidade de cobranca** | Por documento tratado |
| **Formula de remuneracao** | Quantidade executada x Valor Unitario |

### 13.2 Componentes de Custo a Considerar

| Componente | Descricao |
|-----------|----------|
| Infraestrutura de processamento | GPU/CPU para algoritmos de imagem |
| Armazenamento temporario | Buffer de entrada e saida dos arquivos |
| Licencas de software | Bibliotecas de processamento de imagem |
| Mao de obra tecnica | Desenvolvimento e sustentacao dos algoritmos |
| Monitoramento | Ferramentas de observabilidade |
| Redundancia | Infra de contingencia para garantir 99,5% |

### 13.3 Alerta de Precificacao

> O tratamento de arquivo digital tem **volume identico** ao da classificacao documental e extracao de dados (19,6M/ano). Isso sugere que a CAIXA espera que **todo documento passe por tratamento**. Precificar de forma competitiva neste servico e critico pois ele impacta o custo total em larga escala.

---

## 14. RISCOS ESPECIFICOS DO SERVICO

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| 1 | Scans de baixa qualidade em volume | Alta | Aumento de rejeicoes e retrabalho | Algoritmos adaptativos de melhoria de imagem |
| 2 | Mosaicos complexos (3+ documentos) | Media | Separacao incorreta impacta toda a cadeia | ML especializado em document detection |
| 3 | Formatos nao padronizados recebidos | Media | Rejeicao ou erro no processamento | Suporte amplo a formatos + validacao na entrada |
| 4 | SLA de 1h para filas prioritarias | Alta | Pouco tempo para tratamento + servicos subsequentes | Pipeline otimizado, processamento em streaming |
| 5 | Variacao sazonal de volume | Media | Infraestrutura sub ou superdimensionada | Auto-scaling com monitoramento preditivo |
| 6 | Mudanca na tipologia de documentos pela CAIXA | Media | Modelos de mosaico/classificacao desatualizados | Retraining rapido, modelos parametrizaveis |
| 7 | Falha no tratamento gera efeito cascata | Alta | OCR, classificacao e validacao erram | QA automatizado pos-tratamento antes de enviar downstream |

---

## 15. CHECKLIST DE IMPLEMENTACAO

### Fase 1 — MVP

- [ ] Correcao de inclinacao (deskew) automatica
- [ ] Rotacao automatica (0/90/180/270 graus)
- [ ] Remocao de bordas pretas
- [ ] Recorte de area util basico
- [ ] Suporte a PDF, TIFF, PNG, JPEG
- [ ] Retorno vinculado ao identificador da demanda
- [ ] API REST com entrada e saida documentadas
- [ ] Logs estruturados

### Fase 2 — Completo

- [ ] Separacao de mosaicos (2+ documentos)
- [ ] Classificacao de sub-imagens em mosaico
- [ ] Descarte de areas sobressalentes por tipologia
- [ ] Retorno em arquivo unico (TIFF/PDF) ou imagens separadas (parametrizavel)
- [ ] Preservacao ou conversao de extensao de arquivo conforme parametro
- [ ] Validacao de conformidade e recusa com motivo
- [ ] Recorte de imagem especifica (foto, assinatura)
- [ ] Tratamento de documentos multipaginados

### Fase 3 — Cheques + Otimizacao

- [ ] Tratamento especifico para cheques (CMN 5.071/2023)
- [ ] Conformidade com Circular BACEN 3.535/2011
- [ ] Melhoria de qualidade adaptativa (denoising, binarizacao)
- [ ] Auto-scaling para absorver picos
- [ ] Dashboard de monitoramento de qualidade
- [ ] Metricas de acuracia por tipo de operacao

---

## 16. REFERENCIAS NORMATIVAS

| Documento | Secao | Conteudo Relevante |
|-----------|-------|-------------------|
| Anexo I — TR | 2.8 | Definicao completa do servico |
| Anexo I — TR | 2.8.2 | Operacoes detalhadas |
| Anexo I — TR | 2.8.2.1 | Tratamento de cheques |
| Anexo I — TR | 2.9 | Arquivamento (servico subsequente) |
| Anexo I — TR | 5.2 | Formula de remuneracao |
| Anexo I — TR | 5.4.3 | Inconsistencias documentais |
| Anexo I — TR | 5.5 | Deducoes por servico incorreto |
| Anexo I-A | Definicoes | Area util, mosaico, recorte, extensao de arquivo |
| Anexo I-B | Padrao Tecnologico | Formatos, protocolos, integracoes |
| Anexo I-C | Volumetria | 19.659.587 tratamentos/ano |
| Anexo I-H | Filas | SLAs por fila (1h, 18h, 24h) |
| Resolucao CMN 5.071/2023 | — | Compensacao de cheques |
| Circular BACEN 3.535/2011 | — | Apresentacao interbancaria de cheques |
| Lei 7.357/1985 | — | Lei do Cheque |
