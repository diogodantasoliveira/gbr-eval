# Analise do Edital BPO CAIXA — Termo de Referencia
## GarantiaBR — Documento de Produto

**Data de analise:** 2026-04-10
**Fonte:** Anexos I (A-H), II e II-A do Edital de Contratacao de Servicos BPO — Caixa Economica Federal

---

## SUMARIO EXECUTIVO

A CAIXA pretende contratar **ate 3 empresas simultaneamente** para prestacao de servicos de front, middle e backoffice em regime de outsourcing (BPO). O modelo e 100% baseado em performance — remuneracao variavel conforme niveis de servico e qualidade. Criterio de julgamento: **menor preco** atendidos requisitos tecnicos. A CAIXA tem prerrogativa exclusiva de redistribuir volumes entre contratadas a qualquer momento, baseado em desempenho.

**Volume anual estimado:** ~25,9 milhoes de demandas e ~480,9 milhoes de analises de regras.

**Vigencia:** 24 meses, renovavel.

---

## 1. OBJETO DA CONTRATACAO

### 1.1 Escopo Geral

Servicos de front, middle e backoffice em regime de outsourcing (BPO), incluindo:

| Servico | Descricao |
|---------|-----------|
| Extracao de dados | Extrair atributos conforme tipologia do documento, respeitando janelas temporais |
| Validacao de autenticidade | Verificacao automatizada de padroes graficos, cruzamento de dados, biometria facial/digital, score de fraude |
| Classificacao documental | Identificar tipo de documento conforme tipologia definida pela CAIXA |
| Consulta em bases externas | Consultas em bases publicas (gratuitas) e privadas (custo da contratada) |
| Regras negociais simples | Unico criterio de validacao isolado (ex: idade >= 18, data de emissao em 90 dias) |
| Regras negociais compostas | Multiplos criterios encadeados (ex: analise de contrato social, margem consignavel, onus em matricula) |
| Tratamento de arquivo digital | Correcao de posicao, separacao de mosaicos, rotacao, remocao de bordas, recorte |
| Arquivamento temporario | Manter arquivos por ate 90 dias, depois eliminacao segura (LGPD) |
| Jornadas automatizadas | Parametrizacao dinamica com IA, low-code/no-code, linguagem natural |
| Operacao assistida | Suporte humano e/ou tecnologico via e-mail, portal, SMS, WhatsApp, chatbot |

### 1.2 Pontos Criticos para Produto

- **Extracao so e remunerada quando e produto final.** Quando e etapa preparatoria para outros servicos, NAO ha remuneracao especifica.
- **Regras simples vs. compostas tem tarifacao diferenciada** — precificar corretamente.
- **Operacao assistida** e remunerada por quantidade de acionamentos ao cliente.
- **Jornadas automatizadas** exigem que a CAIXA consiga criar/editar fluxos SEM intervencao tecnica (low-code/no-code obrigatorio).
- **Vedacao:** NAO e permitido fornecimento de solucao tecnologica como produto, cessao de uso, aquisicao ou licenciamento de software. E exclusivamente SERVICO.

---

## 2. VOLUMETRIA E ESCALA

### 2.1 Volume Anual por Processo (Demandas)

| Processo | Volume Anual | % do Total |
|----------|-------------|------------|
| ONBOARDING FGTS | 6.829.602 | 26,4% |
| Conta Digital | 4.704.706 | 18,2% |
| ONBOARDING | 4.558.404 | 17,6% |
| Abertura de Conta Agencia/CCA | 3.510.402 | 13,6% |
| Concessao Habitacional | 1.839.620 | 7,1% |
| Outros Processos | 1.777.448 | 6,9% |
| Dossie CCA – Comercial/Consignado | 1.134.461 | 4,4% |
| Agronegocio | 460.607 | 1,8% |
| Garantias Comerciais PJ | 382.962 | 1,5% |
| Concessao Comercial PJ | 325.802 | 1,3% |
| Garantia Habitacional CIP | 278.657 | 1,1% |
| Programa Pe de Meia | 97.293 | 0,4% |
| **TOTAL** | **~25.900.962** | **100%** |

