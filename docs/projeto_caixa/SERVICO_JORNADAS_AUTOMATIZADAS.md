# Servico de Criacao e Gestao de Jornadas Automatizadas
## Especificacao Completa — Edital BPO CAIXA

**Referencia:** Termo de Referencia, Secao 2.10 | Anexo I-A (Definicoes) | Anexo I-B (Padrao Tecnologico) | Anexo I-D (Execucao)
**Ultima atualizacao:** 2026-04-10

---

## 1. DEFINICAO E OBJETIVO

> O servico tem como objetivo disponibilizar uma **solucao integrada** para parametrizacao de fluxos, execucao e gestao de demandas, documentos e dados, garantindo uma **jornada completa e automatizada** para a CONTRATANTE. Trata-se de um **servico transversal** aos demais previstos neste Termo.
>
> — TR 2.10.1

### 1.1 Definicoes Relacionadas (Anexo I-A)

> **Jornada de tratamento** — E o conjunto de servicos a serem aplicados a demanda para obtencao de resultado conforme fluxo definido pela CAIXA.
>
> **Demanda** — Conjunto de servicos a serem aplicados a um ou mais documentos para obtencao de resultado conforme fluxo definido pela CAIXA.
>
> **Filas** — Conjunto estruturado de demandas com especificacoes identicas, vinculadas a um mesmo processo, mantidas em espera para tratamento sequencial ou priorizado, de acordo com parametros operacionais, regras de negocio e niveis de servico previamente acordados.

**Objetivo central:** Fornecer a CAIXA uma **plataforma de orquestracao** que permite criar, configurar, executar e monitorar fluxos de processamento de documentos de forma autonoma — sem depender da equipe tecnica da CONTRATADA para cada alteracao ou novo fluxo.

**Natureza transversal:** Este servico NAO e um pipeline isolado — ele e a **camada de orquestracao** que conecta e coordena todos os demais servicos (tratamento, classificacao, extracao, validacao, regras, consultas, operacao assistida) em jornadas end-to-end configuradas pela CAIXA.

---

## 2. ESCOPO DETALHADO DO SERVICO

### 2.1 Sete Capacidades Obrigatorias (TR 2.10.2)

| # | Capacidade | Descricao Completa do TR | Natureza |
|---|-----------|------------------------|----------|
| 1 | **Parametrizacao dinamica** | Definicao de itens de analise/checklist, ordem de execucao das atividades, etapas da jornada, construcao de formularios e captura de documentos | Configuracao |
| 2 | **Automacao Inteligente** | Aplicacao de tecnologias avancadas, incluindo IA, para classificacao, extracao e validacao de informacoes, assegurando precisao e aderencia as regras estabelecidas. A automacao deve permitir **parametrizacao via linguagem natural**, ajuste de parametros e evolucao continua dos fluxos, **sem necessidade de conhecimento tecnico** por parte dos usuarios | Tecnologia |
| 3 | **Autonomia da CONTRATANTE** | A solucao deve permitir criacao, edicao e parametrizacao de fluxos **sem intervencao tecnica da CONTRATADA** | Governanca |
| 4 | **Ferramentas low-code/no-code** | Disponibilizacao de recursos que facilitem a construcao e manutencao de fluxos pela CONTRATANTE | Ferramenta |
| 5 | **Interfaces interativas** | Disponibilizacao de interface para insercao de dados e/ou documentos por publico interno ou externo, com retorno dos resultados das atividades realizadas | Interface |
| 6 | **Integracao com sistemas** | Responsabilidade da CONTRATADA pela criacao e gestao das interfaces necessarias a troca de dados, garantindo interoperabilidade e seguranca conforme padroes tecnicos da CAIXA | Integracao |
| 7 | **Governanca e curadoria** | Monitoramento e revisao dos resultados gerados pelos processos automatizados, assegurando conformidade, qualidade e aderencia as regras do projeto | Controle |

### 2.2 Interpretacao Consolidada

Este servico exige que a contratada forneca uma **plataforma completa de BPM (Business Process Management) com IA embutida**, que permita a CAIXA:

| O que a CAIXA deve poder fazer | Sem depender de |
|-------------------------------|----------------|
| Criar um novo fluxo de processamento | Equipe tecnica da contratada |
| Editar etapas de um fluxo existente | Deploy tecnico |
| Definir checklist de regras por fluxo | Desenvolvimento de codigo |
| Criar formularios para captura de dados | Designer/desenvolvedor |
| Ajustar parametros de IA (via linguagem natural) | Data scientist |
| Monitorar resultados em tempo real | Relatorios manuais |
| Corrigir fluxos com baixa performance | Ticket de suporte |

---

## 3. NATUREZA TRANSVERSAL — O QUE SIGNIFICA

