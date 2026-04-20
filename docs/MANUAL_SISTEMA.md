# gbr-eval — Manual do Sistema

> Para qualquer pessoa que precise entender o que e o gbr-eval, por que ele existe e como funciona.
> Nao requer conhecimento tecnico.
>
> Ultima atualizacao: 2026-04-20

---

## Sumario

1. [O que e o gbr-eval](#1-o-que-e-o-gbr-eval)
2. [Por que ele existe](#2-por-que-ele-existe)
3. [O problema que ele resolve](#3-o-problema-que-ele-resolve)
4. [Como funciona — visao geral](#4-como-funciona--visao-geral)
5. [As quatro camadas de qualidade](#5-as-quatro-camadas-de-qualidade)
6. [Golden sets — a verdade de referencia](#6-golden-sets--a-verdade-de-referencia)
7. [Graders — os avaliadores](#7-graders--os-avaliadores)
8. [O que e avaliado hoje — os 5 documentos prioritarios](#8-o-que-e-avaliado-hoje--os-5-documentos-prioritarios)
9. [O ciclo de avaliacao](#9-o-ciclo-de-avaliacao)
10. [O Gate — decisao de go/no-go](#10-o-gate--decisao-de-gono-go)
11. [Deteccao de problemas ao longo do tempo](#11-deteccao-de-problemas-ao-longo-do-tempo)
12. [O painel administrativo (frontend)](#12-o-painel-administrativo-frontend)
13. [Integracao com o pipeline de desenvolvimento](#13-integracao-com-o-pipeline-de-desenvolvimento)
14. [Quem faz o que — papeis e responsabilidades](#14-quem-faz-o-que--papeis-e-responsabilidades)
15. [Protecao de dados e conformidade](#15-protecao-de-dados-e-conformidade)
16. [Estado atual do projeto](#16-estado-atual-do-projeto)
17. [O que falta — proximos passos](#17-o-que-falta--proximos-passos)
18. [Perguntas frequentes](#18-perguntas-frequentes)
19. [Glossario](#19-glossario)

---

## 1. O que e o gbr-eval

O gbr-eval e o **sistema de controle de qualidade automatizado** da GarantiaBR. Ele funciona como um "inspetor de qualidade" que verifica se os produtos de inteligencia artificial da empresa estao produzindo resultados corretos.

Imagine uma fabrica de automoveis: antes de cada carro sair da linha de producao, ele passa por uma inspecao rigorosa — freios funcionam? Pintura sem defeito? Motor dentro das especificacoes? O gbr-eval faz o mesmo, mas para os **produtos de IA** da GarantiaBR.

Na pratica, a GarantiaBR usa inteligencia artificial para ler documentos financeiros (matriculas de imoveis, contratos sociais, certidoes, procuracoes) e extrair informacoes importantes deles. O gbr-eval verifica se a IA esta fazendo isso corretamente — se o CPF extraido esta certo, se o valor do imovel confere, se a data de validade da certidao foi lida sem erro.

**Em uma frase:** gbr-eval e o guardiao da qualidade dos produtos de IA da GarantiaBR.

---

## 2. Por que ele existe

### O contexto de negocios

A GarantiaBR processa documentos financeiros para grandes instituicoes como **Itau, Bradesco e Banco Pine**. Cada informacao extraida incorretamente pode gerar consequencias serias:

- Um **CPF errado** pode associar uma garantia ao proprietario errado
- Um **valor de imovel incorreto** pode comprometer uma decisao de credito
- Uma **certidao vencida** lida como valida pode violar regras regulatorias
- Um **onus nao identificado** em uma matricula pode gerar prejuizo para o banco

Quando a IA erra, o erro se propaga pela cadeia de decisao. O gbr-eval existe para **capturar esses erros antes que cheguem ao cliente**.

### O problema do legado

Os sistemas anteriores da GarantiaBR (plataforma-modular e originacao_imobiliaria, com mais de 1.600 branches combinadas) serao descontinuados e reconstruidos. O gbr-eval foi construido **antes** dos novos sistemas — isso se chama "eval-first" (avaliacao primeiro).

A logica e simples: se voce define os criterios de qualidade **antes** de construir o produto, todo o time sabe exatamente o que "correto" significa desde o primeiro dia.

### Por que nao confiar apenas em testes tradicionais

Testes tradicionais de software (testes unitarios, testes de integracao) verificam se o **codigo** funciona — "quando eu chamo a funcao X, ela retorna Y?". Isso e necessario, mas insuficiente quando IA esta envolvida.

O gbr-eval vai alem: ele verifica se o **resultado** esta correto contra uma referencia humana. Nao importa se o codigo executou sem erros — importa se a IA extraiu o CPF certo do documento.

---

## 3. O problema que ele resolve

### Antes do gbr-eval

| Situacao | Risco |
|----------|-------|
| Nenhum teste automatizado para os 3 fluxos criticos (documentos, due diligence, avaliacao de bens) | Erros de extracao so eram descobertos quando o analista do banco reclamava |
| Checklists manuais de QA | Humanos sao inconsistentes, cansam, esquecem itens |
| Testes "tautologicos" no sistema anterior | O teste comparava o resultado da IA com ele mesmo — como um aluno corrigindo sua propria prova |
| Sem rastreabilidade | Impossivel provar para auditores (ISO 27001) que a qualidade era monitorada |

### Depois do gbr-eval

| Situacao | Beneficio |
|----------|----------|
| Avaliacao automatica contra golden sets (respostas corretas anotadas por humano) | Erros sao capturados automaticamente, antes de chegar ao cliente |
| Criterios objetivos e mensuraveis | "Extracao >= 95% nos campos criticos" e uma meta clara, nao uma opiniao |
| Execucao no pipeline de desenvolvimento (CI) | Codigo com problemas nao consegue ser integrado ao produto |
| Rastreabilidade completa | Cada avaliacao tem ID, data, versao, resultados — pronto para auditoria |

---

## 4. Como funciona — visao geral

O gbr-eval funciona em tres etapas simples:

### Etapa 1: Definir o que e "correto" (Golden Sets)

Um especialista humano analisa documentos reais e anota as respostas corretas. Por exemplo, para uma matricula de imovel:

> "O numero da matricula e 12345, o proprietario e Joao Silva, CPF 000.000.000-XX, a area e 150m2, e ha uma alienacao fiduciaria em favor do Banco Exemplo."

Essas respostas corretas sao chamadas de **golden sets** — a "verdade de referencia" contra a qual tudo e comparado.

### Etapa 2: Definir como medir (Tasks e Graders)

Para cada tipo de verificacao, existe uma **task** (tarefa de avaliacao) e um ou mais **graders** (avaliadores):

- **Task:** "Verificar se a IA extrai corretamente os campos criticos de uma matricula"
- **Graders:** "O CPF deve ser exatamente igual" (exact_match), "O nome do proprietario deve ser pelo menos 85% similar" (fuzzy matching), "O campo de onus nao pode estar vazio" (field_not_empty)

### Etapa 3: Executar e comparar (Runner)

O sistema executa a IA contra os mesmos documentos e compara os resultados com as respostas corretas:

```
Resultado da IA:  CPF = 123.456.789-09, Nome = "Joao da Silva"
Resposta correta: CPF = 123.456.789-09, Nome = "Joao Silva"
                  ----
                  CPF: CORRETO (match exato)
                  Nome: CORRETO (similaridade 94%, acima do minimo de 85%)
```

Se a IA acerta acima do limiar definido (por exemplo, 95%), a avaliacao **passa**. Se nao, **falha** — e o codigo nao pode ser integrado ao produto.

---

## 5. As quatro camadas de qualidade

O gbr-eval organiza a qualidade em quatro camadas independentes. Cada uma avalia um aspecto diferente:

### Camada E — Qualidade de Engenharia

**Pergunta:** "O codigo esta bem escrito e segue as regras da empresa?"

**Dono do criterio:** role `technology` — a area de Tecnologia define os padroes de codigo, convencoes e regras de dominio que os engenheiros devem seguir.

Exemplos do que avalia:
- Toda consulta ao banco de dados filtra pelo cliente (tenant)? Se nao, dados de um banco podem vazar para outro.
- Calculos financeiros usam tipo Decimal (preciso) em vez de float (impreciso)?
- Integracoes externas (SERPRO, ONR) tem mecanismo de retry com backoff?
- Credenciais de acesso estao protegidas, nao escritas no codigo?

**Status:** Operacional. 22 regras definidas para 5 sistemas prioritarios (atom-back-end, engine-billing, engine-integracao, garantia-ia, notifier). Execucao local-first via `--code-dir`.

### Camada P — Qualidade do Produto

**Pergunta:** "A IA esta produzindo resultados corretos?"

**Dono do criterio:** role `product` — a area de Produto define o que "correto" significa: quais campos sao criticos, quais limiares sao aceitaveis, e o que constitui uma extracao valida.

Exemplos do que avalia:
- O CPF extraido de uma matricula esta correto?
- A classificacao do documento esta certa (e uma matricula, nao um IPTU)?
- Cada campo extraido tem citacao indicando de onde no documento veio?
- O parecer final segue a rubrica definida?

**Status:** Operacional. 26 tarefas de avaliacao de produto, 40 golden sets, 12 avaliadores.

### Camada O — Qualidade Operacional (futuro)

**Pergunta:** "O sistema esta operando dentro dos parametros?"

**Dono do criterio:** role `operations` — a area de Operacoes definira os SLAs, limites de custo e parametros de disponibilidade.

Exemplos:
- A IA processa um documento em menos de 10 minutos (SLA)?
- O custo por jornada de auditoria esta abaixo de R$50?
- O sistema esta disponivel quando necessario?

### Camada C — Conformidade (futuro)

**Pergunta:** "Estamos em conformidade com regulamentacoes?"

**Dono do criterio:** role `compliance` — a area de Compliance definira os requisitos regulatorios (LGPD, BACEN, ISO 27001) que o sistema deve satisfazer.

Exemplos:
- Dados pessoais (LGPD) estao sendo tratados corretamente?
- Toda acao tem registro de auditoria (ISO 27001)?
- Controles financeiros atendem requisitos do BACEN?

---

## 6. Golden sets — a verdade de referencia

### O que sao

Golden sets sao conjuntos de **respostas corretas anotadas por um especialista humano**. Eles sao a referencia contra a qual a IA e avaliada.

Pense assim: em uma prova, o gabarito e criado pelo professor. Os golden sets sao o "gabarito" do gbr-eval — feitos por um humano qualificado, nao pela propria IA.

### Como sao criados

1. O especialista responsavel acessa o sistema de producao e localiza documentos reais
2. Le o PDF original e compara com o que a IA extraiu
3. Anota as respostas corretas campo por campo
4. Remove dados pessoais sensiveis (CPFs, nomes reais, enderecos) — anonimizacao obrigatoria
5. Um revisor verifica a anotacao
6. O golden set e salvo no repositorio com metadados completos (quem anotou, quando, hash do documento)

### Tipos de cases (casos de teste)

Cada golden set tem diferentes tipos de casos para testar a IA em situacoes variadas:

| Tipo | Numeracao | O que testa | Exemplo |
|------|-----------|-------------|---------|
| **Positivo** | 001-099 | Documento correto, completo | Matricula normal com todos os campos |
| **Confuser** | 100-199 | Documento parecido mas diferente | IPTU confundido com matricula |
| **Edge case** | 200-299 | Documento correto com situacoes incomuns | Matricula com campo de onus vazio |
| **Degradado** | 300-399 | Documento com qualidade ruim | Scan cortado, OCR com erros |

### Por que isso importa

- **Zero tautologia:** a IA nunca avalia a si mesma. O gabarito e humano.
- **Rastreabilidade:** cada caso tem registro de quem anotou, quando, e qual documento original
- **LGPD:** dados pessoais sao removidos antes de entrar no sistema. CPFs reais viram `000.000.000-XX`.

### Numeros atuais

| Documento | Casos | Composicao |
|-----------|-------|------------|
| Matricula de imovel | 8 | 5 positivos + 2 edge cases + 1 confuser |
| Contrato social | 8 | 5 positivos + 2 edge cases + 1 confuser |
| Certidao negativa de debito (CND) | 8 | 5 positivos + 2 edge cases + 1 confuser |
| Procuracao | 8 | 5 positivos + 2 edge cases + 1 confuser |
| Certidao trabalhista | 8 | 5 positivos + 2 edge cases + 1 confuser |
| Balanco patrimonial | 0 | Bloqueado — nenhum documento disponivel no sistema |
| Red team (adversarial) | 0 | Bloqueado — capacidade de deteccao ainda nao implementada |
| **Total** | **40** | |

Meta: expandir para 150+ casos com geracao sintetica (assistida por IA, mas sempre revisada por humano).

---

## 7. Graders — os avaliadores

Graders sao os "inspetores de qualidade" individuais. Cada um sabe verificar um tipo especifico de coisa.

### Graders deterministicos (sempre dao o mesmo resultado)

| Grader | O que faz | Analogia |
|--------|-----------|----------|
| **exact_match** | Verifica se o valor e exatamente igual | "O CPF extraido e identico ao do gabarito?" |
| **numeric_range** | Verifica se um numero esta dentro de limites | "O custo esta entre R$0 e R$50?" |
| **numeric_tolerance** | Verifica se um numero esta proximo (com margem) | "A area e 150m2 com tolerancia de 1%?" |
| **field_not_empty** | Verifica se o campo existe e nao esta vazio | "O campo de onus foi preenchido?" |
| **set_membership** | Verifica se o valor pertence a um conjunto valido | "O status e 'valida', 'vencida' ou 'revogada'?" |
| **string_contains** | Verifica se um texto contem uma informacao | "O parecer menciona alienacao fiduciaria?" |
| **regex_match** | Verifica se um texto segue um padrao | "O CPF esta no formato XXX.XXX.XXX-XX?" |
| **field_f1** | Compara campos extraidos vs esperados com tolerancia | "Dos 10 campos, quantos a IA acertou? (F1 score)" |

### Graders de engenharia (verificam o codigo)

| Grader | O que faz | Analogia |
|--------|-----------|----------|
| **pattern_required** | Padrao deve estar presente no codigo | "O codigo filtra por tenant_id?" |
| **pattern_forbidden** | Padrao NAO deve estar presente | "O codigo tem senha hardcoded?" |
| **convention_check** | Conjunto de regras (obrigatorias + proibidas) | "O codigo segue todas as 5 convencoes?" |

### Grader baseado em IA (LLM-judge)

Alem dos graders deterministicos, existe um avaliador que usa a propria IA (Claude Sonnet) para julgar resultados mais complexos, como a qualidade de um parecer juridico. Esse avaliador:

- Comeca como **informativo** (anota observacoes mas nao bloqueia)
- So se torna **bloqueante** apos provar consistencia em 50+ avaliacoes
- Nunca recebe dados pessoais reais — tudo e anonimizado antes

O LLM-judge tambem pode considerar os resultados dos graders anteriores na sua avaliacao. Por exemplo, se o grader de CPF detectou erro, o LLM-judge sabe disso e pode levar em conta ao avaliar o parecer geral. Isso se chama "avaliacao contextual" — cada avaliador pode ver o que os anteriores encontraram.

### Como os graders trabalham juntos

Cada tarefa de avaliacao pode usar **multiplos graders** com pesos diferentes:

- Campos **criticos** (CPF, valor do imovel, onus) tem peso 3
- Campos **importantes** (nome do proprietario, area) tem peso 2
- Campos **informativos** (endereco, comarca) tem peso 1

O score final e uma media ponderada. Se o score fica abaixo do limiar (normalmente 95%), a avaliacao falha.

### Repeticao para consistencia (Epochs)

Graders baseados em IA (como o LLM-judge) podem dar resultados ligeiramente diferentes a cada execucao — assim como dois professores podem discordar em uma avaliacao subjetiva. Para lidar com isso, o gbr-eval pode repetir a avaliacao varias vezes e agregar os resultados:

- **Media:** usa a media dos scores (o padrao)
- **Pelo menos um:** passa se pelo menos uma repeticao teve sucesso
- **Unanimidade:** so passa se todas as repeticoes tiveram sucesso
- **Maioria:** passa se a maioria das repeticoes teve sucesso

Graders deterministicos (que sempre dao o mesmo resultado) nao precisam de repeticao — o sistema pula automaticamente.

---

## 8. O que e avaliado hoje — os 5 documentos prioritarios

O gbr-eval avalia a extracao de informacoes de 5 tipos de documentos financeiros (chamados "skills P0" — prioridade maxima):

### 1. Matricula de imovel

Documento que comprova a propriedade de um imovel. Campos criticos avaliados:

- Numero da matricula
- CPF/CNPJ do proprietario
- Area do imovel
- Onus (hipotecas, penhoras, restricoes)
- Alienacao fiduciaria (garantia bancaria)

### 2. Contrato social

Documento de constituicao de uma empresa. Campos criticos avaliados:

- CNPJ da empresa
- Razao social
- Socios e suas participacoes (%)
- Capital social
- Poderes de administracao

### 3. Certidao negativa de debito (CND)

Certidao emitida por orgaos como Receita Federal, FGTS, etc. Campos criticos:

- Tipo de certidao (federal, estadual, trabalhista)
- Numero da certidao
- Orgao emissor
- Data de validade
- Status (negativa, positiva com efeito de negativa)

### 4. Procuracao

Documento que confere poderes a um representante. Campos criticos:

- Outorgante (quem concede poderes) e CPF
- Outorgado (quem recebe poderes)
- Poderes especificos concedidos
- Data de validade

### 5. Certidao trabalhista

Certidao emitida por tribunais do trabalho. Campos criticos:

- Titular (pessoa ou empresa consultada)
- Resultado (negativa = sem processos, positiva = com processos)
- Lista de processos (quando positiva)
- Orgao emissor (qual TRT)

### Documento bloqueado: Balanco patrimonial

O balanco patrimonial (tipo de documento 293) foi removido da lista prioritaria porque nao ha documentos desse tipo disponiveis no sistema de producao para criar golden sets. Substituido pela certidao trabalhista.

---

## 9. O ciclo de avaliacao

O gbr-eval opera em um ciclo continuo:

```
    [1. Definir criterios]
           |
           v
    [2. Criar golden sets]  <-- Humano anota respostas corretas
           |
           v
    [3. Configurar tasks]   <-- Quais graders usar, com quais pesos
           |
           v
    [4. Executar avaliacao]  <-- IA processa documentos, graders comparam com golden set
           |
           v
    [5. Analisar resultados] <-- Passou ou falhou? Onde errou? Tendencia?
           |
           v
    [6. Melhorar o produto]  <-- Time corrige a IA com base nos erros encontrados
           |
           v
       (volta ao passo 4)
```

### Modos de execucao

| Modo | O que faz | Quando usar |
|------|-----------|-------------|
| **Self-eval** | Compara a resposta correta consigo mesma | Sanity check: se isso falhar, os graders estao com problema |
| **Offline** | Compara respostas pre-gravadas com golden set | Avaliacao diaria, validacao de mudancas |
| **Online** (futuro) | Chama a IA em tempo real e avalia a resposta | Avaliacao em staging/producao |

### Workflow local-first para Engenharia

Para a Camada E (avaliacao de codigo), o fluxo comeca na maquina do engenheiro, antes do PR:

```
    Engenheiro escreve codigo
           |
           v
    Roda eval de engenharia LOCAL:
    gbr-eval run --suite tasks/engineering/ --code-dir /caminho/para/repo/
           |
           v
    Vê quais arquivos violam quais regras
    (avaliacao arquivo por arquivo, nao concatenado)
           |
           v
    Corrige e confirma que passou localmente
           |
           v
    Abre PR -> CI valida novamente
```

Isso permite ao engenheiro entender exatamente qual arquivo violou qual regra, sem esperar o CI. O CI e a confirmacao final, nao o primeiro sinal de problema.

---

## 10. O Gate — decisao de go/no-go

O "Gate" e o **ponto de decisao** que determina se uma mudanca no produto pode ser integrada ou nao. Funciona como um semaforo:

| Resultado | Significado | Acao |
|-----------|-------------|------|
| **GO** | Tudo passou. Qualidade dentro dos criterios. | Mudanca pode ser integrada |
| **CONDITIONAL GO** | Criterios obrigatorios passaram, mas alguns opcionais falharam. | Mudanca pode ser integrada com ressalvas documentadas |
| **NO GO** | Pelo menos um criterio obrigatorio falhou. | Mudanca **bloqueada** ate correcao |
| **NO GO ABSOLUTE** | Regressao detectada: algo que funcionava parou de funcionar. | Mudanca **bloqueada**. Alerta critico. |

### Os 13 criterios do Gate Fase 1

Para o produto ser aprovado para uso com o primeiro cliente (Banco Pine), todos estes criterios devem ser atendidos:

| # | Criterio | Meta | Tipo |
|---|----------|------|------|
| 1 | Acuracia de classificacao | >= 90% | Automatico (eval) |
| 2 | Acuracia de extracao (campos P0) | >= 95% | Automatico (eval) |
| 3 | Cobertura de citation linking | = 100% | Automatico (eval) |
| 4 | Deteccao de inconsistencias pelo Evaluator | >= 80% | Nao avaliavel (capacidade pendente) |
| 5 | Custo de IA por jornada | <= R$50 | Automatico (eval) |
| 6 | Cobertura de audit trail | = 100% | Automatico (eval) |
| 7 | Vulnerabilidades de seguranca P0 | = Zero | Manual + SAST/DAST |
| 8 | SLA de completude (P95) | < 10 minutos | Automatico (eval) |
| 9 | Analises reais com Pine | >= 10 | Manual |
| 10 | NPS do analista Pine | >= 40 | Manual |
| 11 | Proposta comercial enviada | Sim/Nao | Manual |
| 12 | Formula de scoring assinada pelo CLO | Sim/Nao | Manual |
| 13 | UI aprovada pelo Designer | Sim/Nao | Manual |

Os criterios 1-8 sao verificados automaticamente pelo gbr-eval. Os criterios 9-13 sao manuais e estao fora do escopo do sistema.

---

## 11. Deteccao de problemas ao longo do tempo

O gbr-eval nao apenas verifica qualidade em um momento. Ele tambem detecta **tendencias** ao longo do tempo:

### Regressao

Compara duas execucoes (uma antiga e uma nova) para detectar se algo piorou:

- **Falhas novas:** tarefas que passavam e agora falham. Isso e grave — algo quebrou.
- **Degradacao silenciosa:** tarefas que ainda passam mas o score caiu significativamente. Por exemplo, uma tarefa que tinha score 1.0 e agora tem 0.7 — tecnicamente ainda passa (limiar de 0.5), mas a qualidade caiu muito.

### Tendencias

Analisa multiplas execucoes ao longo de dias/semanas para detectar padroes:

- **Declinio consistente:** se o score de uma tarefa cai 5 execucoes seguidas, algo esta degradando gradualmente
- **Declinio ruidoso:** mesmo quando os scores oscilam (0.98, 0.94, 0.96, 0.92, 0.93), o sistema detecta a tendencia de queda usando analise estatistica (regressao linear)
- **Aproximando do limiar:** alerta quando o score esta proximo do limiar de aprovacao, mesmo que ainda passe

Esses alertas permitem agir **antes** que o problema se torne critico.

---

## 12. O painel administrativo (frontend)

O gbr-eval tem um **painel administrativo web** que permite visualizar e gerenciar tudo sem precisar usar a linha de comando.

### Modulos disponiveis

| Modulo | O que faz |
|--------|-----------|
| **Dashboard** | Visao geral: metricas-chave, ultimas execucoes, alertas ativos |
| **Runs** | Historico de execucoes, comparacao entre runs, analise de tendencias |
| **Golden Sets** | Visualizar e gerenciar os gabaritos (criar, editar, importar/exportar) |
| **Tasks** | Configurar tarefas de avaliacao (quais graders, quais pesos, qual limiar) |
| **Rubrics** | Gerenciar rubricas do avaliador IA (LLM-judge) |
| **Conventions** | Regras de engenharia por repositorio |
| **Calibration** | Sessoes de calibracao entre anotadores |
| **Contracts** | Contratos de schema com sistemas alvo |
| **Skills** | Definicoes de skills (campos, pesos, criticidade) |
| **Alerts** | Alertas de degradacao, regressao, tendencias |

### Acesso

O painel roda localmente na maquina do engenheiro (porta 3000). Nao e um servico em nuvem — os dados ficam em um banco de dados local (SQLite).

### Seguranca do painel

O acesso ao painel e protegido por um token de autenticacao (variavel de ambiente `ADMIN_API_TOKEN`). Se o token nao estiver configurado, o painel retorna erro em vez de permitir acesso — uma medida de seguranca chamada "fail-closed" (falhar fechado, nao aberto). A comparacao do token usa um metodo resistente a ataques de temporalizacao.

---

## 13. Integracao com o pipeline de desenvolvimento

### Como funciona no dia a dia

Quando um engenheiro faz uma mudanca no codigo e abre um PR (Pull Request — pedido de integracao):

```
    Engenheiro faz mudanca
           |
           v
    [ENGENHARIA] Roda eval LOCAL antes do PR:
    gbr-eval run --suite tasks/engineering/ --code-dir /caminho/para/repo/
    Resultado: quais arquivos violam quais regras
           |
           v (apos corrigir localmente)
    Abre PR no GitHub
           |
           v
    CI roda automaticamente:
    1. Testes unitarios          -> Codigo funciona?
    2. Lint + type check         -> Codigo esta limpo?
    3. gbr-eval (self-eval)      -> Qualidade da IA ok?
    4. gbr-eval (engineering)    -> Regras de engenharia ok?
           |
           v
    Resultado aparece no PR:
    - "GO" -> Reviewer pode aprovar
    - "NO GO" -> PR bloqueado ate correcao
```

**Filosofia local-first para Engenharia:** o engenheiro roda o eval de engenharia na propria maquina antes de abrir o PR. O CI e a confirmacao, nao o primeiro sinal de problema. A avaliacao e arquivo por arquivo — o engenheiro sabe exatamente qual arquivo violou qual regra, sem precisar esperar o pipeline de CI.

### Dois niveis de verificacao

| Nivel | O que testa | Quem roda |
|-------|-------------|-----------|
| **CI do gbr-eval** | Os avaliadores estao funcionando corretamente? | Automatico, a cada mudanca no gbr-eval |
| **Local (Engineering)** | O codigo segue as regras de engenharia? | Engenheiro, antes de abrir PR |
| **CI dos repos alvo** (futuro) | O produto esta produzindo resultados corretos? | Automatico, a cada mudanca no produto |

Atualmente, o eval de engenharia roda localmente (local-first) e no CI do gbr-eval. A integracao completa com o CI dos repositorios de produto e uma das proximas prioridades.

---

## 14. Quem faz o que — papeis e responsabilidades

O sistema e **agnóstico a pessoas especificas**. A propriedade e definida por **papel (role)**, nao por nome. Versoes futuras terao um sistema de permissoes de usuarios que mapeara pessoas a roles. Hoje, cada role e exercido pela area responsavel.

### Role: product — dono da Camada P (Produto)

A area de Produto define o que "correto" significa para os outputs de IA:

- **Anota golden sets** — unica area autorizada a definir o que e a resposta correta
- **Valida resultados** — assina a formula de scoring
- **Define criterios** — decide quais campos sao criticos, importantes ou informativos
- **Decide limiares** — 95% de acuracia? 90%? Essa e uma decisao de negocio, nao tecnica
- **Promove graders** — decide quando o LLM-judge passa de informativo a bloqueante

*Responsavel atual:* o especialista designado para cada skill exerce este role. Diogo Dantas coordena enquanto o sistema de permissoes nao existe.

### Role: technology — dono da Camada E (Engenharia)

A area de Tecnologia define os padroes de codigo que o eval verifica:

- **Define convencoes** — quais padroes sao obrigatorios, quais sao proibidos em cada repo
- **Configura tasks de engenharia** — quais arquivos verificar, quais graders usar
- **Roda o eval localmente** — antes de abrir PR, usando `--code-dir` para apontar para o repo alvo
- **Implementa graders** — escreve o codigo dos avaliadores
- **Corrige problemas** — quando o eval falha, investigam e corrigem o codigo

### Role: operations — dono da Camada O (Operacional, futuro)

A area de Operacoes definira os SLAs, limites de custo e parametros de disponibilidade que o eval verificara.

### Role: compliance — dono da Camada C (Conformidade, futuro)

A area de Compliance definira os requisitos regulatorios (LGPD, BACEN, ISO 27001) que o eval verificara.

### IA (Claude)

- **Assiste na anotacao** — sugere campos esperados, mas NUNCA valida sozinha
- **Assiste no codigo** — gera graders, testes, configuracoes
- **Limitacao explicita:** a IA nunca decide o que e "correto" — isso e responsabilidade de cada role humano

### Principio fundamental

> **"A IA e a ultima linha de defesa da qualidade"** — ela ajuda, mas quem decide e o humano com o role correto.

A IA nao pode:
- Criar golden sets e declara-los como validados
- Decidir se um grader deve bloquear ou apenas informar
- Alterar limiares de aprovacao
- Expandir o escopo de uma avaliacao sem autorizacao

---

## 15. Protecao de dados e conformidade

### LGPD e privacidade

O gbr-eval lida com dados de documentos financeiros. Mesmo anonimizados, eles sao tratados como **restritos**. Regras:

| Dado original | Como e protegido |
|---------------|-----------------|
| CPF (123.456.789-09) | Substituido por `000.000.000-XX` |
| CNPJ (12.345.678/0001-90) | Substituido por `00.000.000/0000-XX` |
| Nomes de pessoas reais | Substituidos por nomes ficticios |
| Nomes de empresas clientes | Substituidos (ex: "Banco Pine" vira "Banco Exemplo") |
| Enderecos | Rua e numero substituidos, cidade e estado mantidos |
| Valores monetarios | Ordem de grandeza mantida, digitos alterados |
| Emails e telefones | Substituidos por placeholders |
| CEPs | Substituidos por `00000-000` |
| RG (identidade) | Substituido por `0.000.000-X` |
| PIS/PASEP (numero trabalhista) | Substituido por `000.00000.00-0` |

**Dados pessoais reais NUNCA entram no repositorio de codigo.**

### Rastreabilidade (ISO 27001)

Cada avaliacao gera um registro completo:
- **ID unico** da execucao
- **Data e hora** de inicio e fim
- **Versao** dos golden sets e do codigo
- **Resultados** de cada grader individual
- **Hash SHA-256** do documento original (permite rastrear sem expor o conteudo)

### Classificacao de dados

| Artefato | Classificacao | Quem pode acessar |
|----------|--------------|-------------------|
| Codigo dos graders | Publico | Qualquer engenheiro |
| Configuracoes de tasks | Interno | Time de engenharia |
| Golden sets (anonimizados) | Restrito | Time de engenharia + CLO |
| Golden sets (com PII) | Proibido no repo | Ninguem — devem ser anonimizados ANTES |
| Resultados de avaliacoes | Interno | Time de engenharia + gestao |
| Rubricas do LLM-judge | Interno | Time de engenharia |

### Seguranca do LLM-judge

Quando o avaliador baseado em IA (LLM-judge) e usado, dados pessoais sao removidos automaticamente **antes** de serem enviados para a API. O sistema percorre recursivamente todos os campos e substitui padroes sensiveis (CPF, CNPJ, email, telefone, CEP).

Mensagens de erro do LLM-judge tambem sao sanitizadas — se uma excecao contiver dados pessoais (por exemplo, um CPF na mensagem de erro), eles sao removidos antes de serem armazenados no resultado da avaliacao.

---

## 16. Estado atual do projeto

### Resumo executivo (2026-04-20)

| Aspecto | Estado |
|---------|--------|
| Framework de avaliacao | **Operacional** — 28 modulos, 12 graders, runner sync e async |
| Testes do framework | **533 testes** passando, cobertura >= 80% |
| Golden sets | **40 casos** em 5 tipos de documento (meta: 150+) |
| Tarefas de avaliacao | **48 tasks** (26 produto + 22 engenharia) |
| Painel administrativo | **Operacional** — 39 paginas, 57 rotas de API |
| CI/CD | **Parcial** — testa o framework, mas ainda nao integrado aos repos de produto |
| Auditorias independentes | **6 rodadas** concluidas, todas com correcoes aplicadas |
| Primeiro cliente (Gate) | **Meta: 10/Mai/2026** (Banco Pine) |

### O que esta funcionando

- **Self-eval validado:** o sistema avaliou a si mesmo e confirmou que os graders funcionam corretamente (23/23 tasks passando, score 1.0)
- **3 execucoes gravadas:** baseline (18/abr) e duas self-evals (18 e 19/abr)
- **Deteccao de regressao:** comparacao automatica entre execucoes
- **Deteccao de tendencias:** analise de declinio ao longo do tempo (monotonica + estatistica)
- **Protecao PII:** remocao automatica de dados pessoais antes de enviar ao LLM-judge
- **Protecao ReDoS:** rejeicao de padroes regex que poderiam travar o sistema
- **Painel web:** dashboard com KPIs, historico de execucoes, gerenciamento de golden sets
- **Avaliacao com repeticao (epochs):** graders nao-deterministicos podem ser executados multiplas vezes com agregacao automatica
- **Separacao de modelos (model roles):** o modelo usado para avaliar pode ser diferente do modelo avaliado (importante para compliance)
- **Protecao contra SSRF:** o cliente HTTP valida que URLs nao apontam para servicos internos, incluindo protecao contra redirects (HTTP 301/302) para IPs internos e deteccao de IPv4-mapped IPv6
- **DNS rebinding protection:** re-resolve DNS no momento da chamada para detectar mudanca de IP publico para interno entre construcao e uso
- **CI supply chain:** todas as GitHub Actions fixadas por SHA (nao por tag mutavel)
- **Auth fail-closed:** painel rejeita acesso quando token nao configurado

### Auditorias realizadas

O framework passou por 6 rodadas de auditoria independente, onde agentes especializados (arquiteto, revisor de codigo, especialista em seguranca) analisaram o sistema com olhar critico:

| Rodada | Findings | Resultado |
|--------|----------|-----------|
| Auditoria #1 | Iniciais | Todos corrigidos |
| Auditoria #2 | Follow-up | Todos corrigidos |
| Auditoria #3 | 25 findings (3 agentes independentes) | Todos corrigidos, 37 testes adicionados |
| Auditoria #4 | ~15 findings (3 agentes frescos) | Avaliados |
| Auditoria #5 | 15 findings (1 critico, 6 altos, 8 medios) | Todos corrigidos |
| Auditoria #6 | 4 imediatos (SSRF redirect, SHA pins, exceptions, retry cap) | Todos corrigidos — 533 testes |

---

## 17. O que falta — proximos passos

### Prioridade 1 — Expandir golden sets

**Problema:** 40 casos e insuficiente para confianca estatistica.
**Meta:** 150+ casos.
**Como:** geracao sintetica assistida por IA (scripts prontos), com revisao humana de 20-30% da amostra.

### Prioridade 2 — Hashes dos documentos originais

**Problema:** os golden sets referenciam documentos reais, mas o hash SHA-256 (identificador unico do arquivo PDF) ainda nao foi calculado.
**Impacto:** rastreabilidade incompleta para auditoria ISO 27001.
**Como:** executar o script `compute_hashes.py` contra os PDFs do sistema de producao.

### Prioridade 3 — Integrar com CI dos repos de produto

**Problema:** o eval roda apenas no CI do proprio gbr-eval (testando a si mesmo). Nao esta integrado aos repos de produto.
**Impacto:** o framework e um "exercicio academico" sem conexao com o produto real.
**Como:** configurar workflow cross-repo que executa o eval contra outputs reais do ai-engine a cada PR.

### Prioridade 4 — Avaliacao online (em tempo real)

**Problema:** o eval roda apenas contra respostas pre-gravadas (offline).
**Meta:** rodar contra o produto em staging/producao em tempo real.
**Como:** adicionar HTTP client ao runner para chamadas reais ao ai-engine, com flag de gravacao para replay.

### Prioridade 5 — Calibracao do LLM-judge

**Problema:** o avaliador baseado em IA (LLM-judge) e informativo, nao bloqueante.
**Meta:** apos 50+ execucoes consistentes (auto-concordancia >= 90%), promover a bloqueante.
**Impacto:** avaliacoes de qualidade de texto (pareceres, justificativas) passam de opinativas a formais.

### Prioridade 6 — Camada de Engenharia: integracao cross-repo

**O que existe:** Code Loader implementado — os graders de engineering (`pattern_required`, `pattern_forbidden`, `convention_check`) ja conseguem verificar codigo real dos repos alvo via `gbr-eval run --code-dir /caminho/para/repo/`. A avaliacao e arquivo por arquivo, com rastreabilidade de qual arquivo violou qual regra.

**O que falta:** integracao com o CI dos 5 repos alvo (cross-repo). Cada repo precisa de um workflow que faz checkout do gbr-eval, instala dependencias, e roda `gbr-eval run --suite tasks/engineering/ --code-dir ../`.

**Como:** configurar GitHub Action nos 5 repos alvo usando a reusable action pronta em `.github/actions/gbr-eval-gate/`. Alem disso, calibrar os patterns contra repos reais para garantir zero falsos positivos.

### Timeline aproximada

| Marco | Meta | Dependencia |
|-------|------|-------------|
| Gate Fase 1 (Banco Pine) | ~10/Mai/2026 | 13 criterios atendidos |
| Primeira receita | 12/Jun/2026 | Gate aprovado |
| 10 clientes | Dez/2026 | Expansao de skills e golden sets |

---

## 18. Perguntas frequentes

### "O eval garante que a IA nunca vai errar?"

Nao. O eval garante que erros sao **detectados e quantificados**. Se a IA acerta 96% dos campos criticos, sabemos que e 96% — e podemos decidir se isso e aceitavel. Sem eval, nao sabemos nem quanto ela acerta.

### "Por que nao usar so testes tradicionais?"

Testes tradicionais verificam se o **codigo** executa sem erros. O eval verifica se o **resultado** esta correto. Uma IA pode executar sem erros e retornar um CPF completamente errado — o teste tradicional passa, mas o eval pega.

### "Quem define o que e 'correto'?"

O especialista designado para cada skill (coordenado por Diogo Dantas). A IA pode sugerir, mas a decisao final e sempre humana. Isso e fundamental para evitar "tautologia" (a IA avaliando a si mesma).

### "O que acontece quando o eval falha?"

O PR (Pull Request) e bloqueado no CI. O engenheiro precisa investigar por que falhou, corrigir o problema, e submeter novamente. Isso garante que codigo com problemas de qualidade nao chegue a producao.

### "O LLM-judge nao tem conflito de interesses? Uma IA avaliando outra IA?"

O LLM-judge usa um modelo diferente (Claude Sonnet) com uma rubrica especifica. Alem disso:
- Comeca como informativo (nao bloqueia)
- So se torna bloqueante apos provar consistencia em 50+ avaliacoes
- Dados pessoais sao removidos antes de enviar
- Criterios objetivos (campos, datas, valores) usam graders deterministicos, nao o LLM-judge

### "O sistema esta pronto para producao?"

O framework esta operacional e validado (6 auditorias independentes, 533 testes). Porem, falta integrar com os repositorios de produto e expandir os golden sets. A meta e ter tudo pronto para o Gate Fase 1 em ~10/Mai/2026.

### "Como isso ajuda na auditoria ISO 27001?"

Cada execucao do eval gera um registro completo e rastreavel (ID, timestamp, versao, resultados). Isso e evidencia auditavel de que a qualidade da IA e monitorada sistematicamente — um requisito da ISO 27001 para sistemas de IA em ambientes regulados.

### "Posso ver os resultados sem ser tecnico?"

Sim, via painel administrativo (frontend). O Dashboard mostra metricas-chave, o modulo Runs mostra historico de execucoes com graficos de tendencia, e o modulo Alerts mostra alertas ativos.

### "Como saber se a qualidade esta melhorando ou piorando?"

O modulo de tendencias analisa automaticamente as ultimas execucoes e gera alertas:
- **Declinio:** score caindo consistentemente ao longo de varias execucoes
- **Aproximacao do limiar:** score proximo do minimo de aprovacao
- **Regressao:** algo que funcionava parou de funcionar

---

## 19. Glossario

| Termo | Significado |
|-------|-------------|
| **AgentTrace** | Registro completo da execucao de um agente de IA: mensagens, chamadas de ferramenta, custos, duracao |
| **Avaliacao (eval)** | Processo de medir a qualidade de um output de IA contra uma referencia humana |
| **Camada (layer)** | Dimensao de qualidade: Engineering, Product, Operational, Compliance |
| **Case** | Um caso de teste individual dentro de um golden set |
| **CI/CD** | Integracao Continua / Entrega Continua — pipeline automatizado que testa e integra codigo |
| **CLO** | Chief Legal Officer do eval — pessoa responsavel por definir o que e "correto" |
| **Confuser** | Documento que parece ser de um tipo mas e de outro (teste de classificacao) |
| **Degradacao silenciosa** | Queda gradual de qualidade que nao e detectada porque a tarefa ainda "passa" |
| **Edge case** | Caso incomum ou extremo (documento com campos ausentes, formatos atipicos) |
| **EvalRun** | Uma execucao completa do sistema de avaliacao, com todas as tarefas e resultados |
| **Epoch** | Uma repeticao da avaliacao. Multiplos epochs permitem medir consistencia de graders nao-deterministicos |
| **F1 score** | Metrica que combina precisao (nao errar) e recall (nao esquecer). 1.0 = perfeito |
| **Gate** | Ponto de decisao go/no-go antes de integrar mudancas ao produto |
| **Golden set** | Conjunto de respostas corretas anotadas por um especialista humano |
| **GraderContext** | Contexto acumulado entre graders — permite que um grader veja resultados dos anteriores |
| **Grader** | Avaliador individual que verifica um aspecto especifico da qualidade |
| **GraderSpec** | Configuracao de um grader (qual tipo, qual campo, qual peso, e obrigatorio?) |
| **LGPD** | Lei Geral de Protecao de Dados — legislacao brasileira de privacidade |
| **Limiar (threshold)** | Score minimo para aprovacao (ex: 0.95 = 95%) |
| **LLM-judge** | Avaliador que usa IA (Claude Sonnet) para julgar qualidade de textos complexos |
| **Metadados (metadata)** | Informacoes sobre o dado (quem criou, quando, hash do original) |
| **Model role** | Papel atribuido a um modelo de IA na avaliacao. Permite usar modelos diferentes para avaliar vs ser avaliado |
| **Overall score** | Score geral de uma execucao — media dos scores individuais das tarefas |
| **PII** | Personally Identifiable Information — dados que identificam uma pessoa (CPF, nome, endereco) |
| **PR (Pull Request)** | Pedido de integracao de codigo ao projeto principal |
| **Regressao** | Quando algo que funcionava para de funcionar apos uma mudanca |
| **Reducer** | Funcao que agrega multiplos epoch scores em um unico score (media, maioria, unanimidade, etc.) |
| **Runner** | Motor que executa as avaliacoes (carrega tasks, roda graders, computa scores) |
| **Self-eval** | Modo de verificacao onde o sistema avalia as respostas corretas contra si mesmas (sanity check) |
| **Skill** | Capacidade de extrair informacoes de um tipo especifico de documento |
| **Solver** | Componente que executa um agente de IA e captura o trace completo da execucao |
| **SSRF** | Server-Side Request Forgery — ataque onde um sistema e enganado para fazer requisicoes a servicos internos |
| **Task** | Tarefa de avaliacao: define o que avaliar, com quais graders, e qual limiar |
| **Tautologia** | Quando o sistema avalia a si mesmo (comparar output com ele mesmo) — anti-padrao |
| **Tendencia (trend)** | Padrao de mudanca ao longo do tempo (ex: score caindo gradualmente) |
| **Tier** | Nivel de urgencia: Gate (bloqueia), Regression (compara), Canary (observa) |