### 2.2 Volume Anual por Servico

| Servico | Quantidade Anual |
|---------|-----------------|
| Validacao de regras simples | 96.151.084 |
| Operacao Assistida | 64.920.591 |
| Tratamento do arquivo digital | 19.659.587 |
| Classificacao documental | 19.659.587 |
| Extracao de atributos | 19.659.587 |
| Avaliacao de autenticidade | 14.418.118 |
| Portal web e comunicacao cliente | 6.410.499 |
| Avaliacao de Demandas | 2.412.466 |
| Validacao de regras compostas | 1.690.623 |
| Rejeicao de dossie | 1.467.493 |
| Rejeicao de documento | 787.170 |
| Validacao documental em fontes externas | 237.988 |
| Disponibilizacao de dados de bases externas | 112.499 |

### 2.3 Analises de Regras (Volume Massivo)

| Tipo | Quantidade Anual |
|------|-----------------|
| Analises com regras simples | 353.792.880 |
| Analises com regras compostas | 127.100.382 |
| **Total de analises** | **~480.893.262** |

### 2.4 Alertas de Volumetria

- Volumetrias sao **estimativas** — NAO configuram consumo minimo garantido.
- Contratada deve absorver **oscilacoes sazonais e picos nao previstos**.
- Horario de pico: **08h as 20h, segunda a sexta** — reforcar estrutura nesse periodo.
- Demandas emergenciais fora do horario de pico tambem devem ser atendidas.
- **Risco de ociosidade e inteiramente da contratada.**

---

## 3. TIPOS DE DOCUMENTOS

### 3.1 Documentos por Complexidade

**Alta complexidade (15-40 paginas):**
- Laudo de Avaliacao do Imovel (15-40 pag.)
- Contrato Habitacional (15-30 pag.)
- Documento de licenciamento ambiental (5-30 pag.)
- Plano de negocios (10-30 pag.)
- Contrato comercial registrado (10-25 pag.)

**Media complexidade (3-20 paginas):**
- Certidao da Matricula Imovel (2-20 pag.)
- IRPF (5-20 pag.)
- Documento constitutivo / Contrato social (5-20 pag.)
- Contrato Comercial (8-20 pag.)
- Parecer Juridico (3-10 pag.)

**Baixa complexidade (1-5 paginas):**
- Identificacao (RG/CNH) (1-2 pag.)
- Certidao de Estado Civil (1 pag.)
- Selfie (1 imagem)
- IPTU (1-3 pag.)
- Nota fiscal ou CRLV (1-2 pag.)
- Residencia (1-3 pag.)

### 3.2 Composicao de Dossies por Linha de Negocio

| Linha de Negocio | Complexidade do Dossie | Documentos Tipicos |
|------------------|----------------------|-------------------|
| Agronegocio | MUITO ALTA (12+ tipos) | Apolice, certidoes, contratos, licenciamento ambiental, registro sanitario, plano de negocios |
| Concessao Habitacional | ALTA (~10 tipos) | Alvara, certidoes, IPTU, IRPF, laudo de avaliacao, registro CREA, renda |
| Garantia Habitacional | ALTA (~7 tipos) | Apolice, matricula imovel, contrato habitacional, laudo, parecer juridico |
| Concessao Comercial PJ | MEDIA | Matricula imovel, contrato social, modelo padrao, nota fiscal, parecer |
| Garantias Comerciais PJ | MEDIA | Matricula, certidoes, contrato, documento constitutivo |
| Abertura de Conta | BAIXA | Certidao estado civil, identificacao, renda, residencia |
| Programa Pe de Meia | MUITO BAIXA | Identificacao, selfie |

---

## 4. FILAS DE ATENDIMENTO E SLAs

