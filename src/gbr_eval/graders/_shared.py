"""Shared utilities for grader implementations."""

from __future__ import annotations

import json
import re

import anthropic

from gbr_eval.harness.models import GraderResult, GraderSpec

_CATASTROPHIC_RE = re.compile(r"(\([^)]*[+*][^)]*\))[+*]")

# ---------------------------------------------------------------------------
# Shared Anthropic client — single instance per process, closed explicitly.
# Prevents CLOSE_WAIT accumulation from creating a new client per grader call.
# ---------------------------------------------------------------------------
_shared_client: anthropic.Anthropic | None = None


def get_anthropic_client(api_key: str) -> anthropic.Anthropic:
    """Return a shared Anthropic client, creating one if needed."""
    global _shared_client  # noqa: PLW0603
    if _shared_client is None:
        _shared_client = anthropic.Anthropic(api_key=api_key)
    return _shared_client


def close_anthropic_client() -> None:
    """Close the shared Anthropic client and release connections."""
    global _shared_client  # noqa: PLW0603
    if _shared_client is not None:
        _shared_client.close()
        _shared_client = None


def _is_catastrophic_pattern(pattern: str) -> bool:
    """Detect obvious catastrophic backtracking patterns like (a+)+."""
    return bool(_CATASTROPHIC_RE.search(pattern))


def _make_result(spec: GraderSpec, passed: bool, score: float, details: str) -> GraderResult:
    return GraderResult(
        grader_type=spec.type,
        field=spec.field,
        passed=passed,
        score=score,
        weight=spec.weight,
        required=spec.required,
        details=details,
    )


def _strip_markdown_fence(text: str) -> str:
    """Remove markdown code fences wrapping a JSON response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)
    return text


def _find_json_object(text: str) -> str:
    """Find the outermost ``{...}`` in *text* using a string-aware brace matcher.

    Tracks whether we are inside a JSON string (between unescaped ``"``) so
    braces within string values do not confuse the depth counter.
    """
    start = text.find("{")
    if start == -1:
        return text

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return text[start:]


_UNQUOTED_KEY_RE = re.compile(
    r'(?<=[\{,])\s*([a-zA-Z_]\w*)\s*:(?=\s*[\["\d{tfn])'
)
_SINGLE_QUOTE_RE = re.compile(r"(?<![\\])'")
_TRAILING_COMMA_RE = re.compile(r",\s*([\]}])")


def _repair_json(text: str) -> str:
    """Best-effort repair of common LLM JSON malformations.

    Handles: unquoted keys, single-quoted strings, trailing commas.
    Returns the repaired string (caller should still try json.loads).
    """
    # 1. Replace single quotes with double quotes (simple heuristic).
    if "'" in text and '"' not in text:
        text = _SINGLE_QUOTE_RE.sub('"', text)

    # 2. Quote unquoted keys: {score: 5} → {"score": 5}
    text = _UNQUOTED_KEY_RE.sub(r' "\1":', text)

    # 3. Remove trailing commas: [1, 2,] → [1, 2]
    text = _TRAILING_COMMA_RE.sub(r"\1", text)

    return text


def _extract_json(text: str) -> str:
    """Extract JSON object from LLM response text, handling mixed prose+JSON.

    Strategies attempted in order:
    1. Direct parse after stripping markdown fences.
    2. String-aware brace matching to locate the outermost object.
    3. JSON repair (unquoted keys, single quotes, trailing commas).
    """
    cleaned = _strip_markdown_fence(text)
    try:
        json.loads(cleaned)
        return cleaned
    except (json.JSONDecodeError, ValueError):
        pass

    candidate = _find_json_object(cleaned)
    try:
        json.loads(candidate)
        return candidate
    except (json.JSONDecodeError, ValueError):
        pass

    repaired = _repair_json(candidate)
    try:
        json.loads(repaired)
        return repaired
    except (json.JSONDecodeError, ValueError):
        pass

    return candidate
