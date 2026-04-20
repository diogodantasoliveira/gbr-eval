#!/usr/bin/env python3
"""Generate synthetic golden set cases from seed cases using Claude.

The generator calls Claude in a SEPARATE context (no access to eval code)
to create plausible variations of seed cases. This approach was validated
by Anthropic engineers as safe and non-tautological.

Usage:
    # Preview what would be generated (dry-run)
    python tools/generate_synthetic.py --golden-dir golden/ --skill matricula --count 5

    # Generate and write to disk
    python tools/generate_synthetic.py --golden-dir golden/ --skill matricula --count 15 --apply

    # Generate for all skills
    python tools/generate_synthetic.py --golden-dir golden/ --all --count 15 --apply

    # Generate negative examples (confusers + edge cases)
    python tools/generate_synthetic.py --golden-dir golden/ --skill cnd --count 5 --category confuser --apply
    python tools/generate_synthetic.py --golden-dir golden/ --skill cnd --count 5 --category edge_case --apply

Requires ANTHROPIC_API_KEY env var.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import anthropic
import click

SKILLS = ["matricula", "contrato_social", "cnd", "procuracao", "certidao_trabalhista"]

CATEGORY_RANGES = {
    "positive": (6, 99),
    "confuser": (100, 199),
    "edge_case": (200, 299),
    "degraded": (300, 399),
}

_DEFAULT_MODEL = os.environ.get("GBR_EVAL_SYNTH_MODEL", "claude-sonnet-4-5-20250929")


def _load_seed_cases(golden_dir: Path, skill: str) -> list[dict]:
    skill_dir = golden_dir / skill
    cases = []
    for f in sorted(skill_dir.glob("case_[0-9]*.json")):
        with open(f) as fh:
            cases.append(json.load(fh))
    return cases


def _load_metadata(golden_dir: Path, skill: str) -> dict:
    meta_path = golden_dir / skill / "metadata.yaml"
    if not meta_path.exists():
        return {}
    import yaml

    with open(meta_path) as f:
        return yaml.safe_load(f) or {}


def _next_case_number(golden_dir: Path, skill: str, category: str) -> int:
    low, high = CATEGORY_RANGES[category]
    skill_dir = golden_dir / skill
    existing = set()
    for f in skill_dir.glob("case_*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
                num = data.get("case_number", 0)
                if low <= num <= high:
                    existing.add(num)
        except (json.JSONDecodeError, KeyError):
            continue
    for n in range(low, high + 1):
        if n not in existing:
            return n
    raise ValueError(f"No available case numbers in range {low}-{high} for {skill}/{category}")


def _build_prompt(seed_cases: list[dict], metadata: dict, skill: str, count: int, category: str) -> str:
    seeds_json = json.dumps(seed_cases[:3], indent=2, ensure_ascii=False)
    meta_json = json.dumps(metadata, indent=2, ensure_ascii=False)

    if category == "positive":
        return _positive_prompt(seeds_json, meta_json, skill, count)
    elif category == "confuser":
        return _confuser_prompt(seeds_json, meta_json, skill, count)
    elif category == "edge_case":
        return _edge_case_prompt(seeds_json, meta_json, skill, count)
    elif category == "degraded":
        return _degraded_prompt(seeds_json, meta_json, skill, count)
    else:
        raise ValueError(f"Unknown category: {category}")


def _positive_prompt(seeds_json: str, meta_json: str, skill: str, count: int) -> str:
    return f"""You are generating synthetic golden set cases for a document evaluation system.
Your job is to create {count} NEW realistic variations of the seed cases below.

SKILL: {skill}
METADATA (field weights and types):
{meta_json}

SEED CASES (use these as structural templates):
{seeds_json}

RULES:
1. Each case must have the EXACT same JSON structure as the seeds
2. Vary: field values (names, CPFs, CNPJs, dates, amounts), array sizes, tags
3. Keep values PLAUSIBLE for Brazilian financial documents
4. CPFs must use format 000.000.000-XX (anonymized, last 2 digits vary)
5. CNPJs must use format 00.000.000/0001-XX (anonymized)
6. Names must be realistic Portuguese names (fictional, never real people)
7. Dates between 2023-2026, amounts in realistic ranges for the document type
8. Each case needs DIFFERENT tags showing what makes it unique
9. citation excerpts must be plausible document text matching the expected_output
10. Set "document_hash": "sha256:PENDING_COMPUTE"
11. Set "annotator": "diogo.dantas", "reviewed_by": null
12. Set "document_source": "synthetic:{skill}:{{case_number}}"
13. Do NOT include "source" field - the tags will contain "synthetic"
14. Tags MUST include "synthetic" as first tag (replacing "seed")
15. Vary the DIVERSITY: mix PF/PJ, different regions, different statuses

