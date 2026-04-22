"""Scope-aware grader — correlates function decorators with function bodies via AST."""

from __future__ import annotations

import ast
import re
from typing import Any

from gbr_eval.graders._shared import _is_catastrophic_pattern, _make_result
from gbr_eval.graders.base import register_grader

_MAX_PATTERN_LEN = 1_000
_MAX_INPUT_LEN = 100_000


def _validate_pattern(pattern: str, spec: Any) -> str | None:
    if len(pattern) > _MAX_PATTERN_LEN:
        return f"Pattern too long ({len(pattern)} > {_MAX_PATTERN_LEN})"
    if _is_catastrophic_pattern(pattern):
        return f"Potentially catastrophic regex pattern rejected: {pattern}"
    return None


def _get_body_text(content_lines: list[str], node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    start = node.body[0].lineno - 1
    end = node.end_lineno
    return "\n".join(content_lines[start:end])


def _get_signature_text(content_lines: list[str], node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    start = node.lineno - 1
    end = node.body[0].lineno - 1
    return "\n".join(content_lines[start:end])


@register_grader("scope_check")
class ScopeCheck:
    """AST-based grader that correlates function decorators with function bodies.

    Config:
        decorator_pattern: regex matching decorator text that puts a function in scope
        required_call: optional regex that MUST appear somewhere in the function body
        required_param: optional regex that MUST match an argument name or appear in signature
        forbidden_call: optional regex that MUST NOT appear in the function body
        skip_if_no_matches: if True and no functions match the decorator, pass with 1.0 (default True)
        file_key: key in output containing source code (default "content")
    """

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: Any) -> Any:
        decorator_pattern = spec.config.get("decorator_pattern", "")
        if not decorator_pattern:
            return _make_result(spec, False, 0.0, "No decorator_pattern specified in config")

        for label, pat in [
            ("decorator_pattern", decorator_pattern),
            ("required_call", spec.config.get("required_call", "")),
            ("required_param", spec.config.get("required_param", "")),
            ("forbidden_call", spec.config.get("forbidden_call", "")),
        ]:
            if not pat:
                continue
            err = _validate_pattern(pat, spec)
            if err:
                return _make_result(spec, False, 0.0, f"{label}: {err}")

        file_key = spec.config.get("file_key", "content")
        skip_if_no_matches = spec.config.get("skip_if_no_matches", True)

        content = output.get(file_key, "")
        if not isinstance(content, str):
            content = str(content)
        content = content[:_MAX_INPUT_LEN]

        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            return _make_result(spec, False, 0.0, f"SyntaxError: {exc}")

        content_lines = content.splitlines()

        required_call = spec.config.get("required_call", "")
        required_param = spec.config.get("required_param", "")
        forbidden_call = spec.config.get("forbidden_call", "")

        in_scope: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                dec_text = "@" + (ast.get_source_segment(content, dec) or "")
                try:
                    if re.search(decorator_pattern, dec_text):
                        in_scope.append(node)
                        break
                except re.error:
                    return _make_result(spec, False, 0.0, f"Invalid decorator_pattern regex: {decorator_pattern}")

        if not in_scope:
            if skip_if_no_matches:
                return _make_result(spec, True, 1.0, "No functions matched decorator — skip_if_no_matches=True")
            return _make_result(spec, False, 0.0, "No functions matched decorator_pattern")

        violations: list[str] = []
        for node in in_scope:
            fname = node.name
            lineno = node.lineno
            body_text = _get_body_text(content_lines, node)
            sig_text = _get_signature_text(content_lines, node)

            if required_call:
                try:
                    if not re.search(required_call, body_text):
                        violations.append(f"{fname}:{lineno}: missing required_call ({required_call})")
                except re.error as exc:
                    violations.append(f"{fname}:{lineno}: invalid required_call regex ({exc})")

            if required_param:
                param_names = [arg.arg for arg in node.args.args + node.args.kwonlyargs]
                if node.args.vararg:
                    param_names.append(node.args.vararg.arg)
                if node.args.kwarg:
                    param_names.append(node.args.kwarg.arg)
                try:
                    param_match = any(re.search(required_param, name) for name in param_names)
                    sig_match = re.search(required_param, sig_text) is not None
                    if not (param_match or sig_match):
                        violations.append(f"{fname}:{lineno}: missing required_param ({required_param})")
                except re.error as exc:
                    violations.append(f"{fname}:{lineno}: invalid required_param regex ({exc})")

            if forbidden_call:
                try:
                    if re.search(forbidden_call, body_text):
                        violations.append(f"{fname}:{lineno}: forbidden_call found ({forbidden_call})")
                except re.error as exc:
                    violations.append(f"{fname}:{lineno}: invalid forbidden_call regex ({exc})")

        checked = len(in_scope)
        if not violations:
            return _make_result(spec, True, 1.0, f"All {checked} in-scope functions pass")

        unique_funcs_with_violations = len({v.split(":")[0] for v in violations})
        score = max(0.0, (checked - unique_funcs_with_violations) / checked)
        return _make_result(spec, False, score, "; ".join(violations))