### 3.1 Este Servico NAO e um Pipeline Isolado

Diferente dos demais servicos (tratamento, classificacao, extracao, etc.) que sao **etapas** do processamento, o servico de jornadas automatizadas e a **camada de orquestracao** que:

```
+==================================================================+
||  SERVICO DE CRIACAO E GESTAO DE JORNADAS AUTOMATIZADAS          ||
||  (Camada transversal de orquestracao)                           ||
||                                                                  ||
||  +----------------------------------------------------------+   ||
||  | FLUXO: "Abertura de Conta PF"                            |   ||
||  |                                                          |   ||
||  | [Receber doc] --> [Tratar] --> [Classificar] --> [Extrair]|   ||
||  |      --> [Validar autenticidade] --> [Regras simples]     |   ||
||  |      --> [Decisao: Aprovado/Rejeitado/Revisao]           |   ||
||  +----------------------------------------------------------+   ||
||                                                                  ||
||  +----------------------------------------------------------+   ||
||  | FLUXO: "Concessao Habitacional"                          |   ||
||  |                                                          |   ||
||  | [Receber dossie] --> [Tratar N docs] --> [Classificar]    |   ||
||  |      --> [Extrair] --> [Consultar bases externas]         |   ||
||  |      --> [Validar autenticidade] --> [Regras simples]     |   ||
||  |      --> [Regras compostas (onus, margem)]               |   ||
||  |      --> [Decisao] --> [Se pendencia: Op. Assistida]     |   ||
||  +----------------------------------------------------------+   ||
||                                                                  ||
||  +----------------------------------------------------------+   ||
||  | FLUXO: "Agronegocio - Financiamento Trator"              |   ||
||  |                                                          |   ||
||  | [Receber 4 docs] --> [Tratar] --> [Classificar]           |   ||
||  |      --> [Extrair] --> [Consultar INCRA/IBAMA]            |   ||
||  |      --> [6 sub-verificacoes encadeadas]                  |   ||
||  |      --> [Decisao] --> [Se rejeitado: Op. Assistida]     |   ||
||  +----------------------------------------------------------+   ||
||                                                                  ||
||  A CAIXA cria, edita e monitora estes fluxos via low-code/      ||
||  no-code, sem intervencao tecnica da CONTRATADA.                ||
+==================================================================+
```

### 3.2 O que Orquestra

| Servico Orquestrado | Como a Jornada Usa |
|--------------------|-------------------|
| Tratamento de arquivo digital | Etapa 1 do fluxo — chamada automatica |
| Classificacao documental | Etapa 2 — define qual ramo do fluxo seguir |
| Extracao de dados | Etapa 3 — alimenta regras e validacoes |
| Validacao de autenticidade | Etapa condicional — acionada conforme tipo |
| Regras simples | Etapa de validacao — checklist automatico |
| Regras compostas | Etapa de validacao — analise profunda |
| Consulta em bases externas | Etapa condicional — quando dossie exige |
| Operacao assistida | Fallback — quando automacao nao resolve |
| Arquivamento | Etapa final — armazenamento temporario |
| Rejeicao | Saida — quando documento/dossie nao passa |

### 3.3 Implicacao para Produto

> **Este servico e a PLATAFORMA em si.** Enquanto os demais servicos sao "engines" especializados (OCR, IA de fraude, motor de regras), as jornadas automatizadas sao o **frontend + orquestrador + workflow engine** que a CAIXA opera no dia-a-dia. E o produto principal visivel para o usuario CAIXA.

---

## 4. CAPACIDADES DETALHADAS

### 4.1 Parametrizacao Dinamica

#### O que o TR Exige

A CAIXA deve poder definir dinamicamente:

| Elemento | Descricao | Exemplo |
|---------|----------|---------|
| **Itens de analise/checklist** | Quais regras aplicar em cada etapa do fluxo | "Para Abertura de Conta: verificar idade >= 18, CPF ativo, nome confere" |
| **Ordem de execucao** | Sequencia das etapas do fluxo | "Primeiro classificar, depois extrair, depois validar, depois regras" |
| **Etapas da jornada** | Quais servicos acionar em cada ponto | "Se tipo = RG, acionar biometria; se tipo = holerite, acionar calculo" |
| **Formularios** | Telas para coleta de dados do cliente/agencia | Formulario de abertura de conta com campos nome, CPF, endereco |
| **Captura de documentos** | Interface para upload de documentos pelo cliente | Tela no app CAIXA para tirar foto do RG, selfie, comprovante |

#### Implicacao Tecnica

A plataforma precisa de:
- **Editor visual de fluxos** (drag-and-drop de etapas)
- **Configurador de checklist** (adicionar/remover regras por fluxo)
- **Form builder** (criar formularios sem codigo)
- **Configurador de rotas condicionais** (SE tipo = X, ENTAO fazer Y)
- **Versionamento de fluxos** (historico de alteracoes, rollback)

