#!/usr/bin/env python3
"""Capture OpenAPI schemas from running services into contract snapshots.

Usage:
    python tools/capture_schemas.py [--service NAME] [--all]

When services are not running, validates existing snapshots are well-formed.
"""

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "contracts" / "schemas"

SERVICES = {
    "engine-integracao": {"url": "http://localhost:8001/openapi.json", "snapshot": "engine_integracao_extract.json"},
    "garantia-ia": {"url": "http://localhost:8002/openapi.json", "snapshot": "garantia_ia_inference.json"},
    "notifier": {"url": "http://localhost:8003/openapi.json", "snapshot": "notifier_event.json"},
    "engine-billing": {"url": "http://localhost:8004/openapi.json", "snapshot": "engine_billing_event.json"},
    "atom-back-end": {"url": "http://localhost:8005/openapi.json", "snapshot": "atom_backend_query.json"},
}


def validate_schema(path: Path) -> bool:
    """Check that a schema file is valid JSON with required fields.

    Accepts both JSON Schema (top-level $schema/title) and OpenAPI 3.x
    documents (info.title).
    """
    try:
        with open(path) as f:
            schema = json.load(f)
        # JSON Schema format
        if "$schema" in schema or "title" in schema:
            print(f"  OK: {path.name} ({schema.get('title', 'untitled')})")
            return True
        # OpenAPI 3.x format
        if "openapi" in schema and isinstance(schema.get("info"), dict):
            title = schema["info"].get("title", "untitled")
            print(f"  OK: {path.name} (OpenAPI: {title})")
            return True
        print(f"  WARN: {path.name} missing $schema/title or openapi/info")
        return False
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  FAIL: {path.name} — {e}")
        return False


def capture_from_service(name: str, config: dict) -> bool:
    """Try to fetch OpenAPI spec from a running service."""
    url = config["url"]
    snapshot = SCHEMAS_DIR / config["snapshot"]
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        with open(snapshot, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  CAPTURED: {name} → {snapshot.name}")
        return True
    except Exception as e:
        print(f"  SKIP: {name} not reachable ({e})")
        return False


def main() -> None:
    args = sys.argv[1:]

    if "--all" in args or not args:
        print("=== Contract Schema Capture ===\n")

        print("Attempting live capture...")
        captured = 0
        for name, config in SERVICES.items():
            if capture_from_service(name, config):
                captured += 1

        print(f"\nCaptured {captured}/{len(SERVICES)} from live services.\n")

        print("Validating all snapshots...")
        valid = 0
        total = 0
        for path in sorted(SCHEMAS_DIR.glob("*.json")):
            total += 1
            if validate_schema(path):
                valid += 1

        print(f"\n{valid}/{total} schemas valid.")
        sys.exit(0 if valid == total else 1)

    elif "--service" in args:
        idx = args.index("--service")
        if idx + 1 >= len(args):
            print("Usage: --service NAME")
            sys.exit(1)
        name = args[idx + 1]
        if name not in SERVICES:
            print(f"Unknown service: {name}. Available: {', '.join(SERVICES)}")
            sys.exit(1)
        if not capture_from_service(name, SERVICES[name]):
            print("Falling back to validation...")
            snapshot = SCHEMAS_DIR / SERVICES[name]["snapshot"]
            if snapshot.exists():
                validate_schema(snapshot)
            else:
                print(f"  No snapshot found at {snapshot}")
                sys.exit(1)


if __name__ == "__main__":
    main()
