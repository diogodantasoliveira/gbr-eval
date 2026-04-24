#!/usr/bin/env python3
"""Sync golden sets, cases, tasks (product + engineering), and eval runs into the frontend DB.

Usage:
    python tools/sync_frontend.py [--base-url http://localhost:3002]
    python tools/sync_frontend.py --engineering-only
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]

BASE_URL = "http://localhost:3002"
ADMIN_TOKEN: str | None = None
ROOT = Path(__file__).resolve().parent.parent
PROJECT: str = "default"
GOLDEN_DIR = ROOT / "golden"
TASKS_DIR = ROOT / "tasks" / "product"
ENGINEERING_TASKS_DIR = ROOT / "tasks" / "engineering"


def _resolve_project_dirs() -> None:
    """Override GOLDEN_DIR / TASKS_DIR / ENGINEERING_TASKS_DIR when --project is set."""
    global GOLDEN_DIR, TASKS_DIR, ENGINEERING_TASKS_DIR
    if PROJECT == "default":
        return
    project_root = ROOT / "projects" / PROJECT
    if (project_root / "golden").is_dir():
        GOLDEN_DIR = project_root / "golden"
    if (project_root / "tasks" / "product").is_dir():
        TASKS_DIR = project_root / "tasks" / "product"
    if (project_root / "tasks" / "engineering").is_dir():
        ENGINEERING_TASKS_DIR = project_root / "tasks" / "engineering"


def api(method: str, path: str, data: dict | list | None = None) -> dict | list:
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if ADMIN_TOKEN:
        req.add_header("X-Admin-Token", ADMIN_TOKEN)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  ERROR {e.code}: {error_body}")
        return {"error": error_body, "status": e.code}


def get_skills() -> dict[str, str]:
    """Return mapping of doc_type → skill_id."""
    resp = api("GET", "/api/skills")
    return {s["doc_type"]: s["id"] for s in resp.get("data", [])}


def get_golden_sets() -> dict[str, dict]:
    """Return mapping of skill_id → golden set info."""
    resp = api("GET", "/api/golden-sets?limit=500")
    return {gs["skill_id"]: gs for gs in resp.get("data", [])}


def sync_golden_sets(skills: dict[str, str]) -> None:
    """Create golden sets and import cases for each skill."""
    existing_gs = get_golden_sets()

    for skill_dir in sorted(GOLDEN_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        doc_type = skill_dir.name
        skill_id = skills.get(doc_type)
        if not skill_id:
            print(f"  SKIP {doc_type} — no matching skill in DB")
            continue

        case_files = sorted(skill_dir.glob("case_[0-9]*.json"))
        if not case_files:
            print(f"  SKIP {doc_type} — no case files")
            continue

        gs = existing_gs.get(skill_id)
        if not gs:
            print(f"  CREATE golden set for {doc_type}")
            description = f"Golden set for {doc_type} — {len(case_files)} cases"
            resp = api("POST", "/api/golden-sets", {
                "skill_id": skill_id,
                "name": f"{doc_type}_golden_v1",
                "description": description,
            })
            if "error" in resp:
                print(f"  FAILED to create golden set for {doc_type}")
                continue
            gs_id = resp["id"]
        else:
            gs_id = gs["id"]
            print(f"  EXISTS golden set for {doc_type} ({gs['case_count']} cases)")

        cases = []
        for cf in case_files:
            if "example" in cf.name:
                continue
            cases.append(json.loads(cf.read_text()))

        if not cases:
            continue

        print(f"  IMPORT {len(cases)} cases into {doc_type}")
        resp = api("POST", f"/api/golden-sets/{gs_id}/import", cases)
        if isinstance(resp, dict) and "imported" in resp:
            imported = resp["imported"]
            errors = resp.get("errors", [])
            warnings = resp.get("warnings", [])
            print(f"    imported={imported}, errors={len(errors)}, pii_warnings={len(warnings)}")
        else:
            print(f"    Response: {resp}")


def _parse_yaml(path: Path) -> dict | None:
    """Parse a YAML file, trying PyYAML first then a simple fallback parser."""
    text = path.read_text()
    if yaml is not None:
        return yaml.safe_load(text)
    return _simple_yaml_parse(text)


def _simple_yaml_parse(text: str) -> dict:
    """Minimal YAML parser for flat task files (no PyYAML dependency)."""
    result: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    current_dict_list: list | None = None

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- ") and current_dict_list is not None:
            item_str = stripped[2:]
            if ":" in item_str:
                item: dict = {}
                item_key, item_val = item_str.split(":", 1)
                item[item_key.strip()] = _coerce(item_val.strip())
                current_dict_list.append(item)
            else:
                if current_list is not None:
                    current_list.append(_coerce(item_str))
            continue

        if stripped.startswith("- ") and current_list is not None:
            current_list.append(_coerce(stripped[2:]))
            continue

        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val:
                if val.startswith('"') and val.endswith('"') or val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                result[key] = _coerce(val)
                current_key = key
                current_list = None
                current_dict_list = None
            else:
                current_key = key
                result[key] = None
                current_list = None
                current_dict_list = None

        if current_key and result.get(current_key) is None:
            result[current_key] = []
            current_list = result[current_key]
            current_dict_list = result[current_key]

    return result


def _coerce(val: str) -> str | int | float | bool | None:
    if val in ("true", "True"):
        return True
    if val in ("false", "False"):
        return False
    if val in ("null", "None", "~"):
        return None
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def _yaml_to_import_payload(data: dict) -> dict:
    """Convert a parsed YAML task dict to the /api/tasks/import payload format."""
    graders = []
    for g in data.get("graders", []):
        grader_payload: dict = {
            "type": g.get("type", ""),
            "field": g.get("field"),
            "weight": g.get("weight", 1.0),
            "required": g.get("required", False),
            "config": g.get("config", {}),
        }
        if g.get("model_role"):
            grader_payload["model_role"] = g["model_role"]
        graders.append(grader_payload)

    payload: dict = {
        "task_id": data["task_id"],
        "category": data.get("category", "classification"),
        "component": data.get("component", ""),
        "layer": data.get("layer", "engineering"),
        "tier": data.get("tier", "gate"),
        "description": data.get("description", ""),
        "scoring_mode": data.get("scoring_mode", "binary"),
        "pass_threshold": data.get("pass_threshold", 1.0),
        "eval_owner": data.get("eval_owner"),
        "eval_cadence": data.get("eval_cadence"),
        "epochs": data.get("epochs", 1),
        "reducers": data.get("reducers", ["mean"]),
        "primary_reducer": data.get("primary_reducer", "mean"),
        "status": "active",
        "graders": graders,
    }

    if data.get("input"):
        payload["input"] = data["input"]

    return payload


def sync_engineering_tasks() -> None:
    """Sync engineering task YAMLs into frontend DB via import API with upsert."""
    if not ENGINEERING_TASKS_DIR.exists():
        print("  SKIP — tasks/engineering/ not found")
        return

    yaml_files = sorted(ENGINEERING_TASKS_DIR.glob("**/*.yaml"))
    if not yaml_files:
        print("  SKIP — no YAML files found")
        return

    payloads = []
    for yf in yaml_files:
        data = _parse_yaml(yf)
        if not data or "task_id" not in data:
            print(f"  SKIP {yf.name} — missing task_id")
            continue
        payloads.append(_yaml_to_import_payload(data))

    if not payloads:
        print("  No valid tasks to sync")
        return

    print(f"  Syncing {len(payloads)} engineering tasks (upsert)...")
    resp = api("POST", "/api/tasks/import?upsert=true", payloads)
    if isinstance(resp, dict):
        imported = resp.get("imported", 0)
        error_count = resp.get("error_count", 0)
        print(f"  Result: {imported} synced, {error_count} errors")
        for r in resp.get("results", []):
            print(f"    {r['status'].upper()}: {r['task_id']}")
        for e in resp.get("errors", []):
            print(f"    ERROR: {e['task_id']} — {e['error']}")
    else:
        print(f"  Unexpected response: {resp}")


def run_self_eval_and_import() -> None:
    """Run self-eval, then import the result into frontend."""
    print("\n--- Running self-eval ---")
    result = subprocess.run(
        [
            "uv", "run", "gbr-eval", "run",
            "--suite", str(TASKS_DIR),
            "--golden-dir", str(GOLDEN_DIR),
            "--self-eval",
            "--tier", "gate",
            "--output-format", "json",
        ],
        capture_output=True, text=True, cwd=ROOT,
    )

    try:
        run_data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        print(f"  Self-eval failed (exit {result.returncode})")
        print(f"  stderr: {result.stderr[:500]}")
        return

    print(f"  Gate: {run_data.get('gate_result')}, Score: {run_data.get('overall_score')}")
    print(f"  Tasks: {run_data.get('tasks_passed')}/{run_data.get('tasks_total')} passed")

    print("\n--- Importing run into frontend ---")
    resp = api("POST", "/api/runs", run_data)
    if isinstance(resp, dict) and "error" in resp:
        if resp.get("status") == 409:
            print("  Already imported (duplicate run_id)")
        else:
            print(f"  Import failed: {resp}")
    else:
        print(f"  Imported run: {resp.get('run_id', 'ok')}")


def main() -> None:
    global BASE_URL, ADMIN_TOKEN, PROJECT
    if "--base-url" in sys.argv:
        idx = sys.argv.index("--base-url")
        BASE_URL = sys.argv[idx + 1]
    if "--token" in sys.argv:
        idx = sys.argv.index("--token")
        ADMIN_TOKEN = sys.argv[idx + 1]
    elif os.environ.get("ADMIN_API_TOKEN"):
        ADMIN_TOKEN = os.environ["ADMIN_API_TOKEN"]
    if "--project" in sys.argv:
        idx = sys.argv.index("--project")
        PROJECT = sys.argv[idx + 1]
        _resolve_project_dirs()

    engineering_only = "--engineering-only" in sys.argv

    print("=== Syncing filesystem → frontend DB ===\n")

    print("--- Syncing engineering tasks ---")
    sync_engineering_tasks()

    if not engineering_only:
        print("\n--- Fetching skills ---")
        skills = get_skills()
        print(f"  Found {len(skills)} skills: {', '.join(skills.keys())}")

        print("\n--- Syncing golden sets ---")
        sync_golden_sets(skills)

        run_self_eval_and_import()

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