### 4.1 Estrutura de Filas

| Prioridade | Fila | SLA (horas) | NSP (min.) | NSQ (min.) | Peso NS | Peso NQ |
|-----------|------|------------|-----------|-----------|---------|---------|
| 1 | Programa Pe de Meia | **1h** | 95% | 90% | 70% | 30% |
| 2 | Abertura Conta Agencia/CCA | **1h** | 95% | 90% | 70% | 30% |
| 3 | Garantias Comerciais PJ | **18h** | 95% | 90% | 70% | 30% |
| 4 | Dossie CCA-Comercial/Consignado | **18h** | 95% | 90% | 70% | 30% |
| 5 | Concessao Comercial PJ | **18h** | 95% | 90% | 70% | 30% |
| 6 | Conta Digital | **24h** | 95% | 90% | 70% | 30% |
| 7 | ONBOARDING | **24h** | 95% | 90% | 70% | 30% |
| 8 | Garantia Habitacional CIP | **24h** | 95% | 90% | 70% | 30% |
| 9 | ONBOARDING FGTS | **24h** | 95% | 90% | 70% | 30% |
| 10 | Concessao Habitacional | **24h** | 95% | 90% | 70% | 30% |
| 11 | Agronegocio | **24h** | 95% | 90% | 70% | 30% |
| 12 | Outros Processos | **24h** | 95% | 90% | 70% | 30% |

### 4.2 Alertas de SLA

- **Filas 1 e 2 (Pe de Meia + Abertura Conta) tem SLA de 1 HORA** — extremamente restritivo. Exige automacao maxima.
- **Filas 3-5 tem SLA de 18 horas** — intermediario.
- **Demais filas tem SLA de 24 horas.**
- Operacao **24x7x365** — todos os dias, sem excecao.
- A CAIXA pode alterar prioridades e SLAs **unilateralmente** a qualquer momento.
- ACP (Adicional de Complexidade e Prioridade) atualmente em **0% para todas as filas** — pode mudar.

### 4.3 Disponibilidade Minima

- **99,5%** de disponibilidade dos servicos.
- Acesso simultaneo sem comprometimento de desempenho.

---

## 5. MODELO DE REMUNERACAO

### 5.1 Formula Principal

```
RMF = (NS/NSP x Peso x VSE + NQ/NQP x Peso x VSE) x (1 + ACP)
```

Onde:
- **NS** = Nivel de Servico mensal da Fila (realizado)
- **NSP** = Nivel de Servico Padrao (meta)
- **NQ** = Nivel de Qualidade mensal (realizado)
- **NQP** = Nivel de Qualidade Padrao (meta)
- **VSE** = Valor dos Servicos Executados = Soma(Quantidade x Valor Unitario)
- **ACP** = Adicional de Complexidade e Prioridade (atualmente 0%)
- **Peso** = Ponderacao NS (70%) vs NQ (30%)

### 5.2 Remuneracao Final

```
RF = RTF + RCI - DI - VDSI
```

- **RTF** = Soma de todas as RMF (todas as filas)
- **RCI** = Ressarcimento de Custos Indiretos (registros cartorarios, certidoes, taxas — valor real, sem margem)
- **DI** = Deducao por Indisponibilidade
- **VDSI** = Valor de Deducao de Servicos Incorretos

### 5.3 Implicacoes para Precificacao

- **Remuneracao e 100% variavel** — se NS ou NQ caem abaixo do padrao, remuneracao e proporcionalmente reduzida.
- **Sem consumo minimo garantido** — volume pode variar sem compensacao.
- **Custos indiretos (cartorio, certidoes)** sao ressarcidos pelo valor real, sem margem de lucro.
- **Demandas nao finalizadas:** remuneracao proporcional aos servicos efetivamente executados.
- **Menor preco vence** atendidos os requisitos tecnicos.

---

## 6. PENALIDADES E DEDUCOES

### 6.1 Deducao por Indisponibilidade (DI)