### 4.2 Automacao Inteligente com IA

#### O que o TR Exige

| Requisito | Descricao Exata do TR |
|-----------|----------------------|
| **IA para classificacao, extracao e validacao** | Aplicacao de tecnologias avancadas, incluindo IA, assegurando precisao e aderencia as regras |
| **Parametrizacao via linguagem natural** | A automacao deve permitir parametrizacao via linguagem natural |
| **Sem conhecimento tecnico** | Sem necessidade de conhecimento tecnico por parte dos usuarios |
| **Evolucao continua** | Ajuste de parametros e evolucao continua dos fluxos |

#### O que "Linguagem Natural" Significa na Pratica

| Cenario | Input do Usuario CAIXA (linguagem natural) | Output do Sistema |
|---------|------------------------------------------|------------------|
| Criar regra | "Verificar se o titular tem mais de 18 anos" | Regra automatica: campo_idade >= 18 |
| Criar checklist | "Para matricula de imovel, verificar se existem onus ativos" | Regra composta configurada com LLM para analise de onus |
| Ajustar fluxo | "Adicionar verificacao de CREA antes da etapa de laudo" | Nova etapa inserida no fluxo antes de "Analise de Laudo" |
| Consultar status | "Quantos dossies de habitacional estao pendentes de matricula?" | Dashboard filtrado com contagem |
| Corrigir regra | "A regra de margem consignavel esta usando 30%, mude para 35%" | Parametro atualizado de 0.30 para 0.35 |

#### Implicacao Tecnica

- **LLM integrado** a interface do usuario para interpretar instrucoes em portugues
- **Traducao NL → configuracao** (linguagem natural para parametros do sistema)
- **Feedback loop** (usuario confirma se a interpretacao esta correta antes de aplicar)
- **Historico de alteracoes via NL** (log de quem pediu o que e quando)

### 4.3 Autonomia da CONTRATANTE

#### O que o TR Exige

> A solucao deve permitir criacao, edicao e parametrizacao de fluxos **sem intervencao tecnica da CONTRATADA**.

#### Implicacao Direta

| A CAIXA FAZ sozinha | A CONTRATADA faz |
|--------------------|-----------------|
| Criar novo fluxo de processamento | Manter a plataforma funcionando |
| Editar etapas existentes | Garantir disponibilidade 99,5% |
| Adicionar/remover regras do checklist | Suporte tecnico quando solicitado |
| Criar formularios de captura | Integracoes com sistemas CAIXA (por UST) |
| Ajustar parametros de IA | Treinar modelos quando necessario |
| Monitorar resultados | Resolver incidentes |
| Configurar alertas | Melhoria continua |

> **Alerta de produto:** A CAIXA **nao quer depender** da contratada para mudancas operacionais. Se um novo tipo de documento surge ou uma regra muda, a CAIXA deve poder resolver sozinha. Isso exige uma plataforma self-service robusta.

### 4.4 Ferramentas Low-Code/No-Code

#### Componentes Necessarios

| Componente | Descricao | Quem Usa |
|-----------|----------|---------|
| **Visual Workflow Builder** | Editor drag-and-drop de fluxos com etapas, condicoes, bifurcacoes | Gestor de processos CAIXA |
| **Form Builder** | Criador de formularios com campos, validacoes, logica condicional | Gestor de processos CAIXA |
| **Rule Builder** | Configurador de regras simples e compostas (sem codigo) | Analista de regras CAIXA |
| **Dashboard Builder** | Criador de paineis de monitoramento customizaveis | Gestor operacional CAIXA |
| **Template Library** | Biblioteca de fluxos e componentes reutilizaveis | Todos |
| **NL Interface** | Interface de linguagem natural para configuracao assistida por IA | Todos |

### 4.5 Interfaces Interativas

#### Dois Publicos Distintos

| Publico | Interface | Funcao |
|---------|----------|--------|
| **Interno (empregados CAIXA)** | Portal web responsivo | Gerenciar demandas, visualizar resultados, configurar fluxos |
| **Externo (clientes CAIXA)** | Portal/app integrado | Upload de documentos, preenchimento de formularios, acompanhamento de status |

#### Requisitos de Interface (TR 7.14)

| Requisito | Especificacao |
|-----------|--------------|
| Tipo | GUI (Graphical User Interface) |
| Design | Intuitivo, responsivo e acessivel |
| Identidade visual | Conforme padroes da CAIXA |
| Acessibilidade | WCAG compliant |
| Compatibilidade | Mobile + desktop |
| Navegacao | Leitores de tela + navegacao por teclado |
| Idioma | Portugues do Brasil |
| API | Segura e documentada |

