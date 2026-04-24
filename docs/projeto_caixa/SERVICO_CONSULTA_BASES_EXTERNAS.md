# Servico de Consulta e Disponibilizacao de Dados e Documentos em Bases Externas
## Especificacao Completa — Edital BPO CAIXA

**Referencia:** Termo de Referencia, Secao 2.6 | Secao 5.3 (Ressarcimento) | Anexo I-A (Definicoes) | Anexo I-C (Volumetria) | Anexo I-H (Filas)
**Ultima atualizacao:** 2026-04-10

---

## 1. DEFINICAO E OBJETIVO

O servico consiste em **realizar consultas em bases publicas e privadas** para obtencao de informacoes, documentos ou certidoes, que serao utilizadas na elaboracao de documentos digitais ou como insumo para outros processos da CAIXA.

**Objetivo central:** Obter dados e documentos de fontes externas ao sistema da CAIXA para complementar as informacoes dos dossies, alimentar validacoes, cruzamentos de dados e regras negociais.

> **Diferenciador:** Este servico e um **produto final** — a consulta e entregue a CAIXA como resultado. Diferente das consultas a bases feitas internamente pelo servico de validacao de autenticidade (secao 2.4), onde a consulta e etapa preparatoria nao remunerada separadamente.

---

## 2. ESCOPO DETALHADO DO SERVICO

### 2.1 Operacoes Obrigatorias (TR 2.6.1)

| # | Operacao | Descricao |
|---|----------|----------|
| 1 | **Consultar bases publicas e privadas** | Realizar consultas em bases publicas e privadas para obtencao de informacoes, documentos ou certidoes |
| 2 | **Utilizar resultados** | Informacoes utilizadas na elaboracao de documentos digitais ou como insumo para outros processos |
| 3 | **Executar sob demanda** | Executar consultas conforme interesse ou necessidade da demanda definida pela CONTRATANTE |

### 2.2 Classificacao de Bases (TR 2.6.1)

| Tipo de Base | Definicao do TR | Custo de Acesso | Responsabilidade |
|-------------|----------------|----------------|-----------------|
| **Base publica** | Aquela de livre acesso e gratuita | Gratuito | Contratada (apenas custo tecnico de integracao) |
| **Base privada** | Aquela de propriedade da CONTRATADA ou de terceiros | Pode envolver custos alem da tecnologia | Contratada paga a fonte dos dados |

> **Ponto critico sobre custos:** O TR diz que bases privadas podem envolver custos alem da tecnologia, **exigindo pagamento pela CONTRATADA junto a fonte dos dados**. Isso significa que o custo de acesso a bases privadas e da contratada — NAO e ressarcido diretamente como custo indireto (salvo quando se enquadra nas hipoteses do 5.3).

---

## 3. DOIS SUB-SERVICOS NA PROPOSTA COMERCIAL

O Anexo I-C separa este servico em **dois itens distintos** na tabela de precos:

### 3.1 Validacao Documental em Fontes Externas

| Aspecto | Detalhe |
|---------|--------|
| **Nome na proposta** | Validacao documental em fontes externas |
| **Volume anual** | **237.988** |
| **Descricao** | Consultar base externa para **validar** informacoes de um documento (ex: CPF ativo na RF, CNPJ com situacao regular, certidao vigente) |
| **Natureza** | A consulta verifica/confirma um dado ja existente no dossie |
| **Output** | Resultado de validacao (confirmado/nao confirmado) + dados complementares |

### 3.2 Disponibilizacao de Dados de Bases Externas

| Aspecto | Detalhe |
|---------|--------|
| **Nome na proposta** | Disponibilizacao de dados de bases externas |
| **Volume anual** | **112.499** |
| **Descricao** | Consultar base externa para **obter** informacoes, documentos ou certidoes que serao incorporados ao dossie (ex: obter certidao negativa de debitos, buscar dados cadastrais completos) |
| **Natureza** | A consulta traz informacao nova que nao existia no dossie |
| **Output** | Dado, documento ou certidao obtido + metadados |

### 3.3 Diferenca Conceitual

| Aspecto | Validacao em Fontes Externas | Disponibilizacao de Dados |
|---------|------------------------------|--------------------------|
| **Pergunta** | "Este dado esta correto?" | "Qual e este dado?" |
| **Input** | Dado extraido do documento + chave de busca | Chave de busca apenas |
| **Output** | Confirmacao/negacao + dados auxiliares | Dado/documento/certidao completo |
| **Exemplo** | CPF 123.456.789-00 esta ativo na RF? → SIM | Qual a situacao cadastral completa do CNPJ 12.345.678/0001-90? → Resposta completa |

