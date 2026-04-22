"""Git-diff mode — grade only files changed in the current PR/branch.

Compares HEAD against a base branch (default: ``main``) and returns
only Added, Copied, Modified, or Renamed files that still exist on disk.
"""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_SAFE_BRANCH = re.compile(r"^[\w./-]+$")


def get_changed_files(repo_dir: Path, base_branch: str = "main") -> set[str]:
    """Return set of file paths changed between *base_branch* and HEAD.

    Only includes Added, Copied, Modified, and Renamed files (``--diff-filter=ACMR``).
    Deleted files are excluded since there's nothing to grade.

    Raises ``ValueError`` if *base_branch* contains unsafe characters.
    Raises ``RuntimeError`` if the directory is not a git repo.
    """
    if not _SAFE_BRANCH.match(base_branch):
        raise ValueError(f"Invalid branch name: {base_branch!r}")

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_dir),
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git not found on PATH") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "not a git repository" in stderr.lower():
            raise RuntimeError(f"Not a git repository: {repo_dir}")
        raise RuntimeError(f"git diff failed (exit {result.returncode}): {stderr}")

    files: set[str] = set()
    for line in result.stdout.strip().splitlines():
        path = line.strip()
        if path and (repo_dir / path).is_file():
            files.add(path)

    return files


def filter_changed_files(
    all_files: list[tuple[str, str]],
    changed: set[str],
) -> list[tuple[str, str]]:
    """Filter loaded files to only those in the changed set.

    Args:
        all_files: List of ``(relative_path, content)`` from ``load_code_files``.
        changed: Set of changed file paths from ``get_changed_files``.
    """
    return [(path, content) for path, content in all_files if path in changed]