### 4.6 Integracao com Sistemas

#### Responsabilidade da CONTRATADA

| Integracao | Tipo | Tecnologia (Anexo I-B) |
|-----------|------|----------------------|
| Sistemas internos CAIXA (online) | Bidirecional | SOAP, REST, AMQP, IBM WebSphere MQ |
| Sistemas internos CAIXA (batch) | Lote | File Transfer, ETL via Informatica PowerCenter |
| Sistemas externos (online) | Saida | SOAP, REST |
| Sistemas externos (batch) | Lote | IBM B2B |
| Transferencia de arquivos | Lote | IBM B2B, IBM Connect:Direct |

#### Remuneracao de Integracoes

Integracoes sao remuneradas separadamente por **UST (Unidade de Servico Tecnico)** — 1 UST = 1 hora:

| Tipo de Integracao | Referencia (UST) | Prazo Maximo |
|-------------------|-----------------|-------------|
| Integracao com sistemas terceiros | 180 UST | Alta: 180h / Media: 135h / Baixa: 36h |
| Integracao com sistemas CAIXA | 180 UST | Alta: 180h / Media: 135h / Baixa: 36h |
| Versao evolutiva de integracao | 60 UST | Alta: 60h / Media: 45h / Baixa: 12h |

### 4.7 Governanca e Curadoria

#### O que o TR Exige

Monitoramento e revisao dos resultados gerados pelos processos automatizados, assegurando:
- **Conformidade** — resultados aderem as regras definidas
- **Qualidade** — acuracia dos servicos automatizados
- **Aderencia** — fluxos executam conforme projetado

#### Implicacao Tecnica

| Capacidade | Descricao |
|-----------|----------|
| **Dashboard em tempo real** | Visualizacao de demandas em processamento, concluidas, rejeitadas, pendentes |
| **Alertas automaticos** | Notificacoes quando SLA esta em risco, erro em etapa, queda de acuracia |
| **Metricas por fluxo** | Volume, tempo medio, taxa de aprovacao, taxa de rejeicao, taxa de erro por etapa |
| **Metricas por regra** | Quantas vezes cada regra e acionada, taxa de CONFORME/NAO_CONFORME |
| **Audit trail** | Historico completo de cada demanda: quem fez o que, quando, com qual resultado |
| **Curadoria de IA** | Revisao de resultados automatizados para calibracao dos modelos |
| **Feedback loop** | Correcoes manuais retroalimentam os modelos de IA |

---

## 5. REMUNERACAO — MODELO ESPECIAL

### 5.1 Servico Transversal sem Item Proprio na Proposta

> **Ponto critico:** O servico de jornadas automatizadas NAO aparece como item isolado na tabela de precos do Anexo I-C (volumetria de servicos isolados). Ele e **transversal** — seu custo esta **diluido** nos demais servicos.

### 5.2 Onde Entra na Formula de Remuneracao

```
RMF = (NS/NSP x Peso x VSE + NQ/NQP x Peso x VSE) x (1 + ACP)

VSE = Soma(Quantidade x Valor do Respectivo Servico)
```

O servico de jornadas automatizadas contribui para o VSE **indiretamente** — cada servico executado dentro da jornada (tratamento, classificacao, extracao, etc.) e remunerado pelo seu valor unitario. A jornada em si e a plataforma que viabiliza a execucao.

### 5.3 Integracoes — Remuneracao Separada por UST

As integracoes necessarias para viabilizar as jornadas sao remuneradas **a parte**, em UST:

| Componente | Remuneracao |
|-----------|------------|
| Servicos executados na jornada | Valor unitario de cada servico (proposta) |
| Plataforma de orquestracao | Custo absorvido nos servicos (transversal) |
| Integracoes com sistemas CAIXA | UST (separado) |
| Melhoria continua da plataforma | Absorvido (sem custo adicional para CAIXA) |

### 5.4 Implicacao para Precificacao

> **O custo da plataforma de jornadas deve ser diluido nos precos unitarios dos demais servicos.** Nao existe linha de receita propria para esta plataforma. Se os precos unitarios dos servicos nao cobrirem o custo de desenvolver e manter a plataforma low-code/no-code + IA + dashboards, a operacao sera deficitaria.

---

## 6. EXEMPLOS DE JORNADAS POR PROCESSO

### 6.1 Jornada: Abertura de Conta PF (Simples)