---

## 4. VOLUMETRIA

### 4.1 Volume Anual Estimado

| Servico | Volume Anual | Media Mensal | Media Diaria (uteis) |
|---------|-------------|-------------|---------------------|
| Validacao documental em fontes externas | **237.988** | ~19.832 | ~952 |
| Disponibilizacao de dados de bases externas | **112.499** | ~9.375 | ~450 |
| **TOTAL** | **350.487** | **~29.207** | **~1.402** |

### 4.2 Contextualizacao

| Metrica | Valor | Observacao |
|---------|-------|-----------|
| Total de documentos processados/ano | 19.659.587 | 100% |
| Documentos com validacao em base externa | 237.988 | **1,2%** — muito seletivo |
| Documentos com disponibilizacao de dados | 112.499 | **0,6%** — ainda mais seletivo |
| Total de consultas externas como servico | 350.487 | **1,8%** do volume total |

> **Insight:** Apenas 1,8% dos documentos processados geram consultas externas remuneradas. Isso indica que a maioria das consultas a bases e feita internamente como parte de outros servicos (validacao de autenticidade, regras negociais), onde NAO sao remuneradas separadamente. O servico de consulta externa remunerado e para casos especificos de obtencao de certidoes, documentos ou validacoes formais.

### 4.3 Distribuicao Estimada por Processo

| Processo | Validacao Externa | Disponibilizacao | Justificativa |
|----------|------------------|------------------|--------------|
| Concessao Habitacional | ~80.000 | ~40.000 | Certidoes de imovel, RI, negativos de debitos |
| Agronegocio | ~40.000 | ~20.000 | DAP, CAF, CCIR, ITR, licenciamento |
| Garantia Habitacional | ~30.000 | ~15.000 | Registro de imovel, seguro |
| Concessao Comercial PJ | ~25.000 | ~12.000 | Junta Comercial, certidoes negativas |
| Garantias Comerciais PJ | ~20.000 | ~10.000 | Registro de imovel, certidoes |
| Abertura de Conta PJ | ~20.000 | ~8.000 | Junta Comercial, RF |
| Demais processos | ~22.988 | ~7.499 | Pontual |

---

## 5. CATALOGO DE BASES EXTERNAS

### 5.1 Bases Publicas (Gratuitas)

| Base | Orgao | Tipo de Consulta | Dados Obtidos | Processos que Usam |
|------|-------|-----------------|--------------|-------------------|
| **Receita Federal (CPF)** | RFB | Situacao cadastral PF | Nome, data nascimento, situacao (regular/irregular/etc.) | Abertura conta, concessao |
| **Receita Federal (CNPJ)** | RFB | Situacao cadastral PJ | Razao social, situacao, atividade, socios, endereco | Concessao PJ, garantias PJ |
| **SEFAZ (NF-e)** | Secretarias Fazenda | Validacao nota fiscal | Chave acesso, situacao, emitente, valor | Agronegocio, garantias |
| **TSE** | Tribunal Superior Eleitoral | Situacao de titulo de eleitor | Situacao cadastral | Abertura conta |
| **Correios (CEP)** | ECT | Validacao de endereco | Logradouro, bairro, cidade, UF | Todos (residencia) |
| **DETRAN** | Departamentos Estaduais | Situacao CNH | Validade, categoria, restricoes | Abertura conta |
| **CREA/CAU** | Conselhos profissionais | Registro profissional | Numero, habilitacao, situacao | Concessao habitacional |
| **Portais de transparencia** | Gov Federal/Estadual/Municipal | Situacao fiscal | Debitos, regularidade | Concessao PJ |
| **IBAMA** | Min. Meio Ambiente | Licenciamento ambiental | Licencas vigentes | Agronegocio |
| **INCRA** | Min. Agrario | Cadastro rural | DAP, CCIR, situacao | Agronegocio |

### 5.2 Bases Privadas (Com Custo)

