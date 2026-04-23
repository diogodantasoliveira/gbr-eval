#!/usr/bin/env python3
"""Evaluate PRs against engineering tasks and push results to the frontend.

Usage:
    # Single PR by number (fetches from GitHub)
    python tools/eval_pr.py --repo atom-back-end --pr 94

    # Multiple PRs
    python tools/eval_pr.py --repo atom-back-end --pr 94 95 96 70

    # Local branch (no GitHub fetch)
    python tools/eval_pr.py --repo atom-back-end --branch my-feature

    # All open PRs from GitHub
    python tools/eval_pr.py --repo atom-back-end --all-open

    # Changed files only (faster, compares to main)
    python tools/eval_pr.py --repo atom-back-end --pr 94 --changed-only

    # Skip webhook push (just generate JSONs)
    python tools/eval_pr.py --repo atom-back-end --pr 94 --no-push

    # Custom frontend URL
    python tools/eval_pr.py --repo atom-back-end --pr 94 --frontend-url http://localhost:3002

Requires:
    - ANTHROPIC_API_KEY env var (for LLM graders)
    - WEBHOOK_SECRET env var or --webhook-secret flag (for pushing to frontend)
    - gh CLI (for --pr and --all-open, fetching from GitHub)
    - Target repo cloned at REPOS_DIR/<repo>/ (default: parent of gbr-eval)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPOS_DIR = ROOT.parent
DEFAULT_FRONTEND_URL = "http://localhost:3002"
RUNS_DIR = ROOT / "runs"


@dataclass
class PRTarget:
    repo: str
    ref: str
    pr_number: int | None = None
    title: str = ""


@dataclass
class EvalResult:
    target: PRTarget
    json_path: Path | None = None
    score: float = 0.0
    gate: str = ""
    tasks_passed: int = 0
    tasks_total: int = 0
    pushed: bool = False
    error: str | None = None


def run_cmd(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def fetch_pr_branch(repo_path: Path, pr_number: int) -> str:
    """Fetch a PR branch from GitHub using gh CLI."""
    branch = f"pr{pr_number}"
    result = run_cmd(
        ["gh", "pr", "checkout", str(pr_number), "--branch", branch],
        cwd=repo_path,
    )
    if result.returncode != 0:
        result = run_cmd(
            ["git", "fetch", "origin", f"pull/{pr_number}/head:{branch}"],
            cwd=repo_path,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch PR #{pr_number}: {result.stderr}")
    return branch


def checkout_branch(repo_path: Path, branch: str) -> None:
    result = run_cmd(["git", "checkout", branch], cwd=repo_path)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to checkout {branch}: {result.stderr}")


def get_open_prs(repo_path: Path) -> list[dict[str, Any]]:
    result = run_cmd(
        ["gh", "pr", "list", "--json", "number,title,headRefName", "--limit", "50"],
        cwd=repo_path,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to list PRs: {result.stderr}")
    return json.loads(result.stdout)


def get_pr_title(repo_path: Path, pr_number: int) -> str:
    result = run_cmd(
        ["gh", "pr", "view", str(pr_number), "--json", "title"],
        cwd=repo_path,
    )
    if result.returncode == 0:
        return json.loads(result.stdout).get("title", "")
    return ""


def run_eval(
    repo: str,
    repos_dir: Path,
    output_file: Path,
    *,
    changed_only: bool = False,
    base_branch: str = "main",
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run the eval suite and return the JSON result."""
    cmd = [
        sys.executable, "-c",
        "from gbr_eval.harness.runner import cli; cli(standalone_mode=False)",
        "run",
        "--suite", str(ROOT / "tasks" / "engineering" / repo),
        "--code-dir", str(repos_dir),
        "--output-format", "json",
        "--output-file", str(output_file),
        "-y",
    ]
    if changed_only:
        cmd.extend(["--changed-only", "--base-branch", base_branch])
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={**os.environ},
    )

    if output_file.exists():
        return json.loads(output_file.read_text())

    if result.stderr:
        raise RuntimeError(f"Eval failed:\n{result.stderr[-1000:]}")
    raise RuntimeError(f"Eval produced no output (exit {result.returncode})")


def push_to_frontend(
    json_path: Path,
    frontend_url: str,
    webhook_secret: str,
) -> bool:
    url = f"{frontend_url}/api/runs/webhook"
    data = json_path.read_bytes()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {webhook_secret}")
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            return body.get("imported", False)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if e.code == 409:
            print(f"    (duplicate — already in frontend)")
            return True
        print(f"    Push failed HTTP {e.code}: {error_body}")
        return False