```
[Cliente envia docs via app CAIXA]
    |
    v
[1. Receber: RG + Selfie + Comprovante Residencia]
    |
    v
[2. Tratar arquivos (rotacao, bordas, recorte)]
    |
    v
[3. Classificar cada documento]
    |
    +-- RG --> [4a. Extrair dados: nome, CPF, data nasc, foto]
    |          --> [5a. Validar autenticidade: padrao grafico + biometria]
    |          --> [6a. Regras simples: idade>=18, CPF ativo, nome confere]
    |
    +-- Selfie --> [4b. Face matching com foto do RG]
    |              --> [5b. Liveness check]
    |
    +-- Residencia --> [4c. Extrair endereco]
    |                  --> [6c. Regra simples: endereco confere]
    |
    v
[7. Consolidar checklist: todos os itens CONFORME?]
    |
    +-- SIM --> [8. Aprovar abertura de conta]
    |
    +-- NAO --> [9. Operacao Assistida: contatar cliente para correcao]
```

**SLA:** 1 hora | **Regras:** ~5 simples | **Complexidade:** BAIXA

### 6.2 Jornada: Concessao Habitacional (Complexa)

```
[Agencia envia dossie: ~10 documentos]
    |
    v
[1. Receber dossie: RG, IRPF, Holerite, Matricula, Laudo, IPTU, Certidoes...]
    |
    v
[2. Tratar cada arquivo (N documentos em paralelo)]
    |
    v
[3. Classificar cada documento]
    |
    +-- Para cada tipo classificado, acionar pipeline especifico:
    |
    |   RG --> Extrair + Autenticidade + Biometria
    |   IRPF --> Extrair rendimentos + Validar com RF
    |   Holerite --> Extrair + Calcular margem consignavel
    |   Matricula --> Extrair + Analisar onus/impedimentos (LLM)
    |   Laudo --> Extrair valor + Validar CREA + Comparar com financiamento
    |   IPTU --> Extrair + Verificar quitacao
    |   Certidoes --> Extrair + Validar vigencia
    |
    v
[4. Regras simples (12-15 itens): idade, CPF, validade, assinaturas...]
    |
    v
[5. Regras compostas (5-10 itens):
    - Margem consignavel suficiente?
    - Onus na matricula impedem garantia?
    - Valor imovel dentro do teto por faixa de renda?
    - Laudo compativel com financiamento?
    - Cruzamento renda holerite vs. IRPF]
    |
    v
[6. Consultar bases externas (se necessario):
    - Certidao atualizada do RI
    - Certidao negativa de debitos]
    |
    v
[7. Consolidar checklist completo]
    |
    +-- APROVADO --> [8. Encaminhar para formalizacao]
    |
    +-- PENDENCIAS --> [9. Op. Assistida: solicitar docs adicionais]
    |
    +-- REJEITADO --> [10. Notificar agencia com motivos]
```

**SLA:** 24 horas | **Regras:** ~12 simples + ~8 compostas | **Complexidade:** MUITO ALTA

### 6.3 Jornada: Programa Pe de Meia (Minima)

```
[Cliente envia docs via app]
    |
    v
[1. Receber: Identificacao + Selfie]
    |
    v
[2. Tratar + Classificar + Extrair]
    |
    v
[3. Face matching: foto doc vs. selfie]
    |
    v
[4. Regras: tipo confere + biometria OK]
    |
    +-- OK --> [5. Aprovar]
    +-- NOK --> [6. Rejeitar com motivo]
```

**SLA:** 1 hora | **Regras:** 2-3 simples | **Complexidade:** MUITO BAIXA

---

## 7. SLAs E QUALIDADE

### 7.1 Disponibilidade da Plataforma

| Metrica | Valor |
|---------|-------|
| Disponibilidade | **99,5%** |
| Regime | **24x7x365** |
| Acesso simultaneo | Sem comprometimento de desempenho |
| Monitoramento | Continuo com alertas automaticos |

### 7.2 SLAs das Jornadas (Herdados das Filas)

| Fila | SLA da Jornada Completa | Demandas/Ano |
|------|------------------------|-------------|
| Programa Pe de Meia | **1h** | 97.293 |
| Abertura Conta | **1h** | 3.510.402 |
| Garantias Comerciais PJ | **18h** | 382.962 |
| Dossie CCA | **18h** | 1.134.461 |
| Concessao Comercial PJ | **18h** | 325.802 |
| Conta Digital | **24h** | 4.704.706 |
| ONBOARDING | **24h** | 4.558.404 |
| Concessao Habitacional | **24h** | 1.839.620 |
| Agronegocio | **24h** | 460.607 |
| ONBOARDING FGTS | **24h** | 6.829.602 |

> **O SLA e da jornada completa** — desde a recepcao do documento ate o resultado final. A plataforma de orquestracao precisa gerenciar o tempo gasto em cada etapa para garantir que o total nao exceda o SLA da fila.

### 7.3 Indicadores da Plataforma