| Base | Provedor | Tipo de Consulta | Dados Obtidos | Custo Estimado | Processos |
|------|---------|-----------------|--------------|---------------|----------|
| **Serasa/Boa Vista** | Bureaus de credito | Score de credito, restritivos | Score, pendencias, protestos, cheques sem fundo | R$ 0,50–5,00/consulta | Concessao |
| **Registros de Imoveis (RI)** | Cartorios / centrais RI | Certidao de matricula atualizada | Matricula completa, onus, proprietarios | R$ 30–80/certidao | Habitacional, garantia |
| **Junta Comercial** | Juntas Estaduais | Certidao simplificada/inteiro teor | Dados da empresa, quadro societario, situacao | R$ 10–50/certidao | Concessao PJ |
| **Cartorios de Protesto** | Centrais de protesto | Certidao de protestos | Protestos ativos, valores | R$ 5–20/certidao | Concessao |
| **Cartorios RTD/PJ** | Cartorios | Certidoes diversas | Registro de titulos, documentos | R$ 15–50/certidao | Garantia |
| **Bases biometricas** | Datavalid/Serpro | Validacao biometrica | Confirmacao de identidade | R$ 0,50–2,00/consulta | Abertura conta, onboarding |
| **ANVISA** | Agencia reguladora | Registro sanitario | Numero registro, situacao | Variavel | Agronegocio |

### 5.3 Bases da Propria CAIXA (Dados Logicos)

| Base | Tipo | Dados | Uso |
|------|------|-------|-----|
| Cadastro de clientes | Interna CAIXA | Dados pessoais, conta, historico | Cruzamento com documentos |
| Sistemas de originacao | Interna CAIXA | Dados da proposta, valores, condições | Input para regras negociais |
| Formularios eletronicos | Interna CAIXA | Dados preenchidos pelo cliente/agencia | Comparacao com documentos |

> **Nota:** Bases internas da CAIXA NAO sao "bases externas" para fins deste servico. Elas sao acessadas via integracao (SOAP/REST/AMQP) e nao geram cobranca deste servico.

---

## 6. MODELO DE REMUNERACAO — DUPLO

Este servico possui **tres camadas de remuneracao** distintas:

### 6.1 Remuneracao pelo Servico (Proposta Comercial)

| Item | Volume | Unidade |
|------|--------|---------|
| Validacao documental em fontes externas | 237.988/ano | Valor unitario por validacao |
| Disponibilizacao de dados de bases externas | 112.499/ano | Valor unitario por disponibilizacao |

### 6.2 Ressarcimento de Custos Indiretos (TR 5.3)

**ALEM** da remuneracao do servico, a CAIXA ressarce custos indiretos diretamente relacionados ao processo:

| Tipo de Custo Ressarcivel (TR 5.3.3–5.3.6) | Exemplo |
|--------------------------------------------|---------|
| Registros, averbacoes e demais atos cartorarios | Registro de garantia em cartorio |
| Emissao de certidoes, declaracoes, autenticacoes e documentos oficiais | Certidao de matricula de imovel |
| Taxas e emolumentos exigidos por orgaos publicos ou entidades habilitadas | Taxa de certidao na Junta Comercial |
| Outras despesas obrigatorias de exigencia legal ou normativa | Custos de diligencia notarial |

### 6.3 Regras do Ressarcimento (TR 5.3.7–5.3.13)

| Regra | Descricao |
|-------|----------|
| **Valor real** | Os valores ressarcidos correspondem ao **custo real incorrido** |
| **Vedacao de margem** | Vedada qualquer forma de acrescimo, remuneracao, taxa administrativa, comissao ou margem de lucro |
| **Comprovacao** | A CONTRATADA deve apresentar documentacao comprobatoria idoneA: fornecedor/orgao emissor, descricao, valor, data |
| **Faturamento segregado** | Despesas ressarciveis faturadas de forma segregada da remuneracao dos servicos de BPO |
| **Glosa** | A CAIXA pode glosar despesas: nao previstas, nao comprovadas, incompativeis, ou em desacordo com orientacoes |
| **Nao e direito adquirido** | A CAIXA pode revisar, restringir ou redefinir criterios de ressarcimento |
| **Vedacao de acrescimos** | Vedada a aplicacao de percentuais, acrescimos ou remuneracao vinculada ao valor das despesas |

### 6.4 Formula de Remuneracao por Custos Indiretos

```
RCI = Soma(Qi x Vi)
```

Onde:
- **RCI** = Remuneracao devida pelos Custos Indiretos
- **Qi** = Quantidade de ocorrencias do tipo i
- **Vi** = Valor unitario por ocorrencia
- **i** = Tipo de ocorrencia (registro, certidao, declaracao etc.)

### 6.5 Remuneracao pela Gestao e Operacionalizacao (TR 5.3.12)