def eval_pr_target(
    target: PRTarget,
    repos_dir: Path,
    *,
    changed_only: bool,
    no_push: bool,
    frontend_url: str,
    webhook_secret: str,
) -> EvalResult:
    result = EvalResult(target=target)
    repo_path = repos_dir / target.repo

    if not repo_path.is_dir():
        result.error = f"Repo not found at {repo_path}"
        return result

    try:
        checkout_branch(repo_path, target.ref)
    except RuntimeError as e:
        result.error = str(e)
        return result

    suffix = f"pr{target.pr_number}" if target.pr_number else target.ref
    output_file = RUNS_DIR / f"{target.repo}_{suffix}.json"
    RUNS_DIR.mkdir(exist_ok=True)

    try:
        data = run_eval(
            target.repo.replace("-", "-"),
            repos_dir,
            output_file,
            changed_only=changed_only,
        )
    except RuntimeError as e:
        result.error = str(e)
        return result

    result.json_path = output_file
    result.score = data.get("overall_score", 0)
    result.gate = data.get("gate_result", "?")
    result.tasks_passed = data.get("tasks_passed", 0)
    result.tasks_total = data.get("tasks_total", 0)

    if not no_push and webhook_secret:
        result.pushed = push_to_frontend(output_file, frontend_url, webhook_secret)

    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate PRs and push to frontend")
    parser.add_argument("--repo", required=True, help="Target repo name (e.g. atom-back-end)")
    parser.add_argument("--pr", nargs="+", type=int, help="PR number(s) to evaluate")
    parser.add_argument("--branch", help="Local branch to evaluate (instead of --pr)")
    parser.add_argument("--all-open", action="store_true", help="Evaluate all open PRs")
    parser.add_argument("--repos-dir", type=Path, default=DEFAULT_REPOS_DIR,
                        help=f"Parent dir containing repos (default: {DEFAULT_REPOS_DIR})")
    parser.add_argument("--frontend-url", default=DEFAULT_FRONTEND_URL)
    parser.add_argument("--webhook-secret", default=os.environ.get("WEBHOOK_SECRET", ""))
    parser.add_argument("--changed-only", action="store_true",
                        help="Only eval changed files vs main")
    parser.add_argument("--no-push", action="store_true", help="Skip pushing to frontend")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not args.no_push and not args.webhook_secret:
        frontend_env = args.repos_dir / "gbr-eval-frontend" / ".env.local"
        if frontend_env.exists():
            for line in frontend_env.read_text().splitlines():
                if line.startswith("WEBHOOK_SECRET="):
                    args.webhook_secret = line.split("=", 1)[1].strip()
                    break
        if not args.webhook_secret:
            print("WARNING: No WEBHOOK_SECRET — results won't be pushed to frontend", file=sys.stderr)

    repo_path = args.repos_dir / args.repo

    targets: list[PRTarget] = []
    if args.all_open:
        prs = get_open_prs(repo_path)
        for pr in prs:
            branch = fetch_pr_branch(repo_path, pr["number"])
            targets.append(PRTarget(
                repo=args.repo, ref=branch,
                pr_number=pr["number"], title=pr["title"],
            ))
    elif args.pr:
        for pr_num in args.pr:
            branch = f"pr{pr_num}"
            existing = run_cmd(["git", "branch", "--list", branch], cwd=repo_path)
            if branch not in existing.stdout:
                try:
                    branch = fetch_pr_branch(repo_path, pr_num)
                except RuntimeError as e:
                    print(f"SKIP PR #{pr_num}: {e}")
                    continue
            title = get_pr_title(repo_path, pr_num)
            targets.append(PRTarget(repo=args.repo, ref=branch, pr_number=pr_num, title=title))
    elif args.branch:
        targets.append(PRTarget(repo=args.repo, ref=args.branch))
    else:
        parser.error("Specify --pr, --branch, or --all-open")

    if not targets:
        print("No targets to evaluate")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  gbr-eval PR Analysis — {args.repo}")
    print(f"  {len(targets)} target(s)")
    print(f"{'='*60}\n")

    results: list[EvalResult] = []
    for i, target in enumerate(targets, 1):
        label = f"PR #{target.pr_number}" if target.pr_number else target.ref
        print(f"[{i}/{len(targets)}] {label}: {target.title}")
        r = eval_pr_target(
            target,
            args.repos_dir,
            changed_only=args.changed_only,
            no_push=args.no_push,
            frontend_url=args.frontend_url,
            webhook_secret=args.webhook_secret,
        )
        results.append(r)

        if r.error:
            print(f"    ERROR: {r.error}")
        else:
            gate_icon = {"go": "✓", "conditional_go": "~", "no_go": "✗", "no_go_absolute": "✗✗"}.get(r.gate, "?")
            push_status = " → frontend ✓" if r.pushed else ""
            print(f"    {gate_icon} {r.gate.upper()} — {r.score*100:.1f}% ({r.tasks_passed}/{r.tasks_total} passed){push_status}")
        print()

    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")
    for r in results:
        label = f"PR #{r.target.pr_number}" if r.target.pr_number else r.target.ref
        if r.error:
            print(f"  {label:>10s}  ERROR: {r.error[:60]}")
        else:
            print(f"  {label:>10s}  {r.gate.upper():>16s}  {r.score*100:5.1f}%  {r.tasks_passed}/{r.tasks_total}")
    print()


if __name__ == "__main__":
    main()