```
DI = Soma(VSETF x FAIDS)
```
- FAIDS = Fator de Ajuste do Indicador de Disponibilidade (definido no Anexo I-B)

### 6.2 Deducao por Servicos Incorretos (VDSI)

```
VDSI = 0,05% x SI x VSETF
```
- Para cada servico inconforme identificado
- **Limite maximo: 10% do VSETF** (teto de penalidade)

### 6.3 Penalidade por Seguranca da Informacao

- **Multa de 10% sobre o faturamento** do mes de ocorrencia do descumprimento de requisitos de seguranca.
- Suspensao temporaria de ate 2 anos em licitacoes.
- Possibilidade de rescisao antecipada do contrato.

### 6.4 Outras Penalidades

- **Glosas** em despesas nao previstas, nao comprovadas ou incompativeis.
- **Transferencia de conhecimento** com nota < 7: reaplicacao sem onus. Descumprimento: multa.
- **Plano de Melhoria** obrigatorio se desempenho abaixo do limite — nao cumprir = sancoes contratuais.
- **Garantia de 90 dias** apos aceite de OS — ajustes sem custo adicional.
- Nao atender niveis minimos = **refazer servico ou restituir horas cobradas**.

---

## 7. REQUISITOS TECNOLOGICOS

### 7.1 Padrao Tecnologico Obrigatorio (Anexo I-B)

**Estacao de Trabalho:**
| Item | Especificacao |
|------|--------------|
| SO | Windows 11 |
| Antivirus | Microsoft Defender |
| Chrome Enterprise | 134.0+ |
| Edge for Business | 136.0+ |
| Firefox ESR | 128.9+ |
| Office | Microsoft 365 |
| PDF | Adobe Acrobat Reader DC |
| Compactador | 7-Zip 24.9 |
| Java | 8.421 |

**Integracoes:**

| Tipo | Tecnologia |
|------|-----------|
| Online Interna | Web Services SOAP, REST, AMQP, IBM WebSphere MQ |
| Online Externa | Web Services SOAP, REST |
| Batch Interna | Transferencia de Arquivos, ETL via Informatica PowerCenter |
| Batch Externa | IBM B2B |
| Transferencia de Arquivos | IBM B2B, IBM Connect:Direct |

**Formatos de Dados:** JSON, XML, Text/Plain, ISO 8583

**Protocolos:** TCP/IP, HTTP, HTTPS

### 7.2 Requisitos de Plataforma

- **IA obrigatoria** para classificacao, extracao e validacao
- **RPA** (Automacao Robotica de Processos)
- **OCR/ICR** para extracao de dados
- **Low-code/No-code** para construcao de fluxos pela CAIXA
- **Parametrizacao via linguagem natural**
- **SaaS permitido** como modelo de disponibilizacao
- **API segura e documentada**
- **Interfaces responsivas** (mobile e desktop)
- **Conformidade WCAG** para acessibilidade
- **Padroes W3C**
- **Tudo em portugues do Brasil** (interfaces, relatorios, manuais)

### 7.3 Integracao com Sistemas CAIXA (UST)

| Tipo | Referencia (UST) | Prazo Alta | Prazo Media | Prazo Baixa |
|------|-----------------|------------|-------------|-------------|
| Integracao com terceiros | 180 UST | 180h | 135h | 36h |
| Integracao com CAIXA | 180 UST | 180h | 135h | 36h |
| Versao evolutiva | 60 UST | 60h | 45h | 12h |

**1 UST = 1 hora de trabalho.** Pagamento por entrega validada, nao por alocacao.

---

## 8. REQUISITOS DE SEGURANCA

### 8.1 Seguranca Geral