Return ONLY a JSON array of {count} case objects. No explanation, no markdown."""


def _confuser_prompt(seeds_json: str, meta_json: str, skill: str, count: int) -> str:
    confuser_map: dict[str, tuple[str, str]] = {
        "matricula": (
            "IPTU, escritura de compra e venda, certidão de ônus",
            "iptu, escritura, certidao_onus",
        ),
        "contrato_social": (
            "alteração contratual, estatuto social S.A., ata de assembleia",
            "alteracao_contratual, estatuto_social, ata_assembleia",
        ),
        "cnd": (
            "certidão de casamento, certidão distribuição cível, certidão de óbito",
            "certidao_casamento, certidao_civel, certidao_obito",
        ),
        "procuracao": (
            "substabelecimento, termo de representação, carta de preposto",
            "substabelecimento, termo_representacao, carta_preposto",
        ),
        "certidao_trabalhista": (
            "certidão distribuição cível, certidão criminal, certidão de objeto e pé",
            "certidao_civel, certidao_criminal, certidao_objeto_pe",
        ),
    }
    doc_types, type_slugs = confuser_map.get(skill, ("documento genérico", "documento_generico"))

    return f"""You are generating NEGATIVE (confuser) golden set cases for a document evaluation system.

SKILL BEING TESTED: {skill}
CONFUSER DOCUMENTS: {doc_types}

These are documents that LOOK SIMILAR to {skill} but are DIFFERENT document types.
The AI system should REJECT these as not being {skill}.

METADATA (what {skill} fields look like):
{meta_json}

REFERENCE SEED (positive cases — to understand the format):
{seeds_json}

RULES:
1. Generate {count} confuser cases
2. expected_output.document_type must be the ACTUAL type (e.g., "iptu", NOT "{skill}")
3. expected_output should contain fields that the ACTUAL document type would have
4. Tags MUST include: "synthetic", "negative", "confuser", "<actual_type>_como_{skill}"
5. citation excerpts should come from the CONFUSER document (not from {skill})
6. The confuser document should be plausible — real field names and values
7. Set "annotator": "diogo.dantas", "reviewed_by": null
8. Set "document_source": "synthetic:confuser_{skill}:{{case_number}}"
9. Set "document_hash": "sha256:PENDING_COMPUTE"
10. Vary the confuser types across: {type_slugs}

Return ONLY a JSON array of {count} case objects. No explanation, no markdown."""


def _edge_case_prompt(seeds_json: str, meta_json: str, skill: str, count: int) -> str:
    return f"""You are generating EDGE CASE golden set cases for a document evaluation system.

SKILL: {skill}
These are documents that ARE the correct type ({skill}) but have unusual characteristics:
- Missing fields (set to null)
- Unusual formats
- Boundary values (very old dates, very large/small amounts)
- Incomplete data

METADATA:
{meta_json}

SEED CASES (normal positive cases):
{seeds_json}

RULES:
1. Generate {count} edge cases
2. expected_output.document_type = "{skill}" (correct type)
3. At least one field should be null or unusual per case
4. Tags MUST include: "synthetic", "negative", "edge_case", description of what's unusual
5. notes field must explain WHY this is an edge case
6. citation should reflect the actual document content (including missing fields)
7. For null fields, citation can say "Campo nao localizado no documento"
8. Set "annotator": "diogo.dantas", "reviewed_by": null
9. Set "document_source": "synthetic:edge_{skill}:{{case_number}}"
10. Set "document_hash": "sha256:PENDING_COMPUTE"

Return ONLY a JSON array of {count} case objects. No explanation, no markdown."""


def _degraded_prompt(seeds_json: str, meta_json: str, skill: str, count: int) -> str:
    return f"""You are generating DEGRADED QUALITY golden set cases for a document evaluation system.

SKILL: {skill}
These are documents that ARE the correct type ({skill}) but have LOW QUALITY input:
- OCR errors in field values (typos, wrong characters)
- Missing fields due to scan cutoff
- Partially legible content

METADATA:
{meta_json}

SEED CASES (normal cases):
{seeds_json}

RULES:
1. Generate {count} degraded cases
2. expected_output.document_type = "{skill}" (correct type)
3. Some fields should be null (unreadable) or contain OCR artifacts
4. Tags MUST include: "synthetic", "negative", "degraded", degradation type
5. Degradation types: "ocr_ruim", "scan_cortado", "baixa_resolucao", "manchas"
6. notes must describe the degradation
7. citation excerpts should reflect the degraded quality
8. Set "annotator": "diogo.dantas", "reviewed_by": null
9. Set "document_source": "synthetic:degraded_{skill}:{{case_number}}"
10. Set "document_hash": "sha256:PENDING_COMPUTE"

