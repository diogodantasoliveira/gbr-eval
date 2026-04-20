#!/usr/bin/env python3
"""Compute SHA-256 hashes for golden set cases from PDF files.

Usage:
    python tools/compute_hashes.py --pdf-dir /path/to/pdfs --golden-dir golden/

The script expects PDF files named to match document_source in golden set cases.
For example, if a case has:
    "document_source": "internal:matricula:001"
The script looks for:
    /path/to/pdfs/matricula/001.pdf  (or matricula_001.pdf)

Dry-run by default. Use --apply to write changes.
"""

import hashlib
import json
import sys
from pathlib import Path

import click


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def find_pdf(pdf_dir: Path, document_source: str) -> Path | None:
    parts = document_source.replace("internal:", "").split(":")
    if len(parts) != 2:
        return None
    doc_type, seq = parts

    candidates = [
        pdf_dir / doc_type / f"{seq}.pdf",
        pdf_dir / f"{doc_type}_{seq}.pdf",
        pdf_dir / doc_type / f"case_{seq}.pdf",
        pdf_dir / doc_type / f"doc_{seq}.pdf",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


@click.command()
@click.option("--pdf-dir", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--golden-dir", type=click.Path(exists=True, path_type=Path), default=Path("golden"))
@click.option("--apply", is_flag=True, default=False, help="Write changes to case files")
def main(pdf_dir: Path, golden_dir: Path, apply: bool) -> None:
    pending = 0
    updated = 0
    missing = 0

    for case_file in sorted(golden_dir.rglob("case_[0-9]*.json")):
        with open(case_file) as f:
            case = json.load(f)

        current_hash = case.get("document_hash", "")
        if not current_hash.startswith("sha256:PENDING"):
            continue

        pending += 1
        source = case.get("document_source", "")
        pdf_path = find_pdf(pdf_dir, source)

        if not pdf_path:
            click.echo(f"  MISS: {case_file.name} — no PDF for {source}")
            missing += 1
            continue

        new_hash = sha256_file(pdf_path)
        click.echo(f"  HASH: {case_file.name} — {new_hash[:30]}...")

        if apply:
            case["document_hash"] = new_hash
            with open(case_file, "w") as f:
                json.dump(case, f, indent=2, ensure_ascii=False)
                f.write("\n")
            updated += 1

    click.echo(f"\nPending: {pending}, Hashed: {updated}, Missing PDFs: {missing}")
    if not apply and pending > 0:
        click.echo("Dry-run mode. Use --apply to write changes.")

    if missing > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
