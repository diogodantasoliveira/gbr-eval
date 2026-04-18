"""LLM-as-judge grader — NOT a pure function (calls external API, non-deterministic).

This grader uses Claude Sonnet to evaluate outputs against a rubric.
It is the ONLY grader that is not deterministic. Documented exception.
"""

from __future__ import annotations

import json
import os
from typing import Any

from gbr_eval.graders.base import register_grader
from gbr_eval.harness.models import GraderResult, GraderSpec

_DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
_SYSTEM_PROMPT = """You are an expert evaluator for GarantiaBR's document audit system.
You evaluate AI-generated outputs against a quality rubric.

Score on a scale of 1-5:
1 = Completely wrong or missing
2 = Major errors that would cause incorrect decisions
3 = Partially correct but with significant gaps
4 = Mostly correct with minor issues
5 = Fully correct and complete

Return ONLY a JSON object:
{"score": <1-5>, "reasoning": "<brief explanation>", "escape_hatch_unknown": <true if you cannot evaluate>}
"""


@register_grader("llm_judge")
class LLMJudge:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return GraderResult(
                grader_type="llm_judge",
                field=spec.field,
                passed=False,
                score=0.0,
                weight=spec.weight,
                required=spec.required,
                details="ANTHROPIC_API_KEY not set — LLM judge cannot run",
            )

        rubric = spec.config.get("rubric", "Evaluate the output for correctness and completeness.")
        model = spec.config.get("model", _DEFAULT_MODEL)
        min_score = float(spec.config.get("min_score", 4.0))

        prompt = (
            f"## Rubric\n{rubric}\n\n"
            f"## Expected Output\n```json\n{json.dumps(expected, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## Actual Output\n```json\n{json.dumps(output, ensure_ascii=False, indent=2)}\n```\n\n"
            f"Evaluate the actual output against the expected output using the rubric above."
        )

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            result = json.loads(response_text)

            if result.get("escape_hatch_unknown"):
                return GraderResult(
                    grader_type="llm_judge",
                    field=spec.field,
                    passed=False,
                    score=0.0,
                    weight=spec.weight,
                    required=spec.required,
                    details=f"LLM judge uncertain: {result.get('reasoning', 'unknown')}",
                )

            raw_score = float(result["score"])
            normalized = (raw_score - 1.0) / 4.0
            passed = raw_score >= min_score

            return GraderResult(
                grader_type="llm_judge",
                field=spec.field,
                passed=passed,
                score=normalized,
                weight=spec.weight,
                required=spec.required,
                details=f"score={raw_score}/5 (min={min_score}): {result.get('reasoning', '')}",
            )

        except Exception as exc:
            return GraderResult(
                grader_type="llm_judge",
                field=spec.field,
                passed=False,
                score=0.0,
                weight=spec.weight,
                required=spec.required,
                error=f"LLM judge error: {exc}",
            )
