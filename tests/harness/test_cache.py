"""Tests for GraderCache — content-hash caching of LLM grader results."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from gbr_eval.harness.cache import GraderCache

if TYPE_CHECKING:
    from pathlib import Path
from gbr_eval.harness.models import GraderResult, GraderSpec, GraderStatus


@pytest.fixture()
def cache_dir(tmp_path: Path) -> Path:
    return tmp_path / "cache"


@pytest.fixture()
def cache(cache_dir: Path) -> GraderCache:
    return GraderCache(cache_dir, enabled=True)


def _make_spec(**overrides: object) -> GraderSpec:
    defaults = {
        "type": "engineering_judge",
        "field": "review",
        "config": {"rubric": "Check code quality", "min_score": 3.0, "model": "claude-opus"},
    }
    defaults.update(overrides)
    return GraderSpec(**defaults)  # type: ignore[arg-type]


def _make_result(**overrides: object) -> GraderResult:
    defaults = {
        "grader_type": "engineering_judge",
        "field": "review",
        "passed": True,
        "score": 0.75,
        "weight": 1.0,
        "details": "score=4/5 (min=3): Good code",
        "status": GraderStatus.GRADED,
    }
    defaults.update(overrides)
    return GraderResult(**defaults)  # type: ignore[arg-type]


class TestMakeKey:
    def test_deterministic(self) -> None:
        spec = _make_spec()
        k1 = GraderCache.make_key("code here", spec)
        k2 = GraderCache.make_key("code here", spec)
        assert k1 == k2

    def test_different_content_different_key(self) -> None:
        spec = _make_spec()
        k1 = GraderCache.make_key("code v1", spec)
        k2 = GraderCache.make_key("code v2", spec)
        assert k1 != k2

    def test_different_rubric_different_key(self) -> None:
        spec_a = _make_spec(config={"rubric": "rubric A"})
        spec_b = _make_spec(config={"rubric": "rubric B"})
        k1 = GraderCache.make_key("same code", spec_a)
        k2 = GraderCache.make_key("same code", spec_b)
        assert k1 != k2

    def test_different_model_override_different_key(self) -> None:
        spec = _make_spec()
        k1 = GraderCache.make_key("code", spec, model_override="opus")
        k2 = GraderCache.make_key("code", spec, model_override="sonnet")
        assert k1 != k2

    def test_key_is_hex_sha256(self) -> None:
        spec = _make_spec()
        key = GraderCache.make_key("code", spec)
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)


class TestGetPut:
    def test_miss_returns_none(self, cache: GraderCache) -> None:
        assert cache.get("nonexistent") is None

    def test_put_then_get(self, cache: GraderCache) -> None:
        result = _make_result()
        cache.put("key1", result)
        got = cache.get("key1")
        assert got is not None
        assert got.score == 0.75
        assert got.passed is True
        assert got.details.startswith("[cached]")

    def test_cached_prefix_not_doubled(self, cache: GraderCache) -> None:
        result = _make_result(details="[cached] already cached")
        cache.put("key2", result)
        got = cache.get("key2")
        assert got is not None
        assert got.details == "[cached] already cached"
        assert not got.details.startswith("[cached] [cached]")

    def test_error_results_not_cached(self, cache: GraderCache) -> None:
        result = _make_result(status=GraderStatus.ERROR, passed=False, score=0.0)
        cache.put("error_key", result)
        assert cache.get("error_key") is None
        assert cache.stats.skipped_errors == 1

    def test_skipped_results_not_cached(self, cache: GraderCache) -> None:
        result = _make_result(status=GraderStatus.SKIPPED)
        cache.put("skip_key", result)
        assert cache.get("skip_key") is None

    def test_overwrite_existing(self, cache: GraderCache) -> None:
        cache.put("key", _make_result(score=0.5))
        cache.put("key", _make_result(score=0.9))
        got = cache.get("key")
        assert got is not None
        assert got.score == 0.9


class TestDisabledCache:
    def test_disabled_get_returns_none(self, cache_dir: Path) -> None:
        c = GraderCache(cache_dir, enabled=False)
        assert c.get("any") is None
        assert c.stats.misses == 1

    def test_disabled_put_is_noop(self, cache_dir: Path) -> None:
        c = GraderCache(cache_dir, enabled=False)
        c.put("any", _make_result())
        assert c.stats.puts == 0

    def test_disabled_size_is_zero(self, cache_dir: Path) -> None:
        c = GraderCache(cache_dir, enabled=False)
        assert c.size() == 0

    def test_disabled_clear_is_zero(self, cache_dir: Path) -> None:
        c = GraderCache(cache_dir, enabled=False)
        assert c.clear() == 0


class TestStats:
    def test_initial_stats(self, cache: GraderCache) -> None:
        s = cache.stats
        assert s.hits == 0
        assert s.misses == 0
        assert s.puts == 0
        assert s.total == 0
        assert s.hit_rate == 0.0

    def test_stats_after_operations(self, cache: GraderCache) -> None:
        cache.get("miss1")
        cache.get("miss2")
        cache.put("k", _make_result())
        cache.get("k")  # hit
        s = cache.stats
        assert s.hits == 1
        assert s.misses == 2
        assert s.puts == 1
        assert s.total == 3
        assert abs(s.hit_rate - 1 / 3) < 0.01


class TestSizeAndClear:
    def test_size_reflects_entries(self, cache: GraderCache) -> None:
        assert cache.size() == 0
        cache.put("a", _make_result())
        cache.put("b", _make_result(score=0.5))
        assert cache.size() == 2

    def test_clear_deletes_all(self, cache: GraderCache) -> None:
        cache.put("a", _make_result())
        cache.put("b", _make_result())
        deleted = cache.clear()
        assert deleted == 2
        assert cache.size() == 0
        assert cache.get("a") is None


class TestPersistence:
    def test_survives_reopen(self, cache_dir: Path) -> None:
        c1 = GraderCache(cache_dir, enabled=True)
        c1.put("persist_key", _make_result(score=0.8))
        c1.close()

        c2 = GraderCache(cache_dir, enabled=True)
        got = c2.get("persist_key")
        assert got is not None
        assert got.score == 0.8
        c2.close()


class TestCacheIntegrationWithSpec:
    def test_full_flow_with_make_key(self, cache: GraderCache) -> None:
        spec = _make_spec()
        content = "function hello() { return 'world'; }"
        key = GraderCache.make_key(content, spec)

        assert cache.get(key) is None

        result = _make_result()
        cache.put(key, result)

        cached = cache.get(key)
        assert cached is not None
        assert cached.score == result.score
        assert cached.grader_type == "engineering_judge"

    def test_different_file_same_spec_different_key(self, cache: GraderCache) -> None:
        spec = _make_spec()
        k1 = GraderCache.make_key("file_v1", spec)
        k2 = GraderCache.make_key("file_v2", spec)

        cache.put(k1, _make_result(score=0.5))
        cache.put(k2, _make_result(score=0.9))

        r1 = cache.get(k1)
        r2 = cache.get(k2)
        assert r1 is not None and r2 is not None
        assert r1.score == 0.5
        assert r2.score == 0.9
