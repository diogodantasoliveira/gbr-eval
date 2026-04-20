# Engineering Eval Guide

How to work with the engineering quality layer in gbr-eval.

## Quick Start

```bash
# Sync engineering tasks to frontend
uv run python tools/sync_frontend.py --engineering-only

# List convention rules
uv run python tools/generate_task_from_rule.py --list

# Generate a task from a convention rule
uv run python tools/generate_task_from_rule.py --rule-name "security:jwt_custom_roles_claim" --repo atom-back-end

# Run engineering eval against a local repo
uv run python -m gbr_eval.harness.runner run --suite tasks/engineering/atom-back-end/

# Capture contract schemas from running services
uv run python tools/capture_schemas.py --all

# Check for contract drift
uv run python tools/check_contract_drift.py
```

## Architecture

### Four-layer quality model

| Layer | What it checks | Graders |
|-------|---------------|---------|
| Engineering | Code follows conventions per repo | pattern_required, pattern_forbidden, convention_check |
| Product | AI outputs match golden sets | exact_match, field_f1, llm_judge, etc. |
| Operational | SLAs, cost, availability | numeric_range (future) |
| Compliance | LGPD, BACEN, audit trail | (future) |

### Engineering graders

| Grader | Purpose | Config |
|--------|---------|--------|
| `pattern_required` | Regex MUST match in code | `{ pattern, file_key }` |
| `pattern_forbidden` | Regex must NOT match in code | `{ pattern, file_key }` |
| `convention_check` | Multi-rule: combines required + forbidden | `{ rules: [{pattern, type, description}], file_key }` |

All engineering graders have ReDoS protection (catastrophic backtracking guard, max pattern 1000 chars, max input 100K chars).

### Code Loader

`src/gbr_eval/harness/code_loader.py` loads repo files for evaluation:

1. Resolves repo path securely (no directory traversal)
2. Globs files matching `scan_target` (e.g. `**/*.py`)
3. Filters: max 1MB/file, max 10K files, UTF-8 only
4. Returns sorted `(relative_path, content)` tuples

### Convention Rules → Tasks Pipeline

Convention rules live in the frontend SQLite DB (18 rules seeded from gbr-engines CLAUDE.md).
Each rule can generate an engineering task YAML:

```
Convention Rule (DB) → generate_task_from_rule.py → YAML → sync_frontend.py → DB Task
                                                         ↓
                                                    /api/conventions/{id}/generate-task → DB Task
```

## Adding a Convention Rule

1. Go to http://localhost:3002/conventions/new
2. Fill in: name, category, severity, detection type, pattern
3. Add positive/negative examples
4. Save → rule appears in the convention list

## Generating a Task from a Rule

### Via CLI
```bash
uv run python tools/generate_task_from_rule.py \
  --rule-name "security:jwt_custom_roles_claim" \
  --repo atom-back-end \
  --scan-target "**/*.py"
```

### Via Frontend
1. Go to the convention detail page
2. Click "Generate Task"
3. Select target repo and scan pattern
4. Click "Create Task"

### Via Coverage Matrix
1. Go to http://localhost:3002/conventions/coverage
2. See which rules lack tasks
3. Click to generate missing ones

## Contract Testing

Schema snapshots live in `contracts/schemas/`. When a target repo changes its API schema without updating the snapshot, CI detects drift.

```bash
# Capture fresh schemas from running services
uv run python tools/capture_schemas.py --all

# Check for drift against committed versions
uv run python tools/check_contract_drift.py
```

## 5 Target Repositories

| Repo | Domain | Tasks | Key Conventions |
|------|--------|-------|----------------|
| atom-back-end | Backoffice | 4 | tenant_id filter, RBAC, audit log, sensitive data |
| engine-billing | Billing | 4 | Decimal not float, idempotency, audit trail, reconciliation |
| engine-integracao | Integrations | 5 | Retry/backoff, circuit breaker, configurable timeout, no credentials, credential vault |
| garantia_ia | AI/Prompts | 4 | Prompt versioned, PII sanitized, output schema, cost tracking |
| notifier | Notifications | 4 | Template approved, idempotent send, LGPD opt-out, rate limiting |

**Total: 21 engineering tasks across 5 repos.**

## CI Integration

The CI pipeline at `.github/workflows/ci.yml` has two stages:

1. **quality**: lint + type check + tests (coverage >= 80%)
2. **eval-gate**: self-eval against golden sets + regression detection

Engineering eval tasks run as part of the eval-gate stage when targeting engineering task suites.