A remuneracao da CONTRATADA pela **gestao e operacionalizacao** dos custos indiretos se da com base na quantidade de ocorrencias efetivamente executadas, multiplicada pelo valor unitario contratado para cada tipo.

> **Leitura critica:** Alem do ressarcimento do custo real da certidao (sem margem), ha uma remuneracao pelo SERVICO de ir ao cartorio/base e obter a certidao. Sao duas coisas:
> 1. **Custo da certidao** → ressarcimento pelo valor real (sem lucro)
> 2. **Servico de obtencao** → valor unitario da proposta (com margem)

---

## 7. DISTINCAO ENTRE CONSULTAS REMUNERADAS E NAO REMUNERADAS

### 7.1 Mapa de Decisao

```
A consulta a base externa e:
    |
    +-- PRODUTO FINAL para a CAIXA?
    |   (CAIXA pediu expressamente a consulta/certidao?)
    |       |
    |       +-- SIM --> SERVICO 2.6 (remunerado)
    |       |          + Ressarcimento de custos indiretos (se aplicavel)
    |       |
    |       +-- NAO --> Etapa preparatoria de outro servico
    |                   |
    |                   +-- Para VALIDACAO DE AUTENTICIDADE (2.4)?
    |                   |   --> Custo embutido no servico 2.4
    |                   |
    |                   +-- Para REGRAS NEGOCIAIS (2.7)?
    |                   |   --> Custo embutido no servico 2.7
    |                   |
    |                   +-- Para CLASSIFICACAO (2.5)?
    |                       --> Custo embutido no servico 2.5
```

### 7.2 Tabela Resumo

| Cenario | Servico | Remunerado? | Quem paga base privada? |
|---------|---------|-----------|----------------------|
| CAIXA pede certidao de matricula | 2.6 Disponibilizacao | SIM (valor unitario + ressarcimento custos) | Ressarcido pela CAIXA (custo real) |
| CAIXA pede validacao de CPF na RF | 2.6 Validacao externa | SIM (valor unitario) | Contratada (base gratuita) |
| Validacao de autenticidade consulta RF internamente | 2.4 Autenticidade | NAO (embutido) | Contratada |
| Regra simples compara nome com RF | 2.7 Regras | NAO (embutido) | Contratada |
| Regra composta consulta Junta Comercial | 2.7 Regras | NAO (embutido) | Contratada paga a base |

> **Alerta financeiro:** Consultas a bases privadas feitas como etapa preparatoria de outros servicos sao **custo puro** da contratada, sem ressarcimento. Apenas quando a CAIXA solicita a consulta como servico autonomo (2.6) ha remuneracao + possibilidade de ressarcimento.

---

## 8. IMPOSSIBILIDADE DE OBTENCAO — DEMANDA NAO FINALIZADA

### 8.1 Previsao Contratual (TR 5.4.2.4)

O TR preve explicitamente que a **impossibilidade tecnica ou operacional de obtencao de informacoes externas** indispensaveis a conclusao da demanda e uma hipotese de classificacao como **Demanda Nao Finalizada**, desde que devidamente registrada e comprovada.

### 8.2 Cenarios de Impossibilidade

| Cenario | Descricao | Tratamento |
|---------|----------|-----------|
| Base externa fora do ar | Site da RF/Junta/Cartorio indisponivel | Registrar tentativa + retry + DNF se persistir |
| Certidao inexistente | Matricula nao encontrada no cartorio indicado | Registrar resultado negativo |
| Dados insuficientes para consulta | CPF/CNPJ invalido ou incompleto | Rejeitar consulta com motivo |
| Base exige presenca fisica | Cartorio nao tem sistema online | Registrar impossibilidade tecnica |
| Base com acesso restrito | Dados protegidos ou acesso negado | Registrar impossibilidade legal |

### 8.3 Remuneracao em Caso de Impossibilidade

- Se a demanda e classificada como **Nao Finalizada** por impossibilidade de obtencao de informacoes externas, ha **remuneracao proporcional** aos servicos efetivamente executados (TR 5.4.4.1)
- A tentativa de consulta e registrada e comporve o esforco realizado
- NAO configura falha da contratada (e sim impedimento externo)

---

## 9. RELACAO COM OUTROS SERVICOS

### 9.1 Posicao no Pipeline