| Indicador | Descricao | Meta |
|-----------|----------|------|
| **IDS** — Indicador de Disponibilidade do Servico | Disponibilidade da plataforma | >= 99,5% |
| **ID** — Indice de Disponibilidade | Uptime medido | >= 99,5% |
| **IA** — Indice de chamados atendidos no prazo | Chamados de suporte funcional | Definido no edital |
| **IR** — Indice de chamados sem reabertura | Qualidade da resolucao | Definido no edital |

---

## 8. REQUISITOS TECNICOS DE IMPLEMENTACAO

### 8.1 Arquitetura da Plataforma

```
+================================================================+
|                    PLATAFORMA DE JORNADAS                       |
|                                                                 |
|  +---------------------------+  +---------------------------+   |
|  | CAMADA DE APRESENTACAO    |  | CAMADA DE CONFIGURACAO    |   |
|  | (Interfaces interativas)  |  | (Low-code/No-code)        |   |
|  |                           |  |                           |   |
|  | - Portal usuario CAIXA    |  | - Visual Workflow Builder |   |
|  | - Portal cliente final    |  | - Form Builder            |   |
|  | - Dashboard operacional   |  | - Rule Builder            |   |
|  | - Dashboard gerencial     |  | - NL Interface (IA)       |   |
|  +---------------------------+  +---------------------------+   |
|                                                                 |
|  +----------------------------------------------------------+   |
|  | CAMADA DE ORQUESTRACAO (Workflow Engine)                   |   |
|  |                                                          |   |
|  | - Gerenciamento de filas e prioridades                    |   |
|  | - Roteamento condicional (tipo doc -> pipeline)           |   |
|  | - Controle de SLA e timeouts                              |   |
|  | - Retry e fallback                                        |   |
|  | - Paralelismo (processar N docs simultaneamente)          |   |
|  +----------------------------------------------------------+   |
|                                                                 |
|  +----------------------------------------------------------+   |
|  | CAMADA DE SERVICOS (Engines especializados)               |   |
|  |                                                          |   |
|  | [Tratamento] [Classificacao] [Extracao] [Autenticidade]   |   |
|  | [Regras Simples] [Regras Compostas] [Consulta Bases]     |   |
|  | [Op. Assistida] [Arquivamento] [Rejeicao]                |   |
|  +----------------------------------------------------------+   |
|                                                                 |
|  +----------------------------------------------------------+   |
|  | CAMADA DE INTEGRACAO                                      |   |
|  |                                                          |   |
|  | [REST/SOAP] [AMQP] [IBM MQ] [IBM B2B] [Connect:Direct]  |   |
|  | [Sistemas CAIXA] [Bases externas] [APIs terceiros]       |   |
|  +----------------------------------------------------------+   |
|                                                                 |
|  +----------------------------------------------------------+   |
|  | CAMADA DE DADOS E OBSERVABILIDADE                         |   |
|  |                                                          |   |
|  | [Logs estruturados] [Trilha de auditoria] [Metricas]     |   |
|  | [Alertas] [Armazenamento temporario 90d] [LGPD]          |   |
|  +----------------------------------------------------------+   |
+================================================================+
```

### 8.2 Stack Tecnologico Recomendado

| Camada | Tecnologia | Finalidade |
|--------|-----------|-----------|
| **Workflow Engine** | Camunda, Temporal, Apache Airflow, n8n | Orquestracao de etapas, filas, retries |
| **Low-code/No-code** | Retool, Appsmith, Budibase (ou proprietario) | Interface self-service para CAIXA |
| **Form Builder** | React + JSON Schema Forms, FormIO | Formularios dinamicos |
| **NL Interface** | Claude/GPT integrado a UI | Interpretacao de instrucoes em portugues |
| **Dashboard** | Grafana, Metabase, ou proprietario | Monitoramento em tempo real |
| **API Gateway** | Kong, AWS API Gateway | Roteamento, auth, rate limiting |
| **Message Queue** | RabbitMQ (AMQP), IBM MQ | Comunicacao assincrona entre etapas |
| **Storage** | S3/Blob (documentos), PostgreSQL/SQLite (metadados) | Armazenamento temporario 90 dias |
| **Observabilidade** | ELK Stack, Datadog, Prometheus + Grafana | Logs, metricas, alertas |

---

## 9. CENARIOS DE TESTE

### 9.1 Testes de Plataforma

| # | Cenario | Resultado Esperado |
|---|---------|-------------------|
| 1 | CAIXA cria novo fluxo via interface low-code | Fluxo criado e operacional sem intervencao tecnica |
| 2 | CAIXA edita etapa existente (adicionar regra) | Regra adicionada, fluxo atualizado em tempo real |
| 3 | CAIXA remove etapa do fluxo | Etapa removida, fluxo roteado corretamente |
| 4 | CAIXA cria formulario de captura de dados | Formulario funcional com validacoes |
| 5 | CAIXA parametriza regra via linguagem natural | Sistema interpreta e configura corretamente |
| 6 | CAIXA monitora fluxo em tempo real via dashboard | Dados atualizados, filtros funcionais |
| 7 | CAIXA configura alerta de SLA | Alerta disparado quando SLA em risco |

