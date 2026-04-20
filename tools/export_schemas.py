"""Export Pydantic model schemas to JSON Schema files for contract validation."""

import json
from pathlib import Path

from gbr_eval.harness.models import EvalRun, GraderResult, Task, TaskResult

SCHEMA_DIR = Path(__file__).parent.parent / "contracts" / "schemas"

MODELS = {
    "eval_run": EvalRun,
    "task": Task,
    "task_result": TaskResult,
    "grader_result": GraderResult,
}


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema = model.model_json_schema()
        path = SCHEMA_DIR / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2) + "\n")
        print(f"Exported {name} -> {path}")


if __name__ == "__main__":
    main()