- Conformidade com **LGPD** (Lei 13.709/2018)
- CAIXA = **Controladora**, Contratada = **Operadora** de dados pessoais
- Sigilo absoluto — responsabilidade civil e criminal por divulgacao indevida
- **Termo de Responsabilidade de Seguranca da Informacao** assinado por todos
- Treinamento anual minimo de **8 horas** em seguranca da informacao
- Dados usados exclusivamente para servicos contratados
- Eliminacao segura apos 90 dias

### 8.2 Controle de Acesso

- Principio do **menor privilegio**
- **MFA obrigatorio** (biometria, OTP ou push)
- ID exclusivo por usuario, vedado contas genericas
- Revisao de acessos: a cada 2 anos (geral), anual (dados pessoais), trimestral (privilegiados)
- Login e senha inicial por canais separados
- Acesso remoto somente via **VPN com MFA**
- Trilha de auditoria completa (tipo de evento, autor, data/hora, endereco logico)
- Monitoramento em tempo real de acessos privilegiados

### 8.3 Criptografia

| Requisito | Especificacao |
|-----------|--------------|
| Comunicacao | TLS 1.3 (fallback TLS 1.2) com autenticacao mutua |
| Dados em repouso | AES 128 bits (minimo) |
| Chaves (IaaS) | FIPS 140-2 nivel 3 |
| Chaves (PaaS/SaaS) | FIPS 140-2 nivel 2 |
| Certificados | Autoridade Certificadora com selo Web Trust v2.2.1+ |
| SSL Labs | Nota "A" obrigatoria em todas as URLs |
| Cifras obrigatorias | TLS_ECDHE_ECDSA/RSA_WITH_AES_128/256_GCM_SHA256/384 |

### 8.4 Seguranca de Rede

- Firewall (norte-sul, leste-oeste e de aplicacoes)
- Regras: **deny all, permit by exception**
- **IPS** (Intrusion Prevention System) em todos os componentes de gateway
- Solucao **anti-DDoS**
- Proibido protocolo **Bluetooth** para transferencia de dados
- Revisao de regras de firewall: **semestralmente**

### 8.5 Gestao de Vulnerabilidades

- **Security by Design** com analise de codigo automatizada (padroes OWASP)
- **Pentest anual** por terceiro independente, sem custo adicional para a CAIXA
- Gestao continua de vulnerabilidades com prazos de remediacao

### 8.6 Gestao de Incidentes

- Processo de notificacao **24x7**
- Comunicacao a CAIXA dentro do SLA contratual
- Integracao com o **SOC da CAIXA** (Res. BACEN 4.893/2021)
- Relatorio de incidente em **ate 5 dias uteis** da deteccao
- Logs retidos por **5 anos**
- SIEM, FIM, IDS/IPS, UEBA como ferramentas de referencia

### 8.7 Nuvem

- Dados hospedados **em territorio brasileiro** (producao, backup, contingencia)
- Tenant **dedicado e exclusivo** para a CAIXA
- Acesso administrativo via **rede privada**
- BACEN com acesso pleno a contratos, dados, logs e backups
- SOC 2 Tipos 1 e 2 (semestral) para provedores de nuvem

### 8.8 Encerramento de Contrato

- Retencao de dados por ate **180 dias** para migracao
- Exclusao conforme **NIST SP 800-88**
- Certificado de Destruicao de Equipamento Eletronico (CEED)
- Devolucao de materiais confidenciais em **ate 5 dias**

### 8.9 Certificacoes Exigidas

| Certificacao | Aplicabilidade | Periodicidade |
|-------------|---------------|--------------|
| FIPS 140-2 Nivel 3 | IaaS | Anual |
| FIPS 140-2 Nivel 2 | PaaS/SaaS | Anual |
| SOC 2 Tipo 1 e 2 | Provedores de nuvem | Semestral |
| Web Trust v2.2.1+ | Autoridades Certificadoras | Conforme validade |
| Qualys SSL Labs "A" | Todas URLs publicadas | Apos instalacao |
| OWASP | Desenvolvimento seguro | Continuo |
| NIST SP 800-88 | Sanitizacao de midias | No encerramento |