### 9.2 Testes de Jornada End-to-End

| # | Jornada | Input | Output |
|---|---------|-------|--------|
| 8 | Abertura conta PF (simples) | RG + Selfie + Residencia | Aprovado/Rejeitado em < 1h |
| 9 | Concessao habitacional (complexa) | Dossie 10 docs | Resultado com checklist completo em < 24h |
| 10 | Agronegocio (multi-doc + regra composta) | 4 docs + consulta INCRA | 6 sub-verificacoes executadas |
| 11 | Pe de Meia (minimo) | Identificacao + Selfie | Resultado em < 1h |
| 12 | Demanda com documento rejeitado | Doc ilegivel no dossie | Rejeicao com motivo + notificacao |
| 13 | Demanda com pendencia (Op. Assistida) | Dossie incompleto | Escalado para atendimento humano |
| 14 | Volume de pico (1000 demandas simultaneas) | Misto de processos | SLAs atendidos, sem degradacao |

### 9.3 Testes de Autonomia

| # | Cenario | Resultado |
|---|---------|----------|
| 15 | CAIXA cria fluxo inteiro sem contratada | Fluxo funcional end-to-end |
| 16 | CAIXA ajusta threshold de regra sem ticket | Parametro alterado imediatamente |
| 17 | CAIXA cria novo tipo de demanda | Novo tipo disponivel em producao |
| 18 | Rollback de fluxo para versao anterior | Fluxo revertido sem perda de dados |
| 19 | Versionamento: 2 versoes do mesmo fluxo | Ambas rastreaveis com historico |

---

## 10. PRECIFICACAO

### 10.1 Modelo Financeiro

| Componente | Receita | Observacao |
|-----------|---------|-----------|
| Plataforma de orquestracao | **NENHUMA DIRETA** | Custo diluido nos servicos |
| Servicos executados nas jornadas | Valor unitario de cada servico | Tratamento, classificacao, extracao, regras, etc. |
| Integracoes com sistemas CAIXA | UST (separado) | 180 UST por integracao nova |
| Melhoria continua da plataforma | **NENHUMA** | Obrigacao contratual sem custo adicional |

### 10.2 Componentes de Custo (Absorvidos)

| Componente | Custo Estimado | Observacao |
|-----------|---------------|-----------|
| Desenvolvimento da plataforma low-code/no-code | ALTO (R$ 500K-2M) | Build ou licenciamento |
| Workflow engine (licenca ou desenvolvimento) | MEDIO-ALTO | Camunda, Temporal, ou proprietario |
| Interface de linguagem natural (LLM) | MEDIO | Integracao com Claude/GPT |
| Dashboards e observabilidade | MEDIO | Grafana, Metabase, custom |
| Form builder | BAIXO-MEDIO | FormIO ou custom |
| Infraestrutura (servidores, rede, storage) | ALTO | 99,5% uptime, auto-scaling |
| Equipe de sustentacao | ALTO | DevOps, SRE, suporte N1/N2 |
| Melhoria continua (TR 7.7.5) | MEDIO | Obrigatorio sem receita adicional |

### 10.3 Alerta Critico de Precificacao

> **Este e o componente MAIS CARO e MAIS INVISIVEL da proposta.** A plataforma de jornadas e o produto principal que a CAIXA usa no dia-a-dia, mas nao tem linha propria de receita. Todo o investimento em low-code, IA, dashboards, workflow engine, integracao e observabilidade deve ser recuperado nos precos unitarios dos servicos individuais.
>
> **Estimativa de custo da plataforma:** R$ 1M-5M para construir + R$ 50K-200K/mes para manter. Com ~25,9M demandas/ano, o custo da plataforma por demanda e de R$ 0,04-0,20 — que deve ser embutido nos servicos.

---

