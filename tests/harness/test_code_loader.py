"""Tests for the Code Loader — engineering eval against actual code files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from gbr_eval.harness.code_loader import (
    FileResult,
    evaluate_file,
    load_code_files,
    run_engineering_suite,
    run_task_against_code,
)
from gbr_eval.harness.models import (
    Category,
    GraderSpec,
    Layer,
    Task,
    TaskInput,
    Tier,
)


@pytest.fixture()
def code_dir(tmp_path: Path) -> Path:
    """Create a fake repo structure for testing."""
    repo = tmp_path / "atom-back-end"
    repo.mkdir()

    # File that has tenant_id filtering
    (repo / "service.py").write_text(
        "def get_items(db, tenant_id):\n"
        "    return db.query(Item).filter(Item.tenant_id == tenant_id).all()\n"
    )

    # File that does NOT have tenant_id filtering
    (repo / "health.py").write_text(
        "def healthcheck():\n"
        "    return {'status': 'ok'}\n"
    )

    # Nested file
    sub = repo / "api"
    sub.mkdir()
    (sub / "routes.py").write_text(
        "def list_orders(db, tenant_id):\n"
        "    return db.query(Order).filter(Order.tenant_id == tenant_id).all()\n"
    )

    return tmp_path


@pytest.fixture()
def tenant_task() -> Task:
    """Task that checks for tenant_id in Python files."""
    return Task(
        task_id="eng.atom.tenant_id_filter",
        category=Category.TENANT_ISOLATION,
        component="atom-back-end",
        layer=Layer.ENGINEERING,
        tier=Tier.GATE,
        description="All queries must filter by tenant_id",
        input=TaskInput(payload={"repo": "atom-back-end", "scan_target": "**/*.py"}),
        graders=[
            GraderSpec(
                type="pattern_required",
                config={"pattern": "tenant_id", "file_key": "content"},
            )
        ],
        pass_threshold=0.95,
    )


class TestLoadCodeFiles:
    def test_loads_matching_files(self, code_dir: Path) -> None:
        files = load_code_files(code_dir, "atom-back-end", "**/*.py")
        assert len(files) == 3
        paths = [p for p, _ in files]
        assert "service.py" in paths
        assert "health.py" in paths
        assert "api/routes.py" in paths

    def test_returns_content(self, code_dir: Path) -> None:
        files = load_code_files(code_dir, "atom-back-end", "*.py")
        content_map = dict(files)
        assert "tenant_id" in content_map["service.py"]
        assert "healthcheck" in content_map["health.py"]

    def test_nonexistent_repo_returns_empty(self, code_dir: Path) -> None:
        files = load_code_files(code_dir, "nonexistent-repo", "**/*.py")
        assert files == []

    def test_no_matching_files_returns_empty(self, code_dir: Path) -> None:
        files = load_code_files(code_dir, "atom-back-end", "**/*.rs")
        assert files == []

    def test_glob_filters_correctly(self, code_dir: Path) -> None:
        files = load_code_files(code_dir, "atom-back-end", "*.py")
        assert len(files) == 2  # only top-level .py files

    def test_skips_binary_files(self, tmp_path: Path) -> None:
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / "binary.py").write_bytes(b"\x00\x01\x02\xff\xfe")
        (repo / "valid.py").write_text("x = 1\n")
        files = load_code_files(tmp_path, "myrepo", "**/*.py")
        assert len(files) == 1
        assert files[0][0] == "valid.py"

    def test_skips_directories_matching_glob(self, tmp_path: Path) -> None:
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / "real.py").write_text("code\n")
        (repo / "fake.py").mkdir()  # directory named like a file
        files = load_code_files(tmp_path, "myrepo", "*.py")
        assert len(files) == 1


class TestEvaluateFile:
    def test_conforming_file(self, tenant_task: Task) -> None:
        content = "query.filter(Item.tenant_id == tid)"
        result = evaluate_file(tenant_task, "service.py", content)
        assert result.conforming is True
        assert result.file_path == "service.py"
        assert len(result.grader_results) == 1
        assert result.grader_results[0].passed is True
        assert result.grader_results[0].file_path == "service.py"

    def test_non_conforming_file(self, tenant_task: Task) -> None:
        content = "def healthcheck(): return 'ok'"
        result = evaluate_file(tenant_task, "health.py", content)
        assert result.conforming is False
        assert result.file_path == "health.py"
        assert result.grader_results[0].passed is False

    def test_multiple_graders(self) -> None:
        task = Task(
            task_id="eng.test.multi",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "test", "scan_target": "**/*.py"}),
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "import logging"}),
                GraderSpec(type="pattern_forbidden", config={"pattern": "print\\("}),
            ],
            pass_threshold=0.95,
        )
        content = "import logging\nlogger = logging.getLogger(__name__)\n"
        result = evaluate_file(task, "mod.py", content)
        assert result.conforming is True
        assert len(result.grader_results) == 2

    def test_partial_conforming_returns_false(self) -> None:
        task = Task(
            task_id="eng.test.partial",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "test", "scan_target": "**/*.py"}),
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "import logging"}),
                GraderSpec(type="pattern_forbidden", config={"pattern": "print\\("}),
            ],
            pass_threshold=0.95,
        )
        content = "import logging\nprint('debug')\n"
        result = evaluate_file(task, "mod.py", content)
        assert result.conforming is False


class TestRunTaskAgainstCode:
    def test_full_pass(self, code_dir: Path) -> None:
        task = Task(
            task_id="eng.test.all_have_def",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "atom-back-end", "scan_target": "**/*.py"}),
            graders=[GraderSpec(type="pattern_required", config={"pattern": "def "})],
            pass_threshold=0.95,
        )
        result = run_task_against_code(task, code_dir)
        assert result.passed is True
        assert result.score == 1.0
        assert result.error is None

    def test_partial_conformance(self, code_dir: Path, tenant_task: Task) -> None:
        result = run_task_against_code(tenant_task, code_dir)
        # 2 out of 3 files have tenant_id → score = 2/3 ≈ 0.667
        assert result.score == pytest.approx(2.0 / 3.0, abs=0.01)
        assert result.passed is False  # below 0.95 threshold

    def test_missing_repo_field(self, code_dir: Path) -> None:
        task = Task(
            task_id="eng.test.no_repo",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={}),
            graders=[GraderSpec(type="pattern_required", config={"pattern": "x"})],
            pass_threshold=0.95,
        )
        result = run_task_against_code(task, code_dir)
        assert result.passed is False
        assert result.error == "Task missing input.payload.repo"

    def test_no_files_found(self, code_dir: Path) -> None:
        task = Task(
            task_id="eng.test.no_files",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "atom-back-end", "scan_target": "**/*.rs"}),
            graders=[GraderSpec(type="pattern_required", config={"pattern": "fn "})],
            pass_threshold=0.95,
        )
        result = run_task_against_code(task, code_dir)
        assert result.passed is False
        assert "No files found" in (result.error or "")

    def test_nonexistent_repo(self, code_dir: Path) -> None:
        task = Task(
            task_id="eng.test.bad_repo",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "does-not-exist", "scan_target": "**/*.py"}),
            graders=[GraderSpec(type="pattern_required", config={"pattern": "x"})],
            pass_threshold=0.95,
        )
        result = run_task_against_code(task, code_dir)
        assert result.passed is False
        assert "No files found" in (result.error or "")

    def test_grader_results_have_file_path(self, code_dir: Path, tenant_task: Task) -> None:
        result = run_task_against_code(tenant_task, code_dir)
        for gr in result.grader_results:
            assert gr.file_path is not None

    def test_duration_tracked(self, code_dir: Path, tenant_task: Task) -> None:
        result = run_task_against_code(tenant_task, code_dir)
        assert result.duration_ms > 0


class TestRunEngineeringSuite:
    def test_runs_engineering_tasks_only(self, code_dir: Path, tmp_path: Path) -> None:
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        eng_dir = tasks_dir / "engineering" / "atom-back-end"
        eng_dir.mkdir(parents=True)

        import yaml

        task_yaml = {
            "task_id": "eng.atom.has_def",
            "category": "code_quality",
            "component": "atom-back-end",
            "layer": "engineering",
            "tier": "gate",
            "input": {"payload": {"repo": "atom-back-end", "scan_target": "**/*.py"}},
            "graders": [{"type": "pattern_required", "config": {"pattern": "def "}}],
            "pass_threshold": 0.95,
        }
        (eng_dir / "has_def.yaml").write_text(yaml.dump(task_yaml))

        run = run_engineering_suite(tasks_dir, code_dir)
        assert run.tasks_total == 1
        assert run.tasks_passed == 1
        assert run.overall_score == 1.0
        assert run.layer == Layer.ENGINEERING
        assert run.metadata["code_dir"] == code_dir.name

    def test_filters_by_tier(self, code_dir: Path, tmp_path: Path) -> None:
        tasks_dir = tmp_path / "tasks"
        eng_dir = tasks_dir / "engineering" / "test"
        eng_dir.mkdir(parents=True)

        import yaml

        gate_task = {
            "task_id": "eng.test.gate",
            "category": "code_quality",
            "component": "test",
            "layer": "engineering",
            "tier": "gate",
            "input": {"payload": {"repo": "atom-back-end", "scan_target": "**/*.py"}},
            "graders": [{"type": "pattern_required", "config": {"pattern": "def "}}],
            "pass_threshold": 0.95,
        }
        regression_task = {
            "task_id": "eng.test.regression",
            "category": "code_quality",
            "component": "test",
            "layer": "engineering",
            "tier": "regression",
            "input": {"payload": {"repo": "atom-back-end", "scan_target": "**/*.py"}},
            "graders": [{"type": "pattern_required", "config": {"pattern": "def "}}],
            "pass_threshold": 0.95,
        }
        (eng_dir / "gate_task.yaml").write_text(yaml.dump(gate_task))
        (eng_dir / "regression_task.yaml").write_text(yaml.dump(regression_task))

        run = run_engineering_suite(tasks_dir, code_dir, tier=Tier.GATE)
        assert run.tasks_total == 1
        assert run.task_results[0].task_id == "eng.test.gate"

    def test_empty_suite(self, code_dir: Path, tmp_path: Path) -> None:
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        run = run_engineering_suite(tasks_dir, code_dir)
        assert run.tasks_total == 0
        assert run.overall_score == 0.0

    def test_gate_result_populated(self, code_dir: Path, tmp_path: Path) -> None:
        tasks_dir = tmp_path / "tasks"
        eng_dir = tasks_dir / "engineering" / "test"
        eng_dir.mkdir(parents=True)

        import yaml

        task_yaml = {
            "task_id": "eng.test.gate_check",
            "category": "code_quality",
            "component": "test",
            "layer": "engineering",
            "tier": "gate",
            "input": {"payload": {"repo": "atom-back-end", "scan_target": "**/*.py"}},
            "graders": [{"type": "pattern_required", "config": {"pattern": "def "}}],
            "pass_threshold": 0.95,
        }
        (eng_dir / "task.yaml").write_text(yaml.dump(task_yaml))

        run = run_engineering_suite(tasks_dir, code_dir)
        assert run.gate_result is not None


class TestFileResult:
    def test_dataclass_creation(self) -> None:
        from gbr_eval.harness.models import GraderResult

        gr = GraderResult(grader_type="pattern_required", passed=True, score=1.0, file_path="test.py")
        fr = FileResult(file_path="test.py", conforming=True, grader_results=[gr])
        assert fr.file_path == "test.py"
        assert fr.conforming is True
        assert len(fr.grader_results) == 1

    def test_default_empty_grader_results(self) -> None:
        fr = FileResult(file_path="x.py", conforming=True)
        assert fr.grader_results == []


class TestSecurityPathTraversal:
    def test_repo_with_dotdot_returns_empty(self, tmp_path: Path) -> None:
        repo = tmp_path / "safe-repo"
        repo.mkdir()
        (repo / "file.py").write_text("x = 1\n")
        files = load_code_files(tmp_path, "../../etc", "passwd")
        assert files == []

    def test_repo_traversal_blocked(self, tmp_path: Path) -> None:
        secret = tmp_path / "secret"
        secret.mkdir()
        (secret / "creds.py").write_text("API_KEY='leaked'\n")
        code_dir = tmp_path / "repos"
        code_dir.mkdir()
        files = load_code_files(code_dir, "../secret", "**/*.py")
        assert files == []

    def test_scan_target_with_dotdot_returns_empty(self, tmp_path: Path) -> None:
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / "ok.py").write_text("x = 1\n")
        files = load_code_files(tmp_path, "myrepo", "../../../etc/passwd")
        assert files == []

    def test_symlink_escape_blocked(self, tmp_path: Path) -> None:
        secret_dir = tmp_path / "secrets"
        secret_dir.mkdir()
        (secret_dir / "key.py").write_text("SECRET='value'\n")

        code_dir = tmp_path / "repos"
        repo = code_dir / "myrepo"
        repo.mkdir(parents=True)
        (repo / "legit.py").write_text("x = 1\n")
        (repo / "evil.py").symlink_to(secret_dir / "key.py")

        files = load_code_files(code_dir, "myrepo", "**/*.py")
        paths = [p for p, _ in files]
        assert "legit.py" in paths
        assert "evil.py" not in paths

    def test_symlinked_directory_escape_blocked(self, tmp_path: Path) -> None:
        secret_dir = tmp_path / "secrets"
        secret_dir.mkdir()
        (secret_dir / "data.py").write_text("sensitive\n")

        code_dir = tmp_path / "repos"
        repo = code_dir / "myrepo"
        repo.mkdir(parents=True)
        (repo / "linked_dir").symlink_to(secret_dir)

        files = load_code_files(code_dir, "myrepo", "**/*.py")
        paths = [p for p, _ in files]
        assert all("linked_dir" not in p for p in paths)


class TestResourceLimits:
    def test_large_file_skipped(self, tmp_path: Path) -> None:
        from gbr_eval.harness.code_loader import _MAX_FILE_SIZE

        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / "small.py").write_text("x = 1\n")
        (repo / "huge.py").write_text("x" * (_MAX_FILE_SIZE + 1))

        files = load_code_files(tmp_path, "myrepo", "**/*.py")
        assert len(files) == 1
        assert files[0][0] == "small.py"

    def test_file_count_limit(self, tmp_path: Path) -> None:
        repo = tmp_path / "myrepo"
        repo.mkdir()
        # Create more files than limit (use a small override for testing)
        for i in range(20):
            (repo / f"file_{i:03d}.py").write_text(f"x = {i}\n")

        # Patch the limit for test speed
        import gbr_eval.harness.code_loader as cl

        original = cl._MAX_FILES
        cl._MAX_FILES = 10
        try:
            files = load_code_files(tmp_path, "myrepo", "**/*.py")
            assert len(files) == 10
        finally:
            cl._MAX_FILES = original


class TestEdgeCases:
    def test_empty_graders_returns_non_conforming(self) -> None:
        task = Task(
            task_id="eng.test.no_graders",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "test", "scan_target": "**/*.py"}),
            graders=[],
            pass_threshold=0.95,
        )
        result = evaluate_file(task, "test.py", "some content")
        assert result.conforming is False
        assert len(result.grader_results) == 1
        assert "no graders" in result.grader_results[0].details.lower()

    def test_different_file_keys_per_grader(self) -> None:
        task = Task(
            task_id="eng.test.multikey",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "test", "scan_target": "**/*.py"}),
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "tenant_id", "file_key": "content"}),
                GraderSpec(type="pattern_forbidden", config={"pattern": "hardcoded", "file_key": "source"}),
            ],
            pass_threshold=0.95,
        )
        content = "query.filter(tenant_id == tid)"
        result = evaluate_file(task, "svc.py", content)
        # First grader uses file_key="content" → finds tenant_id → passes
        assert result.grader_results[0].passed is True
        # Second grader uses file_key="source" → content is set to same value → no "hardcoded" → passes
        assert result.grader_results[1].passed is True

    def test_required_grader_blocks_pass(self, tmp_path: Path) -> None:
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / "ok.py").write_text("def func(): pass\n")
        (repo / "bad.py").write_text("def func(): pass\n")

        task = Task(
            task_id="eng.test.required",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "myrepo", "scan_target": "**/*.py"}),
            graders=[
                GraderSpec(type="pattern_required", required=True, config={"pattern": "tenant_id"}),
            ],
            pass_threshold=0.0,  # score threshold is 0, but required should still block
        )
        result = run_task_against_code(task, tmp_path)
        assert result.passed is False

    def test_error_message_no_absolute_path(self, tmp_path: Path) -> None:
        task = Task(
            task_id="eng.test.nopath",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "nonexistent", "scan_target": "**/*.py"}),
            graders=[GraderSpec(type="pattern_required", config={"pattern": "x"})],
            pass_threshold=0.95,
        )
        result = run_task_against_code(task, tmp_path)
        assert str(tmp_path) not in (result.error or "")
