#!/usr/bin/env python3
"""Generate engineering task YAMLs from convention rules in the frontend DB.

Usage:
    python tools/generate_task_from_rule.py --rule-name <name> --repo <repo> [--scan-target "**/*.py"]
    python tools/generate_task_from_rule.py --all --repo <repo>
    python tools/generate_task_from_rule.py --list
"""

import json
import sys
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:3002"
ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks" / "engineering"


def api_get(path: str) -> list | dict:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def rule_to_yaml(rule: dict, repo: str, scan_target: str = "**/*.py") -> str:
    """Convert a convention rule to a task YAML string."""
    name = rule["name"]
    # Sanitize name for task_id: replace colons with dots
    safe_name = name.replace(":", "_")
    repo_slug = repo.replace("-", "_").replace(" ", "_")
    task_id = f"eng.{repo_slug}.{safe_name}"

    detection_type = rule.get("detection_type", "regex")
    pattern = rule.get("detection_pattern", "")
    description = rule.get("description", name)

    if detection_type == "regex" and pattern:
        # Convention rules that check for forbidden patterns
        forbidden_keywords = ["forbidden", "no_", "not_", "never", "avoid"]
        is_forbidden = any(kw in name.lower() for kw in forbidden_keywords)

        grader_type = "pattern_forbidden" if is_forbidden else "pattern_required"

        # Escape quotes in pattern for YAML
        escaped_pattern = pattern.replace('"', '\\"')

        lines = [
            f'task_id: {task_id}',
            'category: classification',
            f'component: {repo}',
            'layer: engineering',
            'tier: gate',
            f'description: "{description}"',
            'input:',
            '  payload:',
            f'    repo: {repo}',
            f'    scan_target: "{scan_target}"',
            'expected:',
            f'  convention: {safe_name}',
            'graders:',
            f'  - type: {grader_type}',
            f'    field: {safe_name}',
            '    weight: 1.0',
            '    required: true',
            '    config:',
            f'      pattern: "{escaped_pattern}"',
            '      file_key: content',
            'scoring_mode: binary',
            'pass_threshold: 1.0',
            'eval_owner: diogo.dantas',
            'eval_cadence: per-pr',
        ]
    elif detection_type == "llm_judge":
        lines = [
            f'task_id: {task_id}',
            'category: classification',
            f'component: {repo}',
            'layer: engineering',
            'tier: gate',
            f'description: "{description}"',
            '# NOTE: This rule uses llm_judge detection - needs manual review',
            f'# Convention: {name}',
            '# Detection: llm_judge (semantic, not regex)',
            'input:',
            '  payload:',
            f'    repo: {repo}',
            f'    scan_target: "{scan_target}"',
            'expected:',
            f'  convention: {safe_name}',
            'graders:',
            '  - type: llm_judge',
            f'    field: {safe_name}',
            '    weight: 1.0',
            '    required: false',
            '    config:',
            '      rubric_id: ""',
            '      model: "claude-sonnet-4-5-20250514"',
            'scoring_mode: binary',
            'pass_threshold: 1.0',
            'eval_owner: diogo.dantas',
            'eval_cadence: per-pr',
        ]
    else:
        lines = [
            f'task_id: {task_id}',
            f'# NOTE: detection_type={detection_type} — needs manual implementation',
            'category: classification',
            f'component: {repo}',
            'layer: engineering',
            'tier: gate',
            f'description: "{description}"',
        ]

    return "\n".join(lines) + "\n"


def list_rules():
    """List all convention rules from the API."""
    rules = api_get("/api/conventions")
    if not isinstance(rules, list):
        rules = rules.get("data", [])

    print(f"{'Name':<45} {'Category':<18} {'Severity':<10} {'Detection':<10}")
    print("-" * 90)
    for r in rules:
        print(f"{r['name']:<45} {r['category']:<18} {r['severity']:<10} {r['detection_type']:<10}")
    print(f"\nTotal: {len(rules)} rules")


def generate(rule_name: str | None, repo: str, scan_target: str, gen_all: bool):
    """Generate task YAML(s) from convention rule(s)."""
    rules = api_get("/api/conventions")
    if not isinstance(rules, list):
        rules = rules.get("data", [])

    if not gen_all:
        rules = [r for r in rules if r["name"] == rule_name]
        if not rules:
            print(f"Rule '{rule_name}' not found")
            sys.exit(1)

    repo_dir = TASKS_DIR / repo
    repo_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    for rule in rules:
        yaml_content = rule_to_yaml(rule, repo, scan_target)
        safe_name = rule["name"].replace(":", "_")
        out_path = repo_dir / f"{safe_name}.yaml"

        if out_path.exists():
            print(f"  SKIP {out_path.name} (already exists)")
            continue

        out_path.write_text(yaml_content)
        print(f"  CREATED {out_path.name}")
        generated += 1

    print(f"\nGenerated {generated} task YAML(s) in {repo_dir}")


def main():
    args = sys.argv[1:]

    if "--list" in args:
        list_rules()
        return

    if "--base-url" in args:
        global BASE_URL
        idx = args.index("--base-url")
        BASE_URL = args[idx + 1]

    gen_all = "--all" in args
    rule_name = None
    repo = None
    scan_target = "**/*.py"

    if "--rule-name" in args:
        idx = args.index("--rule-name")
        rule_name = args[idx + 1]

    if "--repo" in args:
        idx = args.index("--repo")
        repo = args[idx + 1]

    if "--scan-target" in args:
        idx = args.index("--scan-target")
        scan_target = args[idx + 1]

    if not repo:
        print("Error: --repo is required")
        print("Usage: python tools/generate_task_from_rule.py --rule-name <name> --repo <repo>")
        sys.exit(1)

    if not gen_all and not rule_name:
        print("Error: --rule-name or --all is required")
        sys.exit(1)

    generate(rule_name, repo, scan_target, gen_all)


if __name__ == "__main__":
    main()