---

## 9. ETAPAS DE ENTREGA E PRAZOS

### 9.1 Cronograma de Implantacao

| Etapa | Objetivo | Prazo |
|-------|---------|-------|
| 1 — Planejamento | Plano de Ativacao aprovado pela CAIXA | 20 dias corridos da assinatura + 10 dias para ajustes |
| 2 — Ativacao | Servicos minimos funcionando + treinamento CAIXA | 20 dias corridos apos aprovacao do Plano |
| 3 — Piloto | Minimo 2 fluxos em ambiente controlado, SLA avaliado | 30 dias corridos apos Etapa 2 |
| 4 — Implementacao Continua | Expansao progressiva, integracoes completas | Progressivo durante todo o contrato |
| 5 — Sustentacao | Operacao 24x7x365, suporte, melhoria continua | Inicia na Etapa 2 e dura todo o contrato |

### 9.2 Prazos Chave

| Marco | Prazo |
|-------|-------|
| Proposta de Plano de Ativacao | 20 dias corridos da assinatura |
| Ajustes no Plano | 10 dias corridos |
| Ativacao dos servicos minimos | 20 dias corridos apos aprovacao do plano |
| Piloto (2 fluxos) | 30 dias corridos apos Etapa 2 |
| Aceite de OS | 1 dia util |
| Inicio de atividades apos aceite | 5 dias uteis |
| Validade da proposta | Minimo 60 dias |
| Implantacao total | Maximo 90 dias corridos |
| Vigencia do contrato | 24 meses (renovavel) |

---

## 10. RELATORIOS OBRIGATORIOS

| Relatorio | Prazo |
|-----------|-------|
| Relatorio de Ocorrencias | Ate 2 horas apos identificacao; atualizacoes a cada hora; consolidado no dia seguinte |
| Relatorio Semanal | Toda segunda-feira (dados de segunda a domingo) |
| Relatorio Mensal de Sustentacao | Ate dia 5 do mes subsequente |
| Relatorio Mensal de Suporte Tecnico | Ate 5o dia util do mes subsequente |
| Relatorio Anual de Riscos Ciberneticos | Anual |
| Indicadores de SI (treinamento, termos, aprovacao) | Anual |
| Relatorios de auditoria de seguranca | Anual |

---

## 11. TRANSFERENCIA DE CONHECIMENTO

- **Ate 4 turmas** de treinamento
- **Minimo 40 horas** por turma
- Via **plataforma online** indicada pela CAIXA
- Para **minimo 10 empregados** da CAIXA por turma
- Prazo: **15 dias corridos** apos solicitacao
- Nota minima de avaliacao: **7** (se inferior, reaplicar sem custo)
- Inclui **certificados de participacao**
- Descumprimento: **multa**
- Manuais em ate **10 dias corridos**; atualizacoes em **2 dias uteis**

---

## 12. PROPOSTA COMERCIAL — ESTRUTURA

### 12.1 Tabela de Precos (Valor Unitario por Servico)

A licitante preenche apenas o **Valor Unitario (R$)**:

| Servico | Quantidade Anual |
|---------|-----------------|
| Tratamento do arquivo digital | 19.659.587 |
| Classificacao documental | 19.659.587 |
| Extracao de atributos | 19.659.587 |
| Avaliacao de autenticidade | 14.418.118 |
| Rejeicao de documento | 787.170 |
| Rejeicao de dossie | 1.467.493 |
| Validacao documental fontes externas | 237.988 |
| Disponibilizacao dados bases externas | 112.499 |
| Validacao de regras simples | 96.151.084 |
| Validacao de regras compostas | 1.690.623 |
| Portal web e comunicacao cliente | 6.410.499 |
| Avaliacao de Demandas | 2.412.466 |
| Operacao Assistida | 64.920.591 |

### 12.2 Composicao de Custos Obrigatoria

