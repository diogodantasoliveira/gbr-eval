#!/usr/bin/env python3
"""Check that frontend schema stays in sync with backend models.

Compares enum values and model fields between:
  - src/gbr_eval/harness/models.py (backend — source of truth)
  - frontend/src/lib/validations/task.ts (frontend Zod schemas)
  - frontend/src/db/schema.ts (frontend Drizzle DB schema)

Usage:
    uv run python tools/check_schema_sync.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_MODELS = ROOT / "src" / "gbr_eval" / "harness" / "models.py"
FRONTEND_VALIDATIONS = ROOT / "frontend" / "src" / "lib" / "validations" / "task.ts"
FRONTEND_DB_SCHEMA = ROOT / "frontend" / "src" / "db" / "schema.ts"


def _extract_strenum_values(source: str, enum_name: str) -> set[str]:
    pattern = rf"class {enum_name}\(StrEnum\):\s*\n((?:\s+\w+\s*=\s*\"[^\"]+\"\s*\n)+)"
    m = re.search(pattern, source)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def _extract_zod_enum_values(source: str, var_name: str) -> set[str]:
    pattern = rf'{var_name}\s*=\s*z\.enum\(\[(.*?)\]\)'
    m = re.search(pattern, source, re.DOTALL)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def _extract_pydantic_fields(source: str, class_name: str) -> set[str]:
    pattern = rf"class {class_name}\(BaseModel\):\s*\n((?:[ \t]+\S.*\n|[ \t]*\n)*)"
    m = re.search(pattern, source)
    if not m:
        return set()
    body = m.group(1)
    fields: set[str] = set()
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("@") or stripped.startswith("def "):
            continue
        fm = re.match(r"(\w+)\s*:", stripped)
        if fm and not stripped.startswith("class "):
            fields.add(fm.group(1))
    return fields


def _extract_drizzle_columns(source: str, table_var: str) -> set[str]:
    pattern = rf'(?:export\s+)?(?:const\s+)?{table_var}\s*=\s*sqliteTable\(\s*"[^"]+"\s*,\s*\{{'
    m = re.search(pattern, source)
    if not m:
        return set()
    start = m.end()
    depth = 1
    i = start
    while i < len(source) and depth > 0:
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    body = source[start : i - 1]
    columns: set[str] = set()
    for line in body.split("\n"):
        cm = re.match(r"\s+(\w+)\s*:", line)
        if cm:
            columns.add(cm.group(1))
    return columns


def main() -> int:
    errors: list[str] = []

    if not BACKEND_MODELS.exists():
        print(f"ERROR: Backend models not found: {BACKEND_MODELS}")
        return 1
    if not FRONTEND_VALIDATIONS.exists():
        print(f"ERROR: Frontend validations not found: {FRONTEND_VALIDATIONS}")
        return 1
    if not FRONTEND_DB_SCHEMA.exists():
        print(f"ERROR: Frontend DB schema not found: {FRONTEND_DB_SCHEMA}")
        return 1

    backend = BACKEND_MODELS.read_text()
    validations = FRONTEND_VALIDATIONS.read_text()
    db_schema = FRONTEND_DB_SCHEMA.read_text()

    enum_checks: list[tuple[str, str]] = [
        ("Category", "categoryEnum"),
        ("Layer", "layerEnum"),
        ("Tier", "tierEnum"),
        ("ScoringMode", "scoringModeEnum"),
        ("ScoreReducer", "scoreReducerEnum"),
    ]

    for backend_enum, frontend_var in enum_checks:
        be_vals = _extract_strenum_values(backend, backend_enum)
        fe_vals = _extract_zod_enum_values(validations, frontend_var)

        if not be_vals:
            errors.append(f"WARN: Could not parse backend enum {backend_enum}")
            continue
        if not fe_vals:
            errors.append(f"WARN: Could not parse frontend enum {frontend_var}")
            continue

        missing_in_fe = be_vals - fe_vals
        extra_in_fe = fe_vals - be_vals

        if missing_in_fe:
            errors.append(f"ENUM {backend_enum}: missing in frontend {frontend_var}: {sorted(missing_in_fe)}")
        if extra_in_fe:
            errors.append(f"ENUM {backend_enum}: extra in frontend {frontend_var}: {sorted(extra_in_fe)}")

    grader_registry_file = ROOT / "src" / "gbr_eval" / "graders"
    be_graders: set[str] = set()
    for gf in grader_registry_file.glob("*.py"):
        content = gf.read_text()
        be_graders.update(re.findall(r'@register_grader\("([^"]+)"', content))

    fe_graders = _extract_zod_enum_values(validations, "graderTypeEnum")
    if be_graders and fe_graders:
        missing_graders = be_graders - fe_graders
        extra_graders = fe_graders - be_graders
        if missing_graders:
            errors.append(f"GRADERS: missing in frontend graderTypeEnum: {sorted(missing_graders)}")
        if extra_graders:
            errors.append(f"GRADERS: extra in frontend graderTypeEnum: {sorted(extra_graders)}")

    task_be = _extract_pydantic_fields(backend, "Task")
    task_db = _extract_drizzle_columns(db_schema, "tasks")

    skip_be = {"input", "expected", "graders"}
    skip_db = {"id", "created_at", "updated_at"}
    task_be_compare = task_be - skip_be
    task_db_compare = task_db - skip_db

    missing_in_db = task_be_compare - task_db_compare
    if missing_in_db:
        errors.append(f"TASK FIELDS: in backend Task but not in DB tasks table: {sorted(missing_in_db)}")

    grader_be = _extract_pydantic_fields(backend, "GraderSpec")
    grader_db = _extract_drizzle_columns(db_schema, "task_graders")
    skip_grader_be = {"type"}
    skip_grader_db = {"id", "task_id", "grader_type"}
    grader_be_compare = grader_be - skip_grader_be
    grader_db_compare = grader_db - skip_grader_db

    missing_grader_db = grader_be_compare - grader_db_compare
    if missing_grader_db:
        errors.append(f"GRADER FIELDS: in backend GraderSpec but not in DB task_graders: {sorted(missing_grader_db)}")

    if errors:
        print("Schema sync check FAILED:\n")
        for e in errors:
            print(f"  - {e}")
        print(f"\n{len(errors)} issue(s) found.")
        return 1

    print("Schema sync check PASSED — backend and frontend are aligned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
