"""Tests for the subprocess grader."""

import os
import sys

import pytest

import gbr_eval.graders.subprocess_grader  # noqa: F401
from gbr_eval.graders.base import grade
from gbr_eval.harness.models import GraderSpec


def _spec(**overrides: object) -> GraderSpec:
    defaults = {"type": "subprocess", "weight": 1.0, "required": False, "config": {}}
    defaults.update(overrides)
    return GraderSpec(**defaults)


# ---------------------------------------------------------------------------
# Basic exit code grading
# ---------------------------------------------------------------------------


class TestExitCode:
    def test_pass_on_zero_exit(self):
        spec = _spec(config={"command": ["true"]})
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert result.score == 1.0
        assert "exit_code=0" in result.details

    def test_fail_on_nonzero_exit(self):
        spec = _spec(config={"command": ["false"]})
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_custom_expected_exit_code(self):
        spec = _spec(config={"command": ["false"], "expect_exit_code": 1})
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_echo_captures_stdout(self):
        spec = _spec(config={"command": ["echo", "hello world"]})
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert "hello world" in result.details


# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------


class TestWorkingDirectory:
    def test_cwd_from_config(self, tmp_path):
        spec = _spec(config={"command": ["pwd"], "cwd": str(tmp_path)})
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert str(tmp_path) in result.details

    def test_cwd_from_output(self, tmp_path):
        spec = _spec(config={"command": ["pwd"]})
        result = grade("subprocess", {"cwd": str(tmp_path)}, {}, spec)
        assert result.passed
        assert str(tmp_path) in result.details

    def test_config_cwd_overrides_output(self, tmp_path):
        other = tmp_path / "sub"
        other.mkdir()
        spec = _spec(config={"command": ["pwd"], "cwd": str(other)})
        result = grade("subprocess", {"cwd": str(tmp_path)}, {}, spec)
        assert result.passed
        assert str(other) in result.details

    def test_nonexistent_cwd_fails(self):
        spec = _spec(config={"command": ["true"], "cwd": "/nonexistent/path/xyz"})
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "not found" in result.details


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------


class TestPatterns:
    def test_pass_pattern_found(self):
        spec = _spec(config={
            "command": ["echo", "all 42 tests passed"],
            "pass_pattern": r"\d+ tests passed",
        })
        result = grade("subprocess", {}, {}, spec)
        assert result.passed

    def test_pass_pattern_not_found(self):
        spec = _spec(config={
            "command": ["echo", "something else"],
            "pass_pattern": r"\d+ tests passed",
        })
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "pass_pattern not found in output" in result.details

    def test_fail_pattern_matched(self):
        spec = _spec(config={
            "command": ["echo", "FATAL ERROR occurred"],
            "fail_pattern": r"FATAL|CRITICAL",
        })
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "fail_pattern matched" in result.details

    def test_fail_pattern_not_matched_passes(self):
        spec = _spec(config={
            "command": ["echo", "all good"],
            "fail_pattern": r"FATAL|CRITICAL",
        })
        result = grade("subprocess", {}, {}, spec)
        assert result.passed

    def test_catastrophic_pass_pattern_rejected(self):
        spec = _spec(config={
            "command": ["true"],
            "pass_pattern": r"(a+)+b",
        })
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "Catastrophic" in result.details

    def test_catastrophic_fail_pattern_rejected(self):
        spec = _spec(config={
            "command": ["true"],
            "fail_pattern": r"(a+)+b",
        })
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "Catastrophic" in result.details


# ---------------------------------------------------------------------------
# Security — blocked commands
# ---------------------------------------------------------------------------


class TestSecurity:
    @pytest.mark.parametrize("cmd", [
        ["rm", "-rf", "/"],
        ["rmdir", "something"],
        ["dd", "if=/dev/zero"],
        ["shutdown", "-h", "now"],
        ["reboot"],
    ])
    def test_blocked_commands(self, cmd):
        spec = _spec(config={"command": cmd})
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "Blocked" in result.details

    def test_safe_commands_allowed(self):
        spec = _spec(config={"command": ["echo", "safe"]})
        result = grade("subprocess", {}, {}, spec)
        assert result.passed


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_missing_command_config(self):
        spec = _spec(config={})
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "No command" in result.details

    def test_command_not_found(self):
        spec = _spec(config={"command": ["nonexistent_binary_xyz_123"]})
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "not found" in result.details

    def test_timeout(self):
        spec = _spec(config={
            "command": [sys.executable, "-c", "import time; time.sleep(10)"],
            "timeout_seconds": 1,
        })
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "timed out" in result.details

    def test_timeout_capped_at_max(self):
        spec = _spec(config={
            "command": ["true"],
            "timeout_seconds": 99999,
        })
        result = grade("subprocess", {}, {}, spec)
        assert result.passed


# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------


class TestEnvironment:
    def test_extra_env(self):
        spec = _spec(config={
            "command": [sys.executable, "-c", "import os; print(os.environ['TEST_VAR_XYZ'])"],
            "env": {"TEST_VAR_XYZ": "hello_from_env"},
        })
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert "hello_from_env" in result.details

    def test_env_var_expansion_in_command(self):
        os.environ["_GBR_EVAL_TEST_CMD"] = "echo"
        try:
            spec = _spec(config={"command": "$_GBR_EVAL_TEST_CMD hello"})
            result = grade("subprocess", {}, {}, spec)
            assert result.passed
            assert "hello" in result.details
        finally:
            del os.environ["_GBR_EVAL_TEST_CMD"]


# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------


class TestCommandParsing:
    def test_string_command_split(self):
        spec = _spec(config={"command": "echo hello world"})
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert "hello world" in result.details

    def test_list_command(self):
        spec = _spec(config={"command": ["echo", "hello", "world"]})
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert "hello world" in result.details

    def test_empty_command_list_rejected(self):
        spec = _spec(config={"command": []})
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "No command" in result.details


# ---------------------------------------------------------------------------
# Output capture
# ---------------------------------------------------------------------------


class TestOutputCapture:
    def test_stderr_shown_on_failure(self):
        spec = _spec(config={
            "command": [sys.executable, "-c", "import sys; sys.stderr.write('error msg\\n'); sys.exit(1)"],
        })
        result = grade("subprocess", {}, {}, spec)
        assert not result.passed
        assert "error msg" in result.details

    def test_capture_lines_limits_output(self):
        script = "for i in range(200): print(f'line {i}')"
        spec = _spec(config={
            "command": [sys.executable, "-c", script],
            "capture_lines": 5,
        })
        result = grade("subprocess", {}, {}, spec)
        assert result.passed
        assert "line 199" in result.details
        assert "line 0" not in result.details


# ---------------------------------------------------------------------------
# Integration with code_loader
# ---------------------------------------------------------------------------


class TestCodeLoaderIntegration:
    def test_subprocess_task_via_run_task_against_code(self, tmp_path):
        from gbr_eval.harness.code_loader import run_task_against_code
        from gbr_eval.harness.models import (
            Category,
            Layer,
            ScoringMode,
            Task,
            TaskInput,
            Tier,
        )

        task = Task(
            task_id="test.subprocess.echo",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            tier=Tier.GATE,
            description="test subprocess",
            input=TaskInput(payload={"repo": "."}),
            expected={},
            graders=[GraderSpec(
                type="subprocess",
                weight=1.0,
                required=True,
                config={"command": ["echo", "integration test"]},
            )],
            scoring_mode=ScoringMode.BINARY,
            pass_threshold=1.0,
        )

        result = run_task_against_code(task, tmp_path)
        assert result.passed
        assert result.score == 1.0
        assert "integration test" in result.grader_results[0].details

    def test_subprocess_task_uses_repo_as_cwd(self, tmp_path):
        from gbr_eval.harness.code_loader import run_task_against_code
        from gbr_eval.harness.models import (
            Category,
            Layer,
            ScoringMode,
            Task,
            TaskInput,
            Tier,
        )

        repo_dir = tmp_path / "myrepo"
        repo_dir.mkdir()

        task = Task(
            task_id="test.subprocess.cwd",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            tier=Tier.GATE,
            input=TaskInput(payload={"repo": "myrepo"}),
            expected={},
            graders=[GraderSpec(
                type="subprocess",
                weight=1.0,
                config={"command": ["pwd"]},
            )],
            scoring_mode=ScoringMode.BINARY,
            pass_threshold=1.0,
        )

        result = run_task_against_code(task, tmp_path)
        assert result.passed
        assert "myrepo" in result.grader_results[0].details
