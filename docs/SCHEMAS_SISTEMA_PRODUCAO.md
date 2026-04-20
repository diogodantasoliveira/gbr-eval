# Schemas e Prompts — Sistema de Producao (sistema.garantiabr.com)

> Extraido em 2026-04-18 do backoffice. Fonte de verdade para campos de extracao.

---

## 1. Matricula de Imovel (tipo 135)

**Nome:** Certidao de Matricula de Imovel - Inteiro Teor
**Categoria:** Registro de Imoveis
**Schema JSON:** VAZIO (nao definido)

**Prompt IA — Diretrizes de Extracao:**

1. Numero da Matricula
2. Endereco do Imovel (diferenciando de enderecos de outras partes)
3. Descricao do Imovel (area terreno, dimensoes, confrontacoes, benfeitorias)
4. Cadeia Dominial (proprietarios cronologicos com R/AV, data, tipo ato, dados envolvidos — nome/razao social, CPF/CNPJ, valor transacao)
5. Dados dos Ultimos 4 Registros e/ou Averbacoes (mais recente → mais antigo, com numeracao R/AV, data, tipo, envolvidos)
6. Existencia de Onus e Acoes (hipoteca, usufruto, alienacao fiduciaria, penhoras, restricoes, acoes judiciais reais/reipersecutorias — com indicacao de cancelamento)
7. Observacoes Gerais
8. Data de Emissao da Certidao

**Observacao:** Modelo complexo (usa Claude Opus no gbr-engines). Prompt focado em texto estruturado (lista de niveis), nao JSON.

---

## 2. Contrato Social / Junta Comercial (tipo 130)

**Nome:** Certidao de Inteiro Teor da Junta Comercial - sociedades empresarias, exceto as por acoes
**Categoria:** Junta Comercial
**Schema JSON:** COMPLETO (2210 chars)

```json
{
    "dados_empresa": {
        "razao_social": "string",
        "nome_fantasia": "string|null",
        "natureza_juridica": "string",
        "cnpj": "string",
        "nire": "string",
        "endereco_sede": "string",
        "data_inicio_atividades": "string (formato: dd/mm/aaaa)",
        "objeto_social": "string"
    },
    "capital_social": {
        "valor_capital": "string (ex: R$ 1.000.000,00)",
        "moeda": "string",
        "quantidade_quotas": "string (ex: 1.000.000 quotas)",
        "valor_nominal_quota": "string (ex: R$ 1,00 por quota)"
    },
    "socios": [
        {
            "nome_completo": "string",
            "cpf": "string",
            "qualificacao": "string",
            "participacao_quotas": "string (ex: 50.000 quotas)",
            "participacao_valor": "string (ex: R$ 50.000,00)",
            "participacao_percentual": "string (ex: 5%)"
        }
    ],
    "administradores": [
        {
            "nome_completo": "string|null",
            "cpf": "string|null",
            "forma_atuacao": "string (conjunta/isolada/conforme clausula)"
        }
    ],
    "alteracoes_contratuais": [
        {
            "data": "string (formato: dd/mm/aaaa)",
            "numero": "string",
            "assunto": "string"
        }
    ],
    "situacao_atual": {
        "status": "string|null"
    },
    "observacoes_gerais": {
        "prazo_duracao_sociedade": "string",
        "data_constituicao": "string (formato: dd/mm/aaaa)",
        "nire_consultado": "string",
        "data_ultima_atualizacao": "string (formato: dd/mm/aaaa)",
        "consulta_autenticidade": "string (URL)"
    },
    "assinatura_certidao": {
        "assinante": "string",
        "data_hora_assinatura": "string (ex: 16/07/2025 as 11:47:49)",
        "codigo_autenticidade": "string",
        "validade": "string"
    }
}
```

---

## 3. CND Federal (tipo 96)

**Nome:** Certidao Negativa de Debitos Relativos a Tributos Federais e a Divida Ativa da Uniao - CND Federal
**Categoria:** Governo Federal
**Schema JSON:** VAZIO

**Prompt IA — Diretrizes de Extracao:**

1. Tipo de Certidao (negativa / positiva / positiva com efeito de negativa)
2. Dados do Contribuinte (nome ou razao social, CPF ou CNPJ)
3. Situacao do Contribuinte (se possui debitos inscritos em divida ativa, texto da regularidade fiscal)
4. Orgao Emissor
5. Data e Hora de Emissao

**Observacao:** Documento simples, campos padronizados. Nao menciona explicitamente: numero da certidao, data de validade, codigo de validacao — que existem no prompt do gbr-engines.

---

## 4. Procuracao / Traslado (tipo 146)

**Nome:** Certidao de Traslado de Procuracao
**Categoria:** Tabelionato de Notas
**Schema JSON:** VAZIO

**Prompt IA — Diretrizes de Extracao:**

1. Dados do Tabelionato (nome, endereco, tabeliao)
2. Dados do Outorgante (nome, CPF/CNPJ, nacionalidade, estado civil, profissao, endereco; se PJ: razao social, CNPJ, representante legal)
3. Dados do Outorgado (idem outorgante; se ha mais de um outorgado)
4. Poderes Conferidos (genericos ou especificos; representacao em juizo, administracao bens, movimentacao financeira, contratos; limitacoes/condicoes)
5. Prazo de Validade (determinado/indeterminado; data inicio/termino; revogacao/renuncia)
6. Substabelecimento (autorizado? quais poderes? nomeacao de substabelecidos?)
7. Finalidade da Procuracao (representacao judicial, administracao imoveis, gestao empresarial)
8. Observacoes Gerais
9. Data de Emissao

---

## 5. Balanco Patrimonial (tipo 293)

**Nome:** Balanco Patrimonial - Demonstracoes Contabeis
**Categoria:** Outros Orgaos
**Schema JSON:** VAZIO

**Prompt IA — Diretrizes de Extracao:**

1. Identificacao da Empresa (razao social, CNPJ, data encerramento)
2. Ativo Circulante (disponibilidades, creditos, estoques, demais ativos curto prazo)
3. Ativo Nao Circulante (realizavel LP, imobilizado, intangiveis, depreciacoes/amortizacoes)
4. Composicao do Imobilizado (moveis, utensilios, veiculos, equipamentos, terrenos, edificacoes)
5. Passivo Circulante (obrigacoes trabalhistas, tributarias, fornecedores, emprestimos CP)
6. Passivo Nao Circulante (emprestimos LP, provisoes, obrigacoes fiscais diferidas)
7. Patrimonio Liquido (capital social, reservas, lucros/prejuizos acumulados, resultado exercicio)
8. Verificacao contabil: ativo total == passivo total + PL
9. Comparacao entre exercicios quando houver multiplos periodos

**Observacao:** Prompt pede comparacao entre exercicios. Verificacao de equacao fundamental (A = P + PL) e obrigatoria.

---

## Resumo: Schema JSON por Tipo

| Tipo | ID | Prompt | Schema JSON |
|------|-----|--------|-------------|
| Matricula | 135 | SIM (8 diretrizes) | VAZIO |
| Contrato Social | 130 | SIM | COMPLETO |
| CND Federal | 96 | SIM (5 diretrizes) | VAZIO |
| Procuracao | 146 | SIM (9 diretrizes) | VAZIO |
| Balanco | 293 | SIM (9 diretrizes) | VAZIO |

Apenas o Contrato Social (Junta Comercial) tem schema JSON definido no sistema.