## 11. RISCOS ESPECIFICOS

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| 1 | **CAIXA exige plataforma low-code muito sofisticada** | Alta | Custo de desenvolvimento extremamente alto | Avaliar buy vs. build, plataformas existentes (Retool, n8n) |
| 2 | **Linguagem natural gera configuracao errada** | Media | Fluxo em producao com regra incorreta | Preview/sandbox antes de publicar, confirmacao explicita |
| 3 | **CAIXA cria fluxos complexos demais via low-code** | Media | Performance degradada, erros em cascata | Limites e validacoes no builder, testes automatizados |
| 4 | **Melhoria continua sem receita** | Certa | Custo recorrente sem compensacao direta | Embutir na precificacao inicial, automatizar o maximo |
| 5 | **Integracao com legado CAIXA (IBM MQ, Connect:Direct)** | Alta | Complexidade tecnica, custo de expertise IBM | Parceria com especialistas IBM, orcamento de UST generoso |
| 6 | **Disponibilidade 99,5% da plataforma inteira** | Media | Qualquer componente indisponivel afeta a plataforma | Redundancia em todas as camadas, failover automatico |
| 7 | **Versionamento de fluxos alterados pela CAIXA** | Media | CAIXA altera fluxo e gera regressao | Versionamento obrigatorio, rollback, teste antes de publicar |
| 8 | **Transferencia de conhecimento para 10+ empregados CAIXA** | Media | CAIXA nao consegue usar low-code efetivamente | Treinamento pratico (40h), tour guiado, material didatico, suporte pos-treinamento |

---

## 12. CHECKLIST DE IMPLEMENTACAO

### Fase 1 — MVP (Orquestracao + Dashboard)

- [ ] Workflow engine basico (sequencia de etapas, roteamento por tipo)
- [ ] Integracao com os engines existentes (tratamento, classificacao, extracao, regras)
- [ ] Gerenciamento de filas e prioridades
- [ ] Dashboard operacional (demandas em andamento, concluidas, rejeitadas)
- [ ] Controle de SLA por fila (alertas de estouro)
- [ ] Logs estruturados e trilha de auditoria
- [ ] API REST para recepcao de demandas
- [ ] Suporte aos 3 fluxos mais simples (Pe de Meia, Conta Digital, Onboarding)

### Fase 2 — Low-Code + Autonomia

- [ ] Visual Workflow Builder (drag-and-drop de etapas)
- [ ] Form Builder (criacao de formularios sem codigo)
- [ ] Rule Builder (configuracao de regras simples e compostas)
- [ ] Versionamento de fluxos (historico, comparacao, rollback)
- [ ] Ambiente de sandbox/teste antes de publicar em producao
- [ ] Dashboard gerencial (metricas por fluxo, por regra, por fila)
- [ ] Portal do cliente (upload de docs, acompanhamento de status)
- [ ] Suporte a todos os 12 processos da CAIXA
- [ ] Transferencia de conhecimento (4 turmas, 40h cada)

### Fase 3 — IA + Linguagem Natural + Escala

- [ ] Interface de linguagem natural para parametrizacao (LLM integrado)
- [ ] Curadoria de IA (revisao e calibracao de resultados automatizados)
- [ ] Feedback loop (correcoes humanas retroalimentam modelos)
- [ ] Auto-scaling para absorver picos
- [ ] Dashboard builder customizavel pela CAIXA
- [ ] Template library (fluxos e componentes reutilizaveis)
- [ ] Alertas inteligentes (predizer SLA em risco antes de estourar)
- [ ] Relatorios automatizados (semanal, mensal)
- [ ] Melhoria continua estruturada (diagnostico, proposta, implementacao, monitoramento)

---

## 13. REFERENCIAS NORMATIVAS

| Documento | Secao | Conteudo |
|-----------|-------|---------|
| Anexo I — TR | 2.10 | Definicao do servico de criacao e gestao de jornadas automatizadas |
| Anexo I — TR | 2.10.1 | Objetivo: solucao integrada, servico transversal |
| Anexo I — TR | 2.10.2 | 7 capacidades obrigatorias (parametrizacao, IA, autonomia, low-code, interfaces, integracao, governanca) |
| Anexo I — TR | 5.2 | Formula de remuneracao (VSE dos servicos executados na jornada) |
| Anexo I — TR | 5.8 | Integracao de sistemas — remuneracao por UST |
| Anexo I — TR | 7.14 | Usabilidade: GUI responsiva, WCAG, identidade visual CAIXA |
| Anexo I — TR | 7.15 | Idioma: portugues do Brasil em tudo |
| Anexo I — TR | 7.16 | Disponibilidade: 99,5%, 24x7x365 |
| Anexo I — TR | 7.17 | Monitoracao com logs, alertas automaticos |
| Anexo I — TR | 7.7.5 | Melhoria continua obrigatoria |
| Anexo I — TR | 7.8 | Documentacao, guia pratico, transferencia de conhecimento |
| Anexo I-A | Definicoes | Jornada de tratamento, demanda, filas |
| Anexo I-B | Padrao Tecnologico | SOAP, REST, AMQP, IBM MQ, IBM B2B, Connect:Direct |
| Anexo I-C | Volumetria | 25,9M demandas/ano distribuidas por 12 processos |
| Anexo I-D | Execucao | Etapa 2 (Ativacao) e Etapa 4 (Implementacao continua) |
| Anexo I-H | Filas | 12 filas com SLAs (1h, 18h, 24h) |