```
[Demanda recebida com necessidade de dados externos]
         |
         v
  +--------------------------------------------+
  | CONSULTA E DISPONIBILIZACAO DE DADOS        |  <-- ESTE SERVICO
  |                                            |
  | +------------------+  +------------------+ |
  | | VALIDACAO EM      |  | DISPONIBILIZACAO | |
  | | FONTES EXTERNAS   |  | DE DADOS         | |
  | | (237.988/ano)     |  | (112.499/ano)    | |
  | +--------+---------+  +--------+---------+ |
  |          |                      |           |
  +----------|----------------------|-----------+
             |                      |
             v                      v
      [Dado validado]        [Documento/certidao]
             |                      |
             v                      v
  [Alimenta regras]     [Incorporado ao dossie]
  [Alimenta autenticidade] [Usado em regras compostas]
```

### 9.2 Dependencias Upstream

| Servico | Relacao |
|---------|--------|
| **Extracao de dados** | Fornece as chaves de busca (CPF, CNPJ, numero matricula) para a consulta |
| **Classificacao documental** | Determina qual tipo de consulta e necessaria |
| **Demanda da CAIXA** | Define SE a consulta e necessaria e QUAL base consultar |

### 9.3 Dependencias Downstream

| Servico | Como Usa o Resultado |
|---------|---------------------|
| **Validacao de autenticidade** | Dados obtidos alimentam cruzamento (mas quando embutido neste servico, e remunerado aqui) |
| **Regras negociais** | Certidoes e dados obtidos sao input para regras compostas (ex: onus na matricula obtida) |
| **Dossie final** | Documentos/certidoes obtidos sao anexados ao dossie |
| **Decisao da demanda** | Ausencia de dado externo pode gerar DNF (Demanda Nao Finalizada) |

---

## 10. SLAs E QUALIDADE

### 10.1 Niveis de Servico

| Fila | SLA Total | Observacao para Consultas Externas |
|------|-----------|----------------------------------|
| Programa Pe de Meia | **1h** | Raramente requer consulta externa |
| Abertura Conta | **1h** | Consultas rapidas (RF online) |
| Garantias Comerciais PJ | **18h** | Consultas a cartorios/Junta podem levar horas |
| Concessao Habitacional | **24h** | Certidoes de imovel podem levar dias em cartorios lentos |
| Agronegocio | **24h** | Multiplas certidoes rurais |

### 10.2 Disponibilidade

| Metrica | Valor |
|---------|-------|
| Disponibilidade do servico de consulta | **99,5%** |
| Regime | **24x7x365** |

> **Nota:** A disponibilidade da base externa NAO e responsabilidade da contratada. Se a RF estiver fora do ar, o SLA pode ser impactado sem penalidade (TR 5.4.2.4).

### 10.3 Metricas de Qualidade

| Metrica | Meta | Justificativa |
|---------|------|--------------|
| **Taxa de sucesso de consulta** | >= 95% | 95% das consultas retornam resultado valido |
| **Acuracia da validacao** | >= 99% | Dado comparado corretamente com base |
| **Integridade do documento obtido** | 100% | Certidao/documento completo e legivel |
| **Rastreabilidade** | 100% | Toda consulta com log: base, timestamp, resultado, demanda_id |
| **Latencia (bases online)** | < 10 segundos | APIs publicas e privadas |
| **Latencia (bases com atraso)** | Registrar + notificar | Cartorios sem sistema rapido |

### 10.4 Penalidades

| Tipo | Formula |
|------|---------|
| Deducao por servico incorreto (VDSI) | `VDSI = 0,05% x SI x VSETF` |
| Teto | **10% do VSETF** |

---

## 11. OPERACOES TECNICAS

### 11.1 Pipeline de Consulta

```
[Demanda com necessidade de consulta externa]
         |
         v
  +----------------------------------+
  | 1. IDENTIFICACAO DA BASE         |
  | (qual base consultar?)           |
  | - RF, Junta, Cartorio, Serasa...  |
  +----------------------------------+
         |
         v
  +----------------------------------+
  | 2. PREPARACAO DA CHAVE DE BUSCA  |
  | (CPF, CNPJ, numero matricula)   |
  | - Dados extraidos do documento    |
  | - Dados logicos da CAIXA          |
  +----------------------------------+
         |
         v
  +----------------------------------+
  | 3. EXECUCAO DA CONSULTA          |
  | - API REST/SOAP                   |
  | - Web scraping (se necessario)    |
  | - Integracao com sistema terceiro |
  | - Retry em caso de falha          |
  +----------------------------------+
         |
    +----|----+
    |         |
    v         v
 [SUCESSO]  [FALHA]
    |         |
    v         v
  +-----+  +-----+
  |Parse|  |Log + |
  |dados|  |retry |
  +--+--+  +--+--+
     |        |
     v        v
  +----------------------------------+
  | 4. NORMALIZACAO DO RESULTADO     |
  | - Formato padrao                  |
  | - Vinculacao ao ID demanda        |
  | - Metadados (fonte, timestamp)    |
  +----------------------------------+
         |
         v
  [Retorno a CAIXA]
```