Return ONLY a JSON array of {count} case objects. No explanation, no markdown."""


def _generate_cases(
    seed_cases: list[dict],
    metadata: dict,
    skill: str,
    count: int,
    category: str,
    model: str,
) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        click.echo("ERROR: ANTHROPIC_API_KEY not set", err=True)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(seed_cases, metadata, skill, count, category)

    click.echo(f"  Calling {model} for {count} {category} cases...")
    response = client.messages.create(
        model=model,
        max_tokens=16384,
        temperature=0.8,
        messages=[{"role": "user", "content": prompt}],
    )

    block = response.content[0]
    if block.type != "text":
        raise ValueError("Unexpected response block type from Claude")
    text: str = block.text.strip()  # type: ignore[union-attr]
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]

    cases = json.loads(text)
    if not isinstance(cases, list):
        raise ValueError("Expected JSON array from Claude")

    return cases


def _assign_case_numbers(cases: list[dict], golden_dir: Path, skill: str, category: str) -> list[dict]:
    start = _next_case_number(golden_dir, skill, category)
    for i, case in enumerate(cases):
        case["case_number"] = start + i
        if "synthetic" not in case.get("tags", []):
            case.setdefault("tags", []).insert(0, "synthetic")
        case["document_hash"] = "sha256:PENDING_COMPUTE"
        case["annotator"] = "diogo.dantas"
        case["reviewed_by"] = None
        case["created_at"] = datetime.now(UTC).isoformat()
    return cases


def _write_cases(cases: list[dict], golden_dir: Path, skill: str) -> list[Path]:
    skill_dir = golden_dir / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for case in cases:
        num = case["case_number"]
        path = skill_dir / f"case_{num:03d}.json"
        with open(path, "w") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)
            f.write("\n")
        paths.append(path)
    return paths


@click.command()
@click.option("--golden-dir", type=click.Path(path_type=Path), default=Path("golden"))
@click.option("--skill", type=click.Choice(SKILLS), help="Skill to generate for")
@click.option("--all", "all_skills", is_flag=True, help="Generate for all skills")
@click.option("--count", type=int, default=5, help="Cases to generate per skill")
@click.option(
    "--category",
    type=click.Choice(["positive", "confuser", "edge_case", "degraded"]),
    default="positive",
)
@click.option("--model", default=_DEFAULT_MODEL, help="Claude model to use")
@click.option("--apply", is_flag=True, default=False, help="Write files (dry-run by default)")
def main(
    golden_dir: Path,
    skill: str | None,
    all_skills: bool,
    count: int,
    category: str,
    model: str,
    apply: bool,
) -> None:
    """Generate synthetic golden set cases using Claude."""
    if not skill and not all_skills:
        click.echo("ERROR: Specify --skill or --all", err=True)
        sys.exit(1)

    skills_to_process: list[str] = SKILLS if all_skills else [skill]  # type: ignore[list-item]
    total_generated = 0

    for s in skills_to_process:
        click.echo(f"\n{'='*60}")
        click.echo(f"Skill: {s} | Category: {category} | Count: {count}")
        click.echo(f"{'='*60}")

        seed_cases = _load_seed_cases(golden_dir, s)
        if not seed_cases:
            click.echo(f"  SKIP: No seed cases for {s}")
            continue

        metadata = _load_metadata(golden_dir, s)
        cases = _generate_cases(seed_cases, metadata, s, count, category, model)
        cases = _assign_case_numbers(cases, golden_dir, s, category)

        click.echo(f"  Generated {len(cases)} cases:")
        for c in cases:
            tags = ", ".join(c.get("tags", [])[:4])
            click.echo(f"    case_{c['case_number']:03d} — [{tags}]")

        if apply:
            paths = _write_cases(cases, golden_dir, s)
            click.echo(f"  Written {len(paths)} files to {golden_dir / s}/")
        else:
            click.echo(f"  DRY-RUN: Would write {len(cases)} files. Use --apply to save.")

            preview = json.dumps(cases[0], indent=2, ensure_ascii=False)
            if len(preview) > 800:
                preview = preview[:800] + "\n  ... (truncated)"
            click.echo(f"\n  Preview (first case):\n{preview}")

        total_generated += len(cases)

    click.echo(f"\nTotal: {total_generated} cases generated across {len(skills_to_process)} skills.")
    if not apply:
        click.echo("DRY-RUN mode. Use --apply to write files.")
    else:
        click.echo("CLO review required before committing.")


if __name__ == "__main__":
    main()
