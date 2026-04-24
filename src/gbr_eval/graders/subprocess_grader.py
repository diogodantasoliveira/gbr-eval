"""Subprocess grader — executes external tools and grades based on exit code and output.

Documented exception to grader purity (like LLM judges): runs a subprocess.
Use for build tools, test runners, linters, and type checkers.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess as sp
from typing import Any

from gbr_eval.graders._shared import _is_catastrophic_pattern, _make_result
from gbr_eval.graders.base import register_grader
from gbr_eval.harness.models import GraderResult, GraderSpec

_MAX_OUTPUT_CAPTURE = 50_000
_DEFAULT_TIMEOUT = 120
_MAX_TIMEOUT = 600

_BLOCKED_BASES = frozenset({
    "rm", "rmdir", "del", "format", "mkfs",
    "dd", "shred", "shutdown", "reboot", "halt", "poweroff",
})


def _expand_env(value: str) -> str:
    return os.path.expandvars(value)


def _resolve_command(raw: str | list[str]) -> list[str]:
    if isinstance(raw, list):
        return [_expand_env(str(s)) for s in raw]
    return [_expand_env(s) for s in shlex.split(str(raw))]


def _is_blocked(cmd: list[str]) -> str | None:
    if not cmd:
        return "empty command"
    base = os.path.basename(cmd[0]).lower()
    if base in _BLOCKED_BASES:
        return base
    return None


def _tail_lines(text: str, n: int) -> str:
    lines = text.strip().splitlines()
    if len(lines) <= n:
        return text.strip()
    return "\n".join(lines[-n:])


@register_grader("subprocess")
class SubprocessGrader:
    """Execute an external tool and grade based on exit code and output patterns.

    Config:
        command: str | list[str] — command to execute (supports $ENV_VAR expansion)
        cwd: str — working directory (supports $ENV_VAR, overrides output["cwd"])
        timeout_seconds: int — max execution time (default 120, max 600)
        expect_exit_code: int — expected exit code for pass (default 0)
        pass_pattern: str — regex that must match stdout for pass
        fail_pattern: str — regex in stdout+stderr that forces failure
        env: dict[str, str] — extra environment variables
        capture_lines: int — max tail lines in details (default 50)
    """

    def grade(
        self,
        output: dict[str, Any],
        expected: dict[str, Any],
        spec: GraderSpec,
    ) -> GraderResult:
        command_raw = spec.config.get("command")
        if not command_raw:
            return _make_result(spec, False, 0.0, "No command specified in config")

        try:
            cmd = _resolve_command(command_raw)
        except ValueError as e:
            return _make_result(spec, False, 0.0, f"Invalid command: {e}")

        blocked = _is_blocked(cmd)
        if blocked:
            return _make_result(spec, False, 0.0, f"Blocked command: {blocked}")

        cwd = spec.config.get("cwd") or output.get("cwd")
        if cwd:
            cwd = _expand_env(str(cwd))
        if cwd and not os.path.isdir(cwd):
            return _make_result(spec, False, 0.0, f"Working directory not found: {cwd}")

        timeout = min(
            int(spec.config.get("timeout_seconds", _DEFAULT_TIMEOUT)),
            _MAX_TIMEOUT,
        )
        expect_exit = int(spec.config.get("expect_exit_code", 0))
        pass_pattern: str | None = spec.config.get("pass_pattern")
        fail_pattern: str | None = spec.config.get("fail_pattern")
        capture_lines = int(spec.config.get("capture_lines", 50))
        extra_env: dict[str, str] = spec.config.get("env", {})

        if pass_pattern and _is_catastrophic_pattern(pass_pattern):
            return _make_result(spec, False, 0.0, f"Catastrophic regex in pass_pattern: {pass_pattern}")
        if fail_pattern and _is_catastrophic_pattern(fail_pattern):
            return _make_result(spec, False, 0.0, f"Catastrophic regex in fail_pattern: {fail_pattern}")

        env = {**os.environ, **{k: _expand_env(str(v)) for k, v in extra_env.items()}} if extra_env else None

        try:
            proc = sp.run(
                cmd,
                cwd=cwd or None,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
        except sp.TimeoutExpired:
            return _make_result(spec, False, 0.0, f"Command timed out after {timeout}s: {shlex.join(cmd)}")
        except FileNotFoundError:
            return _make_result(spec, False, 0.0, f"Command not found: {cmd[0]}")
        except OSError as e:
            return _make_result(spec, False, 0.0, f"OS error running command: {e}")

        stdout = (proc.stdout or "")[-_MAX_OUTPUT_CAPTURE:]
        stderr = (proc.stderr or "")[-_MAX_OUTPUT_CAPTURE:]

        exit_ok = proc.returncode == expect_exit

        pattern_ok = True
        pattern_details: list[str] = []

        combined = stdout + "\n" + stderr

        if pass_pattern:
            try:
                if not re.search(pass_pattern, combined, re.MULTILINE):
                    pattern_ok = False
                    pattern_details.append(f"pass_pattern not found in output: {pass_pattern}")
            except re.error as e:
                return _make_result(spec, False, 0.0, f"Invalid pass_pattern regex: {e}")

        if fail_pattern:
            try:
                if re.search(fail_pattern, combined, re.MULTILINE):
                    pattern_ok = False
                    pattern_details.append(f"fail_pattern matched in output: {fail_pattern}")
            except re.error as e:
                return _make_result(spec, False, 0.0, f"Invalid fail_pattern regex: {e}")

        passed = exit_ok and pattern_ok
        score = 1.0 if passed else 0.0

        detail_parts: list[str] = [f"exit_code={proc.returncode} (expected {expect_exit})"]
        detail_parts.extend(pattern_details)

        if stdout.strip():
            detail_parts.append("--- stdout ---")
            detail_parts.append(_tail_lines(stdout, capture_lines))

        if not passed and stderr.strip():
            detail_parts.append("--- stderr ---")
            detail_parts.append(_tail_lines(stderr, capture_lines))

        details = "\n".join(detail_parts)
        if len(details) > 10_000:
            details = details[:10_000] + "\n... (truncated)"

        return _make_result(spec, passed, score, details)