### 11.2 Integracoes por Tipo de Base

| Base | Metodo de Integracao | Autenticacao | Formato de Resposta |
|------|---------------------|-------------|-------------------|
| Receita Federal (CPF/CNPJ) | API REST | Certificado digital / token | JSON |
| SEFAZ (NF-e) | Web Service SOAP | Certificado digital | XML |
| Correios (CEP) | API REST | API key | JSON |
| Serasa/Boa Vista | API REST | OAuth / API key | JSON |
| Junta Comercial | API REST ou web portal | Certificado / login | PDF + JSON |
| Cartorios (RI) | Central de RI eletronica ou portal | Login + certificado | PDF (certidao) |
| DETRAN | API estadual | Certificado | JSON/XML |
| INCRA/IBAMA | Portal gov.br ou API | Login | PDF/JSON |
| Datavalid (Serpro) | API REST | OAuth | JSON |

### 11.3 Padroes Tecnologicos (Anexo I-B)

| Requisito | Especificacao |
|-----------|--------------|
| Integracao online | Web Services SOAP e REST |
| Integracao batch | IBM B2B (para bases que operam em lote) |
| Formatos | JSON, XML |
| Protocolo | HTTPS (TLS 1.3) |
| Transferencia de arquivos | IBM Connect:Direct (para certidoes em lote) |

---

## 12. MODELO DE DADOS DE SAIDA

### 12.1 Validacao em Fonte Externa

```json
{
  "demanda_id": "DEM-2026-001234",
  "servico": "validacao_fonte_externa",
  "timestamp": "2026-04-10T14:30:00Z",
  "consulta": {
    "base": "receita_federal_cpf",
    "tipo": "publica",
    "chave_busca": "123.456.789-00",
    "metodo": "api_rest"
  },
  "resultado": {
    "status": "sucesso",
    "validacao": "confirmado",
    "dados_retornados": {
      "nome": "JOSE DA SILVA SANTOS",
      "data_nascimento": "1990-05-15",
      "situacao_cadastral": "Regular",
      "data_inscricao": "2008-03-10"
    },
    "comparacao": {
      "campo": "nome",
      "valor_documento": "JOSE DA SILVA SANTOS",
      "valor_base": "JOSE DA SILVA SANTOS",
      "match": true,
      "similaridade": 1.0
    }
  },
  "custo": {
    "acesso_base": 0.00,
    "tipo_base": "publica"
  },
  "latencia_ms": 1230
}
```

### 12.2 Disponibilizacao de Dados

```json
{
  "demanda_id": "DEM-2026-005678",
  "servico": "disponibilizacao_dados",
  "timestamp": "2026-04-10T15:45:00Z",
  "consulta": {
    "base": "central_ri_eletronico",
    "tipo": "privada",
    "chave_busca": "matricula_12345_cartorio_1ri_sp",
    "metodo": "portal_web"
  },
  "resultado": {
    "status": "sucesso",
    "tipo_documento_obtido": "certidao_matricula_imovel",
    "formato": "pdf",
    "tamanho_bytes": 245760,
    "paginas": 8,
    "arquivo_id": "ARQ-2026-098765",
    "metadados": {
      "cartorio": "1o Registro de Imoveis de Sao Paulo",
      "data_emissao_certidao": "2026-04-10",
      "matricula": "12.345",
      "comarca": "Sao Paulo"
    }
  },
  "custo": {
    "acesso_base": 45.00,
    "tipo_base": "privada",
    "ressarcivel": true,
    "comprovante": "NF-2026-123456"
  },
  "latencia_ms": 18500
}
```

---

## 13. PRECIFICACAO

### 13.1 Estrutura de Precos (Dois Itens)

| Servico | Volume Anual | Unidade |
|---------|-------------|---------|
| **Validacao documental em fontes externas** | 237.988 | Por validacao |
| **Disponibilizacao de dados de bases externas** | 112.499 | Por disponibilizacao |

### 13.2 Componentes de Custo

