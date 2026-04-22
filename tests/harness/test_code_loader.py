"""Tests for the Code Loader — engineering eval against actual code files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from unittest.mock import patch

from gbr_eval.harness.code_loader import (
    FileResult,
    evaluate_file,
    load_code_files,
    run_engineering_suite,
    run_task_against_code,
    run_task_holistic,
)
from gbr_eval.harness.models import (
    Category,
    EvaluationMode,
    GraderResult,
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


# ---------------------------------------------------------------------------
# Holistic evaluation mode tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def holistic_code_dir(tmp_path: Path) -> Path:
    """Create a fake frontend repo for holistic evaluation testing."""
    repo = tmp_path / "my-frontend"
    repo.mkdir()

    src = repo / "src" / "app"
    src.mkdir(parents=True)
    (src / "page.tsx").write_text(
        "export default function Dashboard() {\n"
        "  return <div>Summary cards, alerts, latest run</div>;\n"
        "}\n"
    )

    comp = repo / "src" / "components"
    comp.mkdir(parents=True)
    (comp / "run-list.tsx").write_text(
        "export function RunList() {\n"
        "  return <table>Runs</table>;\n"
        "}\n"
    )

    api = repo / "src" / "app" / "api"
    api.mkdir(parents=True)
    (api / "route.ts").write_text(
        "export async function POST(req: Request) {\n"
        "  // webhook handler\n"
        "  return Response.json({ ok: true });\n"
        "}\n"
    )

    return tmp_path


def _make_holistic_task(
    *,
    graders: list[GraderSpec] | None = None,
    evaluation_mode: EvaluationMode = EvaluationMode.HOLISTIC,
    pass_threshold: float = 0.5,
) -> Task:
    """Helper to build a holistic task for testing."""
    if graders is None:
        graders = [
            GraderSpec(
                type="pattern_required",
                config={"pattern": "webhook", "file_key": "content"},
            ),
        ]
    return Task(
        task_id="product.test.holistic",
        category=Category.CLASSIFICATION,
        component="my-frontend",
        layer=Layer.PRODUCT,
        input=TaskInput(
            payload={"repo": "my-frontend", "scan_target": "src/**/*.tsx"},
        ),
        graders=graders,
        evaluation_mode=evaluation_mode,
        pass_threshold=pass_threshold,
    )


class TestRunTaskAgainstCodeDispatch:
    """Verify run_task_against_code dispatches correctly based on evaluation_mode."""

    def test_per_file_mode_works_as_before(self, holistic_code_dir: Path) -> None:
        """PER_FILE mode should use the original per-file scoring."""
        task = _make_holistic_task(
            evaluation_mode=EvaluationMode.PER_FILE,
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "export"}),
            ],
        )
        result = run_task_against_code(task, holistic_code_dir)
        # All .tsx files have "export", so score = 2/2 = 1.0
        assert result.score == 1.0
        assert result.passed is True

    def test_holistic_mode_dispatches_to_holistic(self, holistic_code_dir: Path) -> None:
        """HOLISTIC mode should call run_task_holistic."""
        task = _make_holistic_task(
            evaluation_mode=EvaluationMode.HOLISTIC,
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "export"}),
            ],
        )
        with patch(
            "gbr_eval.harness.code_loader.run_task_holistic",
            wraps=run_task_holistic,
        ) as mock_holistic:
            result = run_task_against_code(task, holistic_code_dir)
            mock_holistic.assert_called_once()
        assert result.score > 0


class TestRunTaskHolistic:
    """Tests for the holistic evaluation path."""

    def test_missing_repo_returns_error(self, tmp_path: Path) -> None:
        task = _make_holistic_task()
        task.input.payload = {}  # no repo
        result = run_task_holistic(task, tmp_path)
        assert result.passed is False
        assert result.error == "Task missing input.payload.repo"

    def test_no_files_found_returns_error(self, tmp_path: Path) -> None:
        repo = tmp_path / "my-frontend"
        repo.mkdir()
        task = _make_holistic_task()
        result = run_task_holistic(task, tmp_path)
        assert result.passed is False
        assert "No files found" in (result.error or "")

    def test_deterministic_graders_run_per_file(self, holistic_code_dir: Path) -> None:
        """Deterministic graders should produce one result per file."""
        task = _make_holistic_task(
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "export"}),
            ],
        )
        result = run_task_holistic(task, holistic_code_dir)
        # Should have one grader result per .tsx file
        assert len(result.grader_results) == 2  # page.tsx + run-list.tsx
        file_paths = {r.file_path for r in result.grader_results}
        assert "src/app/page.tsx" in file_paths
        assert "src/components/run-list.tsx" in file_paths

    def test_deterministic_only_holistic_uses_conformance_ratio(
        self, holistic_code_dir: Path,
    ) -> None:
        """Without LLM graders, holistic falls back to deterministic conformance ratio."""
        task = _make_holistic_task(
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "Dashboard"}),
            ],
            pass_threshold=0.0,
        )
        result = run_task_holistic(task, holistic_code_dir)
        # Only page.tsx has "Dashboard", run-list.tsx does not.
        # Score = 1 pass / 2 total = 0.5
        assert result.score == pytest.approx(0.5)

    def test_required_deterministic_failure_vetoes(self, holistic_code_dir: Path) -> None:
        """A required deterministic grader failure should veto the holistic score."""
        task = _make_holistic_task(
            graders=[
                GraderSpec(
                    type="pattern_required",
                    required=True,
                    config={"pattern": "NONEXISTENT_PATTERN"},
                ),
            ],
            pass_threshold=0.0,
        )
        result = run_task_holistic(task, holistic_code_dir)
        assert result.passed is False

    def test_llm_grader_called_once_with_aggregated_content(
        self, holistic_code_dir: Path,
    ) -> None:
        """LLM grader should be called once with aggregated content, not per-file."""
        mock_result = GraderResult(
            grader_type="engineering_judge",
            field="test_review",
            passed=True,
            score=0.75,
            weight=1.0,
            details="score=4/5: Good implementation",
        )

        call_count = 0
        call_outputs: list[dict] = []

        def mock_grade(
            grader_name: str,
            output: dict,
            expected: dict,
            spec: GraderSpec,
            context: object = None,
        ) -> GraderResult:
            nonlocal call_count
            if grader_name == "engineering_judge":
                call_count += 1
                call_outputs.append(output)
                return mock_result
            # For deterministic graders, use the real grade function.
            from gbr_eval.graders.base import grade as real_grade

            return real_grade(grader_name, output, expected, spec, context=context)

        task = _make_holistic_task(
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "export"}),
                GraderSpec(
                    type="engineering_judge",
                    field="test_review",
                    required=True,
                    config={
                        "rubric": "Test rubric",
                        "min_score": 3.0,
                        "file_key": "content",
                    },
                ),
            ],
            pass_threshold=0.5,
        )

        with patch("gbr_eval.harness.code_loader.grade", side_effect=mock_grade):
            run_task_holistic(task, holistic_code_dir)

        # LLM grader should be called exactly once.
        assert call_count == 1
        # The aggregated content should contain file listings.
        aggregated = call_outputs[0]["content"]
        assert "Codebase Overview" in aggregated
        assert "src/app/page.tsx" in aggregated

    def test_holistic_score_uses_llm_score(self, holistic_code_dir: Path) -> None:
        """In holistic mode, the primary score should come from the LLM grader."""
        mock_result = GraderResult(
            grader_type="engineering_judge",
            field="test_review",
            passed=True,
            score=0.75,
            weight=1.0,
            details="score=4/5: Good",
        )

        task = _make_holistic_task(
            graders=[
                GraderSpec(
                    type="engineering_judge",
                    field="test_review",
                    config={
                        "rubric": "Test rubric",
                        "min_score": 3.0,
                        "file_key": "content",
                    },
                ),
            ],
            pass_threshold=0.5,
        )

        with patch(
            "gbr_eval.harness.code_loader.grade",
            return_value=mock_result,
        ):
            result = run_task_holistic(task, holistic_code_dir)

        assert result.score == 0.75
        assert result.passed is True

    def test_holistic_llm_result_has_holistic_file_path(
        self, holistic_code_dir: Path,
    ) -> None:
        """LLM grader results in holistic mode should have file_path='[holistic]'."""
        mock_result = GraderResult(
            grader_type="engineering_judge",
            field="test_review",
            passed=True,
            score=0.75,
            weight=1.0,
            details="score=4/5",
        )

        task = _make_holistic_task(
            graders=[
                GraderSpec(
                    type="engineering_judge",
                    field="test_review",
                    config={
                        "rubric": "Test rubric",
                        "file_key": "content",
                    },
                ),
            ],
        )

        with patch(
            "gbr_eval.harness.code_loader.grade",
            return_value=mock_result,
        ):
            result = run_task_holistic(task, holistic_code_dir)

        llm_results = [r for r in result.grader_results if r.grader_type == "engineering_judge"]
        assert len(llm_results) == 1
        assert llm_results[0].file_path == "[holistic]"

    def test_deterministic_context_passed_to_llm(self, holistic_code_dir: Path) -> None:
        """Deterministic grader results should be passed as context to the LLM grader."""
        captured_context = []

        def mock_grade(
            grader_name: str,
            output: dict,
            expected: dict,
            spec: GraderSpec,
            context: object = None,
        ) -> GraderResult:
            if grader_name == "engineering_judge":
                captured_context.append(context)
                return GraderResult(
                    grader_type="engineering_judge",
                    field="review",
                    passed=True,
                    score=0.75,
                    weight=1.0,
                    details="score=4/5",
                )
            from gbr_eval.graders.base import grade as real_grade

            return real_grade(grader_name, output, expected, spec, context=context)

        task = _make_holistic_task(
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "export"}),
                GraderSpec(
                    type="engineering_judge",
                    field="review",
                    config={"rubric": "Test", "file_key": "content"},
                ),
            ],
        )

        with patch("gbr_eval.harness.code_loader.grade", side_effect=mock_grade):
            run_task_holistic(task, holistic_code_dir)

        assert len(captured_context) == 1
        ctx = captured_context[0]
        assert ctx is not None
        assert len(ctx.previous_results) == 2  # 2 .tsx files each graded by pattern_required

    def test_duration_tracked(self, holistic_code_dir: Path) -> None:
        task = _make_holistic_task(
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "export"}),
            ],
        )
        result = run_task_holistic(task, holistic_code_dir)
        assert result.duration_ms > 0

    def test_mixed_graders_required_llm_failure_vetoes(
        self, holistic_code_dir: Path,
    ) -> None:
        """A required LLM grader that fails should veto the holistic pass."""
        mock_result = GraderResult(
            grader_type="engineering_judge",
            field="review",
            passed=False,
            score=0.0,
            weight=1.0,
            required=True,
            details="score=1/5: Critical failures",
        )

        task = _make_holistic_task(
            graders=[
                GraderSpec(
                    type="engineering_judge",
                    field="review",
                    required=True,
                    config={"rubric": "Test", "file_key": "content"},
                ),
            ],
            pass_threshold=0.0,
        )

        with patch(
            "gbr_eval.harness.code_loader.grade",
            return_value=mock_result,
        ):
            result = run_task_holistic(task, holistic_code_dir)

        assert result.passed is False


class TestEvaluationModeBackwardCompatibility:
    """Verify that existing tasks without evaluation_mode work identically."""

    def test_default_evaluation_mode_is_per_file(self) -> None:
        task = Task(
            task_id="eng.test.default",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(payload={"repo": "test", "scan_target": "**/*.py"}),
            graders=[GraderSpec(type="pattern_required", config={"pattern": "x"})],
            pass_threshold=0.95,
        )
        assert task.evaluation_mode == EvaluationMode.PER_FILE

    def test_per_file_scoring_unchanged(self, code_dir: Path) -> None:
        """The original per-file scoring should be completely unchanged."""
        task = Task(
            task_id="eng.test.unchanged",
            category=Category.CODE_QUALITY,
            component="test",
            layer=Layer.ENGINEERING,
            input=TaskInput(
                payload={"repo": "atom-back-end", "scan_target": "**/*.py"},
            ),
            graders=[
                GraderSpec(type="pattern_required", config={"pattern": "def "}),
            ],
            pass_threshold=0.95,
        )
        result = run_task_against_code(task, code_dir)
        assert result.score == 1.0
        assert result.passed is True
