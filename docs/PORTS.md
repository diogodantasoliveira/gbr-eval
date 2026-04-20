# Registro de portas — gbr-eval

Porta e serviço são fixos. Nenhum componente do sistema deve usar "próxima porta livre" ou default do framework. Mudar uma porta aqui exige mudar também em todos os locais listados na coluna "Onde está fixada".

## Portas locais

| Porta | Serviço | Repo | Onde está fixada |
|-------|---------|------|------------------|
| **3002** | Frontend admin panel (Next.js dev e start) | `gbr-eval-frontend` | `package.json` scripts `dev` e `start` (`-p 3002`), `.env.example` (`PORT=3002`) |

O backend (`gbr-eval`) **não** expõe portas. É um CLI (`gbr-eval run`, `gbr-eval trends`, `gbr-eval analyze`) e um pacote Python importado em testes. Não há servidor HTTP próprio.

## Portas externas (targets, não nossas)

Estes são endereços de serviços externos que o CLI pode consumir via `--endpoint`. Não são portas do gbr-eval — apenas documentamos como referência.

| Porta | Serviço externo | Flag CLI |
|-------|-----------------|----------|
| 8000  | gbr-engines ai-engine (dev local) | `gbr-eval run --endpoint http://localhost:8000 --allow-internal` |

`--allow-internal` é obrigatório para endpoints em faixas RFC1918 / loopback / link-local. Sem ele o `EvalClient` bloqueia a requisição por SSRF guard.

## Regras

1. **Sem auto-discover.** Nunca usar "primeira porta livre", `PORT=0`, ou equivalente.
2. **Sem default do framework.** `next dev` e `next start` sem `-p` caem em 3000 — não aceitar.
3. **Fonte única da verdade:** este arquivo + `.env.example`. Se o Next ou outra ferramenta exigir a porta em mais um lugar, adicionar à tabela "Onde está fixada".
4. **Mudanças de porta** passam por PR revisado — porque afetam docs, CI, webhooks e onboarding de qualquer engenheiro novo.