| Componente | Validacao Externa | Disponibilizacao |
|-----------|-----------------|-----------------|
| Integracao com APIs (desenvolvimento) | MEDIO | MEDIO |
| Custo de acesso a bases publicas | ZERO | ZERO |
| Custo de acesso a bases privadas | VARIAVEL (R$ 0,50–5,00) | VARIAVEL (R$ 10–80) |
| Infraestrutura (servidores, rede) | BAIXO | BAIXO |
| Certificados digitais | BAIXO (anual) | BAIXO (anual) |
| Mao de obra (integracao + manutencao) | MEDIO | MEDIO |
| Armazenamento de documentos obtidos | MINIMO | MEDIO (certidoes em PDF) |

### 13.3 Modelo Financeiro

| Item | Formula |
|------|---------|
| **Receita do servico** | Volume x Valor unitario (proposta) |
| **Receita do ressarcimento** | Soma(Qi x Vi) — custo real sem margem |
| **Receita da gestao** | Volume de ocorrencias x Valor unitario de gestao (proposta) |
| **Custo de bases privadas** | Custo real pago as fontes (parcialmente ressarcido, parcialmente absorvido) |

### 13.4 Alertas de Precificacao

> **Volume baixo, custo unitario potencialmente alto.** Com apenas 350K consultas/ano, cada integracao com base externa precisa de ROI claro. O custo de DESENVOLVER e MANTER integracao com 10+ bases pode nao compensar se poucas sao usadas com frequencia.

> **Ressarcimento =/= lucro.** O ressarcimento de custos indiretos (certidoes, taxas) e pelo valor real SEM margem. A margem vem apenas do valor unitario do servico na proposta.

> **Consultas embutidas em outros servicos sao custo puro.** Lembrar que alem das 350K consultas remuneradas, a plataforma fara milhoes de consultas a bases como etapa de validacao de autenticidade e regras negociais, sem remuneracao especifica.

---

## 14. RISCOS ESPECIFICOS

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| 1 | **Indisponibilidade de bases externas** | Alta | Demanda nao finalizada, atraso no SLA | Retry com backoff, cache de consultas recentes, notificacao proativa |
| 2 | **Custo de bases privadas maior que estimado** | Media | Erosao de margem | Mapeamento previo de custos, negociacao com fornecedores, volume como alavanca |
| 3 | **Mudanca de API de base publica** | Media | Integracao quebra | Monitoramento de health das APIs, alertas, versao de fallback |
| 4 | **Cartorio sem sistema eletronico** | Media | Impossibilidade de consulta automatizada | Parceria com centrais de RI eletronico, fallback manual registrado |
| 5 | **Volume real de consultas embutidas muito alto** | Certa | Custo de bases privadas sem receita correspondente | Precificar servicos downstream ja embutindo custo de consulta |
| 6 | **Glosa de ressarcimento pela CAIXA** | Media | Despesa realizada nao reembolsada | Documentacao comprobatoria rigorosa, alinhamento previo de criterios |
| 7 | **Dados de base publica desatualizados** | Baixa | Validacao com dado obsoleto | Cross-check com multiplas fontes, timestamp de ultima atualizacao |
| 8 | **LGPD — dados pessoais obtidos de bases** | Alta | Risco de compliance | Tratar como dado sensivel, eliminar em 90 dias, criptografia |

---

## 15. CENARIOS DE TESTE

| # | Cenario | Base | Resultado |
|---|---------|------|----------|
| 1 | Validar CPF ativo na RF | RF (publica) | Situacao: Regular |
| 2 | Validar CPF inexistente | RF (publica) | Situacao: Nao encontrado |
| 3 | Validar CNPJ com situacao Inapta | RF (publica) | Situacao: Inapta — flag |
| 4 | Obter certidao de matricula existente | Central RI (privada) | PDF da certidao + custos ressarciveis |
| 5 | Obter certidao de matricula inexistente | Central RI (privada) | Resultado negativo documentado |
| 6 | Validar chave de NF-e valida | SEFAZ (publica) | Autorizada + dados da NF |
| 7 | Validar chave de NF-e cancelada | SEFAZ (publica) | Cancelada — flag |
| 8 | Base externa indisponivel (timeout) | Qualquer | Retry + log + DNF se persistir |
| 9 | Obter certidao simplificada Junta | Junta Comercial (privada) | PDF + dados societarios |
| 10 | Consulta com CPF invalido (digito errado) | RF | Rejeicao com motivo |
| 11 | Validacao de endereco via CEP | Correios (publica) | Logradouro, bairro, cidade, UF |
| 12 | Score de credito via Serasa | Serasa (privada) | Score + custo nao ressarcivel |
| 13 | Volume simultaneo (100 consultas) | Misto | SLA atendido |
| 14 | Ressarcimento com documentacao completa | Cartorio | Comprovante com todos os campos exigidos |
| 15 | Ressarcimento com documentacao incompleta | Cartorio | Recusado — solicitar complemento |

