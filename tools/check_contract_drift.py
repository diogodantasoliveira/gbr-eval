#!/usr/bin/env python3
"""Check for contract drift between schema snapshots and git history.

Compares current schemas against the last committed version.
If schemas changed without a corresponding update to the version/title, warns.

Usage:
    python tools/check_contract_drift.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "contracts" / "schemas"


def get_committed_schema(path: Path) -> dict | None:
    """Get the last committed version of a schema file."""
    rel = path.relative_to(ROOT)
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return None


def compare_schemas(current: dict, committed: dict) -> list[str]:
    """Compare two schemas and return list of drift issues."""
    issues = []

    current_required = set(current.get("required", []))
    committed_required = set(committed.get("required", []))

    added_required = current_required - committed_required
    removed_required = committed_required - current_required

    if added_required:
        issues.append(f"New required fields: {', '.join(sorted(added_required))}")
    if removed_required:
        issues.append(f"Removed required fields: {', '.join(sorted(removed_required))}")

    current_props = set(current.get("properties", {}).keys())
    committed_props = set(committed.get("properties", {}).keys())

    removed_props = committed_props - current_props
    if removed_props:
        issues.append(f"Removed properties: {', '.join(sorted(removed_props))}")

    for prop in current_props & committed_props:
        curr_type = current["properties"][prop].get("type")
        comm_type = committed["properties"][prop].get("type")
        if curr_type != comm_type:
            issues.append(f"Type changed for '{prop}': {comm_type} → {curr_type}")

    return issues


def main() -> None:
    print("=== Contract Drift Detection ===\n")

    schemas = sorted(SCHEMAS_DIR.glob("*.json"))
    if not schemas:
        print("No schemas found.")
        sys.exit(0)

    total_issues = 0

    for path in schemas:
        try:
            with open(path) as f:
                current = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"ERROR: {path.name} — {e}")
            total_issues += 1
            continue

        committed = get_committed_schema(path)
        if committed is None:
            print(f"NEW: {path.name} (no committed version)")
            continue

        issues = compare_schemas(current, committed)
        if issues:
            print(f"DRIFT: {path.name}")
            for issue in issues:
                print(f"  - {issue}")
            total_issues += len(issues)
        else:
            print(f"OK: {path.name}")

    print(f"\n{total_issues} drift issue(s) found.")
    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
