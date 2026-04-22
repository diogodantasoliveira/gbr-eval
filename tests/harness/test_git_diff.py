"""Tests for git-diff mode — changed file detection and filtering."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from gbr_eval.harness.git_diff import filter_changed_files, get_changed_files

if TYPE_CHECKING:
    from pathlib import Path


class TestGetChangedFiles:
    def test_returns_changed_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("print('a')")
        (tmp_path / "b.py").write_text("print('b')")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="a.py\nb.py\n", stderr="",
        )
        with patch("gbr_eval.harness.git_diff.subprocess.run", return_value=mock_result):
            result = get_changed_files(tmp_path, "main")

        assert result == {"a.py", "b.py"}

    def test_excludes_deleted_files(self, tmp_path: Path) -> None:
        (tmp_path / "exists.py").write_text("ok")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="exists.py\ndeleted.py\n", stderr="",
        )
        with patch("gbr_eval.harness.git_diff.subprocess.run", return_value=mock_result):
            result = get_changed_files(tmp_path, "main")

        assert result == {"exists.py"}

    def test_empty_diff(self, tmp_path: Path) -> None:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        with patch("gbr_eval.harness.git_diff.subprocess.run", return_value=mock_result):
            result = get_changed_files(tmp_path, "main")

        assert result == set()

    def test_rejects_unsafe_branch_name(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Invalid branch name"):
            get_changed_files(tmp_path, "main; rm -rf /")

    def test_rejects_branch_with_spaces(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Invalid branch name"):
            get_changed_files(tmp_path, "main branch")

    def test_allows_slashes_and_dots(self, tmp_path: Path) -> None:
        (tmp_path / "f.py").write_text("ok")
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="f.py\n", stderr="",
        )
        with patch("gbr_eval.harness.git_diff.subprocess.run", return_value=mock_result):
            result = get_changed_files(tmp_path, "origin/feature/v1.2")
        assert result == {"f.py"}

    def test_not_a_git_repo(self, tmp_path: Path) -> None:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=128, stdout="",
            stderr="fatal: not a git repository",
        )
        with patch("gbr_eval.harness.git_diff.subprocess.run", return_value=mock_result), \
             pytest.raises(RuntimeError, match="Not a git repository"):
            get_changed_files(tmp_path, "main")

    def test_git_not_found(self, tmp_path: Path) -> None:
        with patch(
            "gbr_eval.harness.git_diff.subprocess.run",
            side_effect=FileNotFoundError("git"),
        ), pytest.raises(RuntimeError, match="git not found"):
            get_changed_files(tmp_path, "main")

    def test_generic_git_error(self, tmp_path: Path) -> None:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="",
            stderr="fatal: ambiguous argument",
        )
        with patch("gbr_eval.harness.git_diff.subprocess.run", return_value=mock_result), \
             pytest.raises(RuntimeError, match="git diff failed"):
            get_changed_files(tmp_path, "main")


class TestFilterChangedFiles:
    def test_filters_to_changed_only(self) -> None:
        all_files = [
            ("src/a.py", "content_a"),
            ("src/b.py", "content_b"),
            ("src/c.py", "content_c"),
        ]
        changed = {"src/a.py", "src/c.py"}
        result = filter_changed_files(all_files, changed)
        assert result == [("src/a.py", "content_a"), ("src/c.py", "content_c")]

    def test_empty_changed_returns_empty(self) -> None:
        all_files = [("src/a.py", "content")]
        result = filter_changed_files(all_files, set())
        assert result == []

    def test_empty_all_files(self) -> None:
        result = filter_changed_files([], {"src/a.py"})
        assert result == []

    def test_preserves_order(self) -> None:
        all_files = [
            ("z.py", "z"),
            ("a.py", "a"),
            ("m.py", "m"),
        ]
        changed = {"a.py", "z.py", "m.py"}
        result = filter_changed_files(all_files, changed)
        assert [p for p, _ in result] == ["z.py", "a.py", "m.py"]

    def test_no_overlap(self) -> None:
        all_files = [("src/a.py", "a")]
        changed = {"src/b.py"}
        result = filter_changed_files(all_files, changed)
        assert result == []
