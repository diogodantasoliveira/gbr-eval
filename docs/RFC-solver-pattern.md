# RFC: Solver / AgentTrace Pattern for gbr-eval

**Status:** Draft
**Author:** Diogo Dantas (CAIO)
**Date:** 2026-04-20
**Depends on:** PR4 (GraderContext)

## 1. Motivation

Today gbr-eval evaluates **WHAT** (the output) but not **HOW** (the trajectory).
For audit requirements at Itau ("did the agent consult ONR before deciding?"),
we need the complete agent trace: which tools were called, in what order, what
the intermediate results were, and how the final output was assembled.

The inspect_ai project solves this with a `Solver` abstraction that captures
the full conversation and tool-call history into a structured `AgentTrace`.

### Use cases

1. **Compliance audit:** prove that the agent followed the required decision
   sequence (e.g., consulted ONR registry before emitting a parecer).
2. **Cost attribution:** track per-task cost from the trace, enabling
   `cost_limit` graders.
3. **Trajectory grading:** verify that specific tools were called (or not
   called) during execution, independent of final output correctness.
4. **Debugging:** replay exact agent trajectories to reproduce failures.

## 2. Design

### 2.1 Core models (`src/gbr_eval/solvers/models.py`)

```python
class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    duration_ms: float = 0.0
    timestamp: datetime | None = None

class Message(BaseModel):
    role: str  # "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    timestamp: datetime | None = None

class AgentTrace(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    started_at: datetime | None = None
    finished_at: datetime | None = None
```

### 2.2 Solver protocol (`src/gbr_eval/solvers/base.py`)

```python
class Solver(Protocol):
    async def solve(self, task_input: TaskInput, trace: AgentTrace) -> AgentTrace: ...
```

Solvers are async because agent execution involves I/O-bound tool calls.
The existing sync runner remains unchanged.

### 2.3 Grading architecture

No adapter in `base.grade()` — the async runner extracts `trace.output` before
grading and passes trace metadata via `GraderContext.metadata`:

```python
extra_metadata = {"has_trace": True, "tool_calls_count": len(trace.tool_calls)}
grader_results, score, duration_ms = _run_single_epoch(
    task, output, model_roles=model_roles, extra_metadata=extra_metadata,
)
```

Key design decisions (post-audit):

- **ContextAwareGrader Protocol:** Separate from `Grader` Protocol. Not
  `@runtime_checkable` because both have `grade()` and isinstance cannot
  distinguish signatures that differ only in keyword arguments. Runtime
  dispatch uses `_CONTEXT_AWARE` registry set populated via
  `register_grader(name, context_aware=True)`.
- **model_roles via GraderContext:** Passed in `context.metadata["model_roles"]`,
  not injected into `spec.config`. LLMJudge reads from context; deterministic
  graders never see it.
- **Shared grading loop:** Both sync `run_task()` and async
  `run_task_with_solver()` delegate to `_run_single_epoch()` from `runner.py`.
  The async runner passes solver-specific metadata via `extra_metadata`.

### 2.4 Async runner (`src/gbr_eval/harness/async_runner.py`)

New file, does not modify the sync runner. Supports multi-epoch with
deterministic short-circuit (same logic as sync runner):

```python
async def run_task_with_solver(
    task: Task,
    solver: Solver,
    *,
    model_roles: dict[str, str] | None = None,
) -> TaskResult:
    trace = AgentTrace(started_at=datetime.now(UTC))
    trace = await solver.solve(task.input, trace)
    trace.finished_at = datetime.now(UTC)
    output = trace.output
    # Uses _run_single_epoch from runner.py (shared grading loop)
    # Epoch loop with deterministic short-circuit
    ...
```

### 2.5 PassthroughSolver

Default solver that does nothing — wraps pre-computed output into a trace:

```python
@register_solver("passthrough")
class PassthroughSolver:
    async def solve(self, task_input, trace):
        return trace
```

## 3. PII considerations

Traces may contain PII from intermediate tool results. The same `_sanitize_pii`
function from `model_judge.py` must be applied before:

- Logging traces
- Sending traces to external systems
- Including trace data in grader prompts

## 4. Storage

Traces are serialized as JSON blobs. Two options:

- **File system:** `runs/{run_id}/traces/{task_id}.json` (current approach)
- **Database:** `solver_traces` table in frontend SQLite (for admin panel)

Both options are supported; the runner writes to file, the frontend imports
from file to DB.

## 5. Future trace-aware graders

These are NOT part of the initial implementation but inform the design:

- `tool_usage`: verifies a specific tool was called N times
- `trajectory_check`: verifies a sequence of actions occurred in order
- `cost_limit`: `trace.cost_usd <= threshold`

## 6. Scope and timeline

**Prerequisites:**
- Gate 10/mai must be complete
- Pipeline Fase 17 must exist (agent execution infrastructure)

**Implementation phases:**
1. Models + registry + passthrough solver (~2 days)
2. Async runner + adapter in base.grade() (~2 days)
3. CLI `--solver` option + trace storage (~1 day)
4. First trace-aware grader (tool_usage) (~2 days)

**Not in scope:**
- Actual agent solvers (these live in gbr-engines, not gbr-eval)
- Production trace collection (infrastructure concern)
- Trace visualization in admin panel (separate frontend PR)

## 7. Backward compatibility

- `solvers/` is an entirely new package — additive only
- `async_runner.py` is a new file — does not modify `runner.py`
- The adapter in `base.grade()` detects `AgentTrace` silently
- No existing test changes required
- No existing YAML changes required
- Existing graders continue to work unchanged
