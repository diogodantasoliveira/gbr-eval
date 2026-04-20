# Plano: Fechar Gaps Frontend vs Backend

> Data: 2026-04-20
> Status: Em execucao

## Ordem de implementacao

| Ordem | Gap | Prioridade | Escopo |
|-------|-----|-----------|--------|
| 1 | GAP 8 | MEDIO | Config schemas incompletos (task.ts, grader-picker) |
| 2 | GAP 1 | ALTO | 3 graders engenharia no enum + picker |
| 3 | GAP 2 | ALTO | epochs/reducers/primary_reducer (DB + form + API) |
| 4 | GAP 3 | MEDIO | model_role no GraderSpec (DB + form) |
| 5 | GAP 5 | BAIXO | eval_owner, eval_cadence (DB + form) |
| 6 | GAP 6 | ALTO | reducer_scores, epoch_scores nos resultados |
| 7 | GAP 9 | BAIXO | file_path no GraderResult |
| 8 | GAP 4 | BAIXO | golden_set_tags na task |
| 9 | GAP 7 | MEDIO | AgentTrace/Solver (futuro) |
| 10 | Prevencao | N/A | check_schema_sync.py |

## db:push agrupados

- Apos GAPs 2+3+5: tasks + task_graders
- Apos GAP 6: eval_task_results
- Apos GAP 4: tasks (golden_set_tags)
- Apos GAP 7: nova tabela agent_traces