**Parte A:** Mao de obra (perfis, quantidades, salarios)
**Parte B:** Encargos sociais (INSS, FGTS, Sistema S, Salario Educacao, SAT, Ferias+1/3, 13o)
**Parte F:** Insumos e infraestrutura (TI, deslocamentos, software, equipamentos)
**Parte H:** Despesas administrativas + lucro
**Parte I:** Tributos (ISS, PIS, COFINS, INSS previdenciario)

> A planilha e um **piso minimo** — a licitante deve incluir TODOS os custos inerentes, mesmo que nao listados.

---

## 13. GLOSSARIO DE TERMOS CHAVE

| Termo | Definicao |
|-------|----------|
| OCR | Reconhecimento optico de caracteres (impresso) |
| ICR | Reconhecimento inteligente de caracteres (manuscrito) |
| GUI | Interface grafica de usuario |
| Area util | Area da imagem com dados relevantes para extracao |
| Atributo extraido | Informacao textual extraida de documento |
| Mosaico | Mais de um documento em uma unica imagem |
| Score de fraude | Metrica de risco de adulteracao/informacoes conflitantes |
| Itens de analise simples | Um unico criterio de validacao |
| Itens de analise compostas | Multiplos criterios encadeados/dependentes |
| Janela temporal | Prazo para execucao do servico em minutos |
| Demanda | Conjunto de servicos a aplicar em documentos conforme fluxo da CAIXA |
| Fila | Conjunto de demandas com especificacoes identicas |
| Jornada de tratamento | Fluxo completo de servicos aplicados a uma demanda |
| UST | Unidade de Servico Tecnico (1 UST = 1 hora) |
| NS | Nivel de Servico (tempo de atendimento em horas) |
| NSP | Nivel de Servico Padrao (meta minima) |
| NSQ | Nivel de Qualidade |
| ACP | Adicional de Complexidade e Prioridade |
| RMF | Remuneracao Mensal da Fila |
| VSE | Valor dos Servicos Executados |

---

## 14. RISCOS E ALERTAS ESTRATEGICOS PARA GARANTIABR

### 14.1 Riscos Operacionais

| # | Risco | Impacto | Mitigacao |
|---|-------|---------|-----------|
| 1 | SLA de 1h para 2 filas (Pe de Meia + Abertura Conta) | Penalidade por atraso | Automacao maxima com IA/OCR; capacidade reserva |
| 2 | Sem consumo minimo garantido | Ociosidade e custo fixo sem receita | Modelo de custos flexivel; equipe escalavel |
| 3 | CAIXA pode redistribuir volume entre 3 contratadas | Perda subita de volume | Manter excelencia operacional para reter volume |
| 4 | Operacao 24x7x365 | Custo de turnos noturnos e feriados | Automacao para reduzir dependencia de humanos |
| 5 | Penalidades acumulativas (DI + VDSI + multa seguranca) | Erosao de margem | Monitoramento proativo de SLAs e qualidade |

### 14.2 Riscos Tecnologicos

| # | Risco | Impacto | Mitigacao |
|---|-------|---------|-----------|
| 1 | Integracoes IBM (WebSphere MQ, Connect:Direct, B2B) | Custo de licenciamento e expertise IBM | Avaliar custos e capacitacao da equipe |
| 2 | Exigencia de TLS 1.3, FIPS 140-2, nota "A" SSL Labs | Investimento em infra de seguranca | Auditoria preventiva de criptografia |
| 3 | Low-code/no-code com linguagem natural | Desenvolvimento de plataforma proprietaria | Avaliar build vs. buy |
| 4 | ETL via Informatica PowerCenter | Licenciamento e expertise especifica | Parcerias tecnicas |
| 5 | Pentest anual obrigatorio | Custo recorrente | Orcamentar desde a proposta |

### 14.3 Riscos Contratuais

