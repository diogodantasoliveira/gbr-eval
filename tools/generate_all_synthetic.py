#!/usr/bin/env python3
"""One-shot: generate all synthetic golden set cases + sync to frontend.

Usage:
    # 1. Configure (once)
    cp .env.example .env
    # Edit .env: set ANTHROPIC_API_KEY and optionally GBR_EVAL_SYNTH_MODEL

    # 2. Preview (dry-run, no API call, shows plan only)
    uv run python tools/generate_all_synthetic.py

    # 3. Generate everything
    uv run python tools/generate_all_synthetic.py --apply

    # 4. Custom model
    uv run python tools/generate_all_synthetic.py --apply --model claude-sonnet-4-5-20250929

Environment variables:
    ANTHROPIC_API_KEY       — Required. Your Anthropic API key.
    GBR_EVAL_SYNTH_MODEL    — Optional. Override default model (default: claude-sonnet-4-5-20250929).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

ROOT = Path(__file__).resolve().parent.parent
GENERATE_SCRIPT = ROOT / "tools" / "generate_synthetic.py"
SYNC_SCRIPT = ROOT / "tools" / "sync_frontend.py"

GENERATION_PLAN = [
    {"category": "positive", "count": 15, "description": "Positivos sintéticos (75 cases)"},
    {"category": "confuser", "count": 5, "description": "Confusers sintéticos (25 cases)"},
    {"category": "edge_case", "count": 4, "description": "Edge cases sintéticos (20 cases)"},
]


_ALLOWED_ENV_KEYS = {"ANTHROPIC_API_KEY", "GBR_EVAL_SYNTH_MODEL", "GBR_EVAL_GOLDEN_STORE"}


def _load_dotenv() -> None:
    """Load .env file if it exists (no dependency needed)."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key in _ALLOWED_ENV_KEYS and key not in os.environ:
                os.environ[key] = value


def _check_prereqs() -> tuple[str, str]:
    """Check prerequisites, return (api_key, model)."""
    _load_dotenv()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-api-key-here":
        click.echo("ERROR: ANTHROPIC_API_KEY not set.", err=True)
        click.echo("  Configure it in .env or export ANTHROPIC_API_KEY=sk-ant-...", err=True)
        sys.exit(1)

    model = os.environ.get("GBR_EVAL_SYNTH_MODEL", "claude-sonnet-4-5-20250929")
    return api_key, model


def _count_existing(golden_dir: Path) -> dict[str, int]:
    """Count existing cases by category."""
    counts: dict[str, int] = {"seed": 0, "confuser": 0, "edge_case": 0, "synthetic": 0}
    for f in sorted(golden_dir.rglob("case_[0-9]*.json")):
        if "example" in f.name:
            continue
        import json
        data = json.loads(f.read_text())
        tags = data.get("tags", [])
        if "synthetic" in tags:
            counts["synthetic"] += 1
        elif "confuser" in tags:
            counts["confuser"] += 1
        elif "edge_case" in tags:
            counts["edge_case"] += 1
        else:
            counts["seed"] += 1
    return counts


@click.command()
@click.option("--apply", is_flag=True, default=False, help="Generate and write (dry-run by default)")
@click.option("--model", default=None, help="Override Claude model (default: env or claude-sonnet-4-5-20250929)")
@click.option("--sync/--no-sync", default=True, help="Sync to frontend after generation (default: yes)")
@click.option("--golden-dir", type=click.Path(path_type=Path), default=ROOT / "golden")
def main(apply: bool, model: str | None, sync: bool, golden_dir: Path) -> None:
    """Generate all synthetic golden set cases and sync to frontend."""

    click.echo("=" * 60)
    click.echo("  gbr-eval — Synthetic Golden Set Generator")
    click.echo("=" * 60)

    if apply:
        api_key, default_model = _check_prereqs()
        final_model = model or default_model
        click.echo("  API Key: configured")
        click.echo(f"  Model:   {final_model}")
    else:
        final_model = model or os.environ.get("GBR_EVAL_SYNTH_MODEL", "claude-sonnet-4-5-20250929")
        click.echo("\n  Mode:    DRY-RUN (no API calls)")
        click.echo(f"  Model:   {final_model}")

    existing = _count_existing(golden_dir)
    click.echo("\n  Current inventory:")
    click.echo(f"    Seed (human):     {existing['seed']}")
    click.echo(f"    Confuser (human): {existing['confuser']}")
    click.echo(f"    Edge case (human):{existing['edge_case']}")
    click.echo(f"    Synthetic:        {existing['synthetic']}")
    total_before = sum(existing.values())
    click.echo(f"    Total:            {total_before}")

    click.echo("\n  Generation plan:")
    total_new = 0
    for step in GENERATION_PLAN:
        n = step["count"] * 5  # 5 skills
        total_new += n
        click.echo(f"    {step['description']}")
    click.echo("    ─────────────────────────────")
    click.echo(f"    Total new cases: {total_new}")
    click.echo(f"    Grand total:     {total_before + total_new}")

    if not apply:
        click.echo("\n  DRY-RUN complete. Run with --apply to generate.")
        click.echo("  Estimated API cost: ~$2-4 (Sonnet) or ~$8-15 (Opus)")
        return

    click.echo(f"\n{'─' * 60}")
    for step in GENERATION_PLAN:
        click.echo(f"\n>>> {step['description']}")
        cmd = [
            sys.executable, str(GENERATE_SCRIPT),
            "--golden-dir", str(golden_dir),
            "--all",
            "--count", str(step["count"]),
            "--category", step["category"],
            "--model", final_model,
            "--apply",
        ]
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            click.echo(f"\n  ERROR: Generation failed for {step['category']}", err=True)
            sys.exit(1)

    final = _count_existing(golden_dir)
    click.echo(f"\n{'=' * 60}")
    click.echo("  Generation complete!")
    click.echo(f"    Seed:      {final['seed']}")
    click.echo(f"    Confuser:  {final['confuser']}")
    click.echo(f"    Edge case: {final['edge_case']}")
    click.echo(f"    Synthetic: {final['synthetic']}")
    click.echo(f"    Total:     {sum(final.values())}")

    if sync:
        click.echo("\n>>> Syncing to frontend...")
        subprocess.run([sys.executable, str(SYNC_SCRIPT)], cwd=ROOT)

    click.echo("\n  NEXT STEP: CLO review required.")
    click.echo("  Review 20-30% of synthetic cases in the frontend.")
    click.echo("  Mark reviewed cases: reviewed_by → 'diogo.dantas'")


if __name__ == "__main__":
    main()
