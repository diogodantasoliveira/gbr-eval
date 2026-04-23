# gbr-eval

Eval-first quality framework for GarantiaBR products. Defines and verifies the quality criteria that every new construction must meet from day one.

This is the **backend / CLI**. The admin panel lives in a sibling repo: [gbr-eval-frontend](https://github.com/diogodantasoliveira/gbr-eval-frontend). The recommended setup is to clone both side-by-side and run them together.

Layout after the recommended setup:

```
your-workspace/
├── gbr-eval/            ← this repo (Python, pytest, uv, CLI runner)
└── gbr-eval-frontend/   ← sibling repo (Next.js 16, SQLite, admin panel)
```

## Prerequisites

| Tool | Minimum | Check / install |
|------|---------|-----------------|
| Git | any recent | `git --version` |
| Python | 3.12 | `python3 --version` |
| uv (Python package manager) | 0.11 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js (for the frontend) | 20 | `node --version` |
| pnpm (for the frontend) | 10 | `corepack enable pnpm && corepack prepare pnpm@latest --activate` |

Everything else (pytest, ruff, mypy, drizzle, better-sqlite3, …) is installed by the setup steps below — do not install anything globally.

## One-shot setup (recommended for new developers)

Run the bootstrap script from anywhere — it clones both repos into the current directory, installs everything, seeds the database, and leaves you with a verified working system.

```bash
# From the folder that will hold the two repos side-by-side (e.g. ~/dev/)
curl -O https://raw.githubusercontent.com/diogodantasoliveira/gbr-eval/main/setup-local.sh
chmod +x setup-local.sh
./setup-local.sh
```

At the end you'll have:

- `gbr-eval/` with `uv sync --all-extras` complete and **725+ tests passing**
- `gbr-eval-frontend/` with `node_modules`, native builds, and a SQLite DB at `./gbr-eval.db`
- SQLite seeded with: **5 P0 skills**, **5 golden sets (40 cases)**, **39 engineering tasks**, **18 convention rules**, and **4 eval runs** (3 historical + 1 fresh self-eval)
- A generated `.env.local` with a random `WEBHOOK_SECRET`

From there:

```bash
cd gbr-eval-frontend
pnpm dev
# -> open http://localhost:3002
```

## Manual setup (if you prefer step-by-step)

### 1. Clone both repos side-by-side

```bash
mkdir -p ~/dev && cd ~/dev
git clone git@github.com:diogodantasoliveira/gbr-eval.git
git clone git@github.com:diogodantasoliveira/gbr-eval-frontend.git
```

### 2. Backend

```bash
cd gbr-eval
uv sync --all-extras
uv run pytest                    # expect: all passed (725+)
```

### 3. Frontend

```bash
cd ../gbr-eval-frontend
cp .env.example .env.local       # edit if needed — defaults are fine for local dev
pnpm install
pnpm db:push                     # creates ./gbr-eval.db and 24 tables
pnpm db:seed                     # inserts 5 P0 skills + 40 field schemas
pnpm dev                         # http://localhost:3002
```

### 4. Populate the rest of the data

In a second terminal, with the dev server still running:

```bash
cd ../gbr-eval

# Golden sets + engineering tasks + one fresh self-eval run
uv run python tools/sync_frontend.py --base-url http://localhost:3002

# 18 convention rules from gbr-engines CLAUDE.md
curl -X POST http://localhost:3002/api/conventions/import-claude-md \
     -H 'Content-Type: application/json' -d '{}'

# Historical eval runs (baseline + earlier self-evals)
SECRET=$(grep ^WEBHOOK_SECRET ../gbr-eval-frontend/.env.local | cut -d= -f2-)
for f in runs/*.json; do
  python3 -c "import json,sys; d=json.load(open('$f'))
for k in ('tier','finished_at','gate_result'):
    if d.get(k) is None: d.pop(k,None)
if d.get('baseline_run_id') is None: d.pop('baseline_run_id',None)
print(json.dumps(d))" | \
  curl -sS -X POST http://localhost:3002/api/runs/webhook \
       -H "Authorization: Bearer $SECRET" \
       -H 'Content-Type: application/json' \
       --data-binary @- && echo
done
```

## Verifying the install

After setup, open these and confirm the counts:

| URL | Expected |
|---|---|
| http://localhost:3002 | Dashboard loads, no errors |
| http://localhost:3002/skills | **5** skills |
| http://localhost:3002/golden-sets | **5** sets (each with **8** cases) |
| http://localhost:3002/tasks | **39** engineering tasks |
| http://localhost:3002/runs | **4** runs (gate GO for the recent ones) |
| http://localhost:3002/conventions | **18** rules |

Backend quality gates (run from `gbr-eval/`):

```bash
uv run pytest                                              # 725+ passed
uv run ruff check .                                        # All checks passed!
uv run mypy src/                                           # no issues
uv run gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval
# -> Total: 31 | Pass: 31 | Overall: ≥90% | GO
```

## Day-to-day commands

### Backend

```bash
uv run pytest                                              # all tests
uv run pytest tests/graders/test_deterministic.py          # one file
uv run pytest -k test_exact_match                          # by name
uv run pytest --cov=src/gbr_eval --cov-report=term-missing # coverage (>= 80%)

uv run ruff check .                                        # lint
uv run mypy src/                                           # types

# Run an eval suite
uv run gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval
uv run gbr-eval run --task tasks/product/extraction/matricula_cpf.yaml --golden-dir golden/ --self-eval

# Evaluate engineering conventions in a target repo
uv run gbr-eval run --suite tasks/engineering/atom-back-end/ --code-dir ~/repos/atom-back-end/

# Online eval (real endpoint)
uv run gbr-eval run --task <task.yaml> --endpoint https://ai-engine.staging.garantiabr.com --tenant my-tenant

# Trends / analyze
uv run gbr-eval trends --runs-dir runs/
uv run gbr-eval analyze --runs-dir runs/
```

### Sync changes back to the frontend DB

After editing tasks, golden sets, or committing a new run:

```bash
# From gbr-eval/, with the frontend running
uv run python tools/sync_frontend.py --base-url http://localhost:3002
```

## Where to go next

- **`CLAUDE.md`** — project invariants, autonomy rules, commit conventions, LGPD, data classification. Read this before your first PR.
- **`docs/MANUAL_ENGENHEIRO.md`** — definitive technical reference (1,400 lines). Pydantic models, grader protocols, runner flow, CLI, golden-set taxonomy, frontend architecture.
- **`docs/PORTS.md`** — single source of truth for ports (3002 only).
- **`docs/PLAN-ONBOARDING-EVAL.md`** — the parallel-eval pilot against the Atom onboarding flow.
- **`docs/BACKEND_ROADMAP.md`** / **`docs/FRONTEND_ROADMAP.md`** — what's shipped vs planned.
- **`PRD.md`** — product requirements.
- **`.claude/rules/00-eval-principles.md`** — the non-negotiables (zero tautology, pure graders, golden sets annotated by humans).

## Troubleshooting

**`pnpm install` skipped native builds; frontend crashes at runtime on `better_sqlite3`.**
`pnpm.onlyBuiltDependencies` in `gbr-eval-frontend/package.json` lists the deps that need compilation. If you're on an old pnpm or the list was stripped, run `npm rebuild better-sqlite3` inside the frontend repo as a fallback. Don't run `npm install` — the project is pnpm-only.

**Frontend shows HTTP 500 on `/api/*` with "Could not parse module '[project]/src/middleware.ts'".**
Stale Turbopack cache. Kill the dev server, run `rm -rf .next`, restart `pnpm dev`.

**`/api/*` returns 503 "Server authentication not configured".**
`ADMIN_API_TOKEN` is unset AND `DISABLE_AUTH=true` is also unset. For local dev the generated `.env.local` sets `DISABLE_AUTH=true`. Copy from `.env.example` if missing.

**`/api/runs/webhook` returns 503 "Webhook not configured".**
`WEBHOOK_SECRET` is empty. Generate one: `openssl rand -hex 32` and put it in `gbr-eval-frontend/.env.local`.

**Webhook returns 422 Validation failed on old run JSONs.**
The frontend's `importRunSchema` uses `z.string().optional()` for `tier` / `finished_at` / `gate_result`, which rejects `null`. Strip the null keys before POSTing (see "Historical eval runs" above).

**`gbr-eval run --endpoint http://localhost:...` errors "SSRF protection: endpoint resolves to internal IP".**
Add `--allow-internal` for local development.

**`uv run pytest` fails with "No such file or directory: pytest".**
You ran it from the wrong directory. Must be inside `gbr-eval/`. uv is workdir-sensitive.

## Project conventions

- **Branches:** `tipo/descricao-curta` (e.g. `feat/grader-field-f1`, `fix/runner-timeout`).
- **Commits:** Conventional Commits — `tipo(escopo): mensagem`. Scopes: `graders`, `harness`, `contracts`, `golden`, `calibration`, `tasks`, `docs`, `ci`, `frontend`.
- **PR title:** `[EVAL] tipo: descricao`.
- **Never push directly to `main`** — always through PR. See `CLAUDE.md` §Regras de autonomia for the full list.
- **Never commit** PII, credentials, raw documents, or non-anonymized golden sets. The frontend has PII redaction enforced at the schema level; the backend has an `ANTHROPIC_API_KEY`-only env surface.

## License

Internal — GarantiaBR. See `CLAUDE.md` for data-classification rules.
