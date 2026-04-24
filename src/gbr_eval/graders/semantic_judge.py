"""Semantic interpretation grader — LLM-based evaluation of legal/juridical text.

Uses Claude to evaluate whether an extracted legal interpretation semantically matches
the expected content (e.g. "ônus na matrícula", "poderes no contrato social").
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import anthropic

from gbr_eval.graders._shared import _extract_json, get_anthropic_client, sanitize_pii_str
from gbr_eval.graders.base import register_grader
from gbr_eval.harness.models import GraderResult, GraderSpec, GraderStatus

_DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
_API_TIMEOUT = 30.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0
_PASS_THRESHOLD = 0.7

_SYSTEM_PROMPT_TEMPLATE = """\
Você é um avaliador jurídico especializado. Analise se a interpretação extraída \
corresponde semanticamente ao conteúdo esperado.

Domínio: {domain}
{rubric_section}
Responda APENAS com JSON: {{"score": 0.0-1.0, "rationale": "explicação breve"}}

score 1.0 = interpretação semanticamente idêntica
score 0.7-0.9 = interpretação correta com detalhes faltantes
score 0.3-0.6 = interpretação parcialmente correta
score 0.0-0.2 = interpretação incorreta ou ausente\
"""


def _call_with_retry(
    client: anthropic.Anthropic,
    *,
    model: str,
    max_tokens: int,
    timeout: float,
    system: str,
    messages: list[anthropic.types.MessageParam],
    max_retries: int = _MAX_RETRIES,
) -> anthropic.types.Message:
    """Call client.messages.create with exponential backoff on transient errors."""
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                timeout=timeout,
                system=system,
                messages=messages,
            )
        except (anthropic.RateLimitError, anthropic.InternalServerError):
            if attempt == max_retries:
                raise
            delay = _BASE_DELAY * (2**attempt)
            time.sleep(delay)
        except TimeoutError:
            if attempt == max_retries:
                raise
            delay = _BASE_DELAY * (2**attempt)
            time.sleep(delay)
    raise AssertionError("unreachable: loop always returns or raises")


@register_grader("semantic_interpretation", context_aware=False)
class SemanticJudge:
    """LLM-based grader for semantic interpretation of legal/juridical text.

    Evaluates whether the extracted interpretation matches the semantic intent
    of the expected content, not just exact text match.

    Config keys:
        model (str): Model override (default: claude-sonnet-4-5-20250929).
        domain (str): Legal domain context (default: "juridico").
        rubric (str, optional): Custom rubric text to include in the prompt.
    """

    def grade(
        self,
        output: dict[str, Any],
        expected: dict[str, Any],
        spec: GraderSpec,
    ) -> GraderResult:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return GraderResult(
                grader_type="semantic_interpretation",
                field=spec.field,
                passed=False,
                score=0.0,
                weight=spec.weight,
                required=spec.required,
                error="ANTHROPIC_API_KEY not set",
                status=GraderStatus.SKIPPED,
            )

        model = spec.config.get("model", _DEFAULT_MODEL)
        domain = spec.config.get("domain", "juridico")
        rubric = spec.config.get("rubric", "")

        rubric_section = f"Rubrica: {rubric}\n" if rubric else ""

        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            domain=domain,
            rubric_section=rubric_section,
        )

        field = spec.field
        output_value = output.get(field, "") if field else output
        expected_value = expected.get(field, "") if field else expected

        safe_output = sanitize_pii_str(str(output_value))
        safe_expected = sanitize_pii_str(str(expected_value))

        prompt = (
            f"Campo avaliado: {field}\n\n"
            f"Valor esperado:\n{safe_expected}\n\n"
            f"Valor extraído:\n{safe_output}\n\n"
            "Avalie se o valor extraído corresponde semanticamente ao esperado."
        )

        try:
            client = get_anthropic_client(api_key)
            api_messages: list[anthropic.types.MessageParam] = [
                {"role": "user", "content": prompt}
            ]
            response = _call_with_retry(
                client,
                model=model,
                max_tokens=256,
                timeout=_API_TIMEOUT,
                system=system_prompt,
                messages=api_messages,
            )

            from anthropic.types import TextBlock

            text_blocks = [b for b in response.content if isinstance(b, TextBlock)]
            if not text_blocks:
                raise ValueError("No text block in LLM response")
            response_text = _extract_json(text_blocks[0].text)
            result = json.loads(response_text)

            score = float(result["score"])
            score = max(0.0, min(1.0, score))
            passed = score >= _PASS_THRESHOLD
            rationale = result.get("rationale", "")

            return GraderResult(
                grader_type="semantic_interpretation",
                field=spec.field,
                passed=passed,
                score=score,
                weight=spec.weight,
                required=spec.required,
                details=f"score={score:.2f} (threshold={_PASS_THRESHOLD}): {rationale}",
            )

        except (anthropic.APIError, json.JSONDecodeError, ValueError, KeyError, TimeoutError) as exc:
            return GraderResult(
                grader_type="semantic_interpretation",
                field=spec.field,
                passed=False,
                score=0.0,
                weight=spec.weight,
                required=spec.required,
                error=f"semantic_judge error: {type(exc).__name__}: {sanitize_pii_str(str(exc))}",
                status=GraderStatus.ERROR,
            )
