"""File aggregator for holistic evaluation mode.

Combines multiple source files into a single prompt for LLM graders,
enabling holistic feature assessment across an entire codebase instead
of per-file evaluation.
"""

from __future__ import annotations

_LARGE_FILE_THRESHOLD = 500  # lines
_HEAD_LINES = 200
_TAIL_LINES = 100

# Priority tiers for file relevance (lower number = higher priority).
_PRIORITY_PATTERNS: list[tuple[int, list[str]]] = [
    (0, ["page.tsx", "page.ts", "page.jsx", "page.js"]),
    (1, ["/components/", "/ui/"]),
    (2, ["/api/", "/routes/", "route.ts", "route.tsx"]),
    (3, ["/lib/", "/utils/", "/helpers/", "/hooks/"]),
]
_DEFAULT_PRIORITY = 4


def _file_priority(rel_path: str) -> int:
    """Return priority tier for a file path (lower = more important)."""
    path_lower = rel_path.lower()
    for priority, patterns in _PRIORITY_PATTERNS:
        for pattern in patterns:
            if pattern in path_lower:
                return priority
    return _DEFAULT_PRIORITY


def _truncate_large_file(content: str) -> str:
    """Truncate files over the threshold, keeping head and tail."""
    lines = content.splitlines(keepends=True)
    if len(lines) <= _LARGE_FILE_THRESHOLD:
        return content

    head = lines[:_HEAD_LINES]
    tail = lines[-_TAIL_LINES:]
    omitted = len(lines) - _HEAD_LINES - _TAIL_LINES
    return (
        "".join(head)
        + f"\n[... truncated {omitted} lines ...]\n\n"
        + "".join(tail)
    )


def _guess_language(rel_path: str) -> str:
    """Guess language hint from file extension for markdown fences."""
    ext_map: dict[str, str] = {
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "jsx",
        ".py": "python",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sql": "sql",
        ".go": "go",
        ".rs": "rust",
    }
    for ext, lang in ext_map.items():
        if rel_path.endswith(ext):
            return lang
    return ""


def aggregate_files_for_prompt(
    files: list[tuple[str, str]],
    max_chars: int = 100_000,
) -> str:
    """Build a single prompt from multiple source files.

    Strategy:
    - Start with a codebase overview: file count, total lines.
    - Include full content for files under 500 lines.
    - For files over 500 lines, include first 200 + last 100 lines.
    - If total exceeds *max_chars*, prioritize by relevance:
      page.tsx first, then components, then API routes, then lib/utils.
    - Always include a file listing at the top even if content is truncated.

    Args:
        files: List of ``(relative_path, content)`` tuples.
        max_chars: Maximum total characters in the aggregated output.

    Returns:
        A formatted string ready to be used as LLM prompt content.
    """
    if not files:
        return "## Codebase Overview\n0 files, 0 total lines\n"

    # Sort by priority, then alphabetically within same priority.
    sorted_files = sorted(files, key=lambda f: (_file_priority(f[0]), f[0]))

    # Compute overview stats.
    total_lines = sum(content.count("\n") + 1 for _, content in sorted_files)

    # Build the file listing section.
    listing_lines: list[str] = []
    for rel_path, content in sorted_files:
        line_count = content.count("\n") + 1
        listing_lines.append(f"- {rel_path} ({line_count} lines)")
    listing_section = "\n".join(listing_lines)

    header = (
        f"## Codebase Overview\n"
        f"{len(sorted_files)} files, {total_lines} total lines\n\n"
        f"### Files\n{listing_section}\n"
    )

    # Build content sections, respecting max_chars.
    content_sections: list[str] = []
    chars_used = len(header)

    for rel_path, content in sorted_files:
        truncated_content = _truncate_large_file(content)
        lang = _guess_language(rel_path)

        section = f"\n## {rel_path}\n```{lang}\n{truncated_content}\n```\n"

        if chars_used + len(section) > max_chars:
            # Try a minimal stub showing that the file exists but was omitted.
            line_count = content.count("\n") + 1
            stub = f"\n## {rel_path}\n[content omitted — {line_count} lines, budget exceeded]\n"
            if chars_used + len(stub) <= max_chars:
                content_sections.append(stub)
                chars_used += len(stub)
            # Otherwise skip entirely — the file listing still shows it.
            continue

        content_sections.append(section)
        chars_used += len(section)

    return header + "".join(content_sections)