| # | Risco | Impacto | Mitigacao |
|---|-------|---------|-----------|
| 1 | CAIXA altera prioridades/SLAs unilateralmente | Necessidade de adaptacao rapida (10 dias) | Arquitetura flexivel e equipe polivalente |
| 2 | Multa de 10% faturamento por falha de seguranca | Impacto financeiro severo | Investimento robusto em seguranca |
| 3 | Propriedade intelectual da documentacao e da CAIXA | Sem reutilizacao em outros clientes | Focar em know-how operacional |
| 4 | Garantia de 90 dias apos aceite de OS | Custo de retrabalho | QA rigoroso antes de entregar |
| 5 | Melhoria continua obrigatoria sem reajuste de preco | Investimento sem retorno direto | Embutir na precificacao inicial |

---

## 15. CHECKLIST DE PRODUTO — O QUE ENTREGAR

### Capacidades Obrigatorias (Dia 1)

- [ ] Plataforma SaaS de processamento de documentos (front, middle, back)
- [ ] OCR/ICR para extracao de dados de todos os 32+ tipos documentais
- [ ] Classificacao documental automatica
- [ ] Validacao de autenticidade com score de fraude
- [ ] Motor de regras simples e compostas
- [ ] Tratamento de imagem (deskew, binarize, recorte, separacao de mosaico)
- [ ] Arquivamento temporario (90 dias) com eliminacao segura
- [ ] API segura e documentada (REST + SOAP)
- [ ] Integracao via AMQP, IBM WebSphere MQ
- [ ] Formatos: JSON, XML, Text/Plain, ISO 8583

### Capacidades de Automacao

- [ ] Jornadas automatizadas com IA
- [ ] Low-code/no-code para criacao de fluxos pela CAIXA
- [ ] Parametrizacao via linguagem natural
- [ ] RPA para processos repetitivos

### Operacao Assistida

- [ ] Canais: e-mail, portal, SMS, WhatsApp, chatbot
- [ ] Registro completo de todas as etapas (logs, trilha de auditoria)
- [ ] Mecanismos de avaliacao de qualidade pelo cliente
- [ ] Atendimento acessivel e inclusivo

### Interface e Experiencia

- [ ] GUI responsiva (mobile + desktop)
- [ ] Conformidade WCAG (acessibilidade)
- [ ] Identidade visual institucional da CAIXA
- [ ] Tudo em portugues do Brasil
- [ ] Suporte a leitores de tela e navegacao por teclado

### Monitoramento e Governanca

- [ ] Dashboard de acompanhamento em tempo real
- [ ] Logs estruturados com engine, document_id, latency, status
- [ ] Alertas automaticos
- [ ] Disponibilidade 99,5% — 24x7x365
- [ ] Relatorios: ocorrencia (2h), semanal, mensal, anual

### Seguranca

- [ ] MFA para todos os acessos
- [ ] TLS 1.3 com autenticacao mutua
- [ ] AES 128 bits minimo para dados em repouso
- [ ] Nota "A" no Qualys SSL Labs
- [ ] Firewall + IPS + anti-DDoS
- [ ] SIEM integrado ao SOC da CAIXA
- [ ] Pentest anual
- [ ] Dados no Brasil
- [ ] LGPD compliance total

---

## 16. PROXIMOS PASSOS RECOMENDADOS

1. **Mapear capacidades atuais da GarantiaBR** contra o checklist da secao 15.
2. **Avaliar gaps tecnologicos** — especialmente integracoes IBM e low-code/no-code.
3. **Modelar custos** usando a planilha do Anexo II-A, considerando todos os cenarios de volume.
4. **Definir estrategia de precificacao** — menor preco vence, mas remuneracao e variavel.
5. **Avaliar possibilidade de consorcio** para complementar capacidades.
6. **Iniciar processo de certificacoes** de seguranca (FIPS, SOC 2) se nao possuir.
7. **Preparar ambiente de homologacao** para a amostra tecnica na fase de julgamento.
8. **Montar equipe de proposta** com produto, engenharia, seguranca, financeiro e juridico.