---

## 16. CHECKLIST DE IMPLEMENTACAO

### Fase 1 — MVP (Bases Publicas Gratuitas)

- [ ] Integracao com Receita Federal (CPF) — validacao de situacao cadastral
- [ ] Integracao com Receita Federal (CNPJ) — situacao cadastral PJ
- [ ] Integracao com Correios (CEP) — validacao de endereco
- [ ] Integracao com SEFAZ (NF-e) — validacao de chave de acesso
- [ ] API REST para solicitacao de consulta (input: tipo base + chave de busca)
- [ ] Retorno JSON padronizado com resultado + metadados
- [ ] Logs com demanda_id, base, chave, resultado, latencia
- [ ] Retry automatico (max 3 tentativas com backoff)
- [ ] Tratamento de indisponibilidade (registro + classificacao como DNF)

### Fase 2 — Bases Privadas e Certidoes

- [ ] Integracao com Central de RI Eletronico (certidoes de matricula)
- [ ] Integracao com Juntas Comerciais (certidoes PJ)
- [ ] Integracao com Serasa/Boa Vista (score de credito)
- [ ] Integracao com Datavalid/Serpro (validacao biometrica)
- [ ] Modulo de gestao de custos indiretos (rastrear despesas para ressarcimento)
- [ ] Geracao automatica de documentacao comprobatoria para ressarcimento
- [ ] Faturamento segregado de custos indiretos vs. servicos BPO
- [ ] Cache de consultas recentes (evitar re-consulta dentro de janela temporal)

### Fase 3 — Escala e Otimizacao

- [ ] Integracao com todas as bases do catalogo (CREA, DETRAN, INCRA, IBAMA, ANVISA)
- [ ] Dashboard de monitoramento: disponibilidade por base, latencia, custos
- [ ] Alertas de indisponibilidade de bases externas
- [ ] Batch processing para consultas em lote (via IBM B2B / Connect:Direct)
- [ ] Otimizacao de custos: negociacao de volume com fornecedores privados
- [ ] Auditoria automatizada de ressarcimentos (pre-validacao antes de enviar a CAIXA)
- [ ] Monitoramento de mudancas em APIs externas (health check periodico)
- [ ] LGPD compliance: eliminacao de dados obtidos apos 90 dias

---

## 17. REFERENCIAS NORMATIVAS

| Documento | Secao | Conteudo |
|-----------|-------|---------|
| Anexo I — TR | 2.6 | Definicao do servico de consulta e disponibilizacao |
| Anexo I — TR | 2.6.1 | 4 operacoes (consultar, utilizar, base publica, base privada, executar sob demanda) |
| Anexo I — TR | 5.3 | Ressarcimento de custos indiretos (5.3.1 a 5.3.13) |
| Anexo I — TR | 5.3.7 | Valor real sem margem |
| Anexo I — TR | 5.3.8 | Documentacao comprobatoria |
| Anexo I — TR | 5.3.10 | Hipoteses de glosa pela CAIXA |
| Anexo I — TR | 5.3.12 | Remuneracao pela gestao e operacionalizacao + formula RCI |
| Anexo I — TR | 5.4.2.4 | Impossibilidade de obtencao de informacoes externas como DNF |
| Anexo I — TR | 2.3.2.3 | Extracao como etapa preparatoria NAO remunerada |
| Anexo I — TR | 2.4 | Validacao de autenticidade (consultas embutidas) |
| Anexo I — TR | 2.7 | Regras negociais (consultas embutidas) |
| Anexo I-A | Definicoes | Cruzamento de dados |
| Anexo I-B | Padrao Tecnologico | SOAP, REST, IBM B2B, Connect:Direct |
| Anexo I-C | Secao 5 | Volumes: 237.988 (validacao) + 112.499 (disponibilizacao) |
| Anexo I-G | Seguranca | LGPD para dados obtidos de bases externas |
| Anexo I-H | Filas | SLAs por fila |
