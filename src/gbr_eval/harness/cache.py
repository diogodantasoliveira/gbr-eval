"""Content-hash cache for LLM grader results — avoids redundant API calls.

Only caches LLM grader results (engineering_judge, llm_judge).  Deterministic
graders are instant so caching them would add overhead for no gain.

Cache key = SHA-256(file_content + grader_type + sorted(config) + model_override).
Results with ``status=ERROR`` are never cached — transient failures must not persist.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gbr_eval.harness.models import GraderResult, GraderSpec, GraderStatus

if TYPE_CHECKING:
    from pathlib import Path

LLM_GRADER_TYPES: frozenset[str] = frozenset({"engineering_judge", "llm_judge"})

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS grader_cache (
    cache_key TEXT PRIMARY KEY,
    grader_type TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    puts: int = 0
    skipped_errors: int = 0

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / self.total if self.total > 0 else 0.0


class GraderCache:
    """SQLite-backed content-hash cache for LLM grader results.

    Args:
        cache_dir: Directory for the SQLite DB file.
        enabled: When ``False``, all operations are no-ops (``get`` always
            returns ``None``, ``put`` is silent).  Useful for ``--no-cache``.
    """

    def __init__(self, cache_dir: Path, *, enabled: bool = True) -> None:
        self._enabled = enabled
        self._stats = CacheStats()
        self._conn: sqlite3.Connection | None = None

        if enabled:
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "cache.db"
            self._conn = sqlite3.connect(str(db_path))
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute(_SCHEMA)
            self._conn.commit()

    @staticmethod
    def make_key(
        file_content: str,
        spec: GraderSpec,
        *,
        model_override: str = "",
    ) -> str:
        config_str = json.dumps(spec.config, sort_keys=True, ensure_ascii=False)
        parts = [file_content, spec.type, config_str, model_override]
        blob = "\0".join(parts).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def get(self, key: str) -> GraderResult | None:
        if not self._enabled or self._conn is None:
            self._stats.misses += 1
            return None

        row = self._conn.execute(
            "SELECT result_json FROM grader_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()

        if row is None:
            self._stats.misses += 1
            return None

        self._stats.hits += 1
        result = GraderResult.model_validate_json(row[0])
        if not result.details.startswith("[cached]"):
            result.details = f"[cached] {result.details}"
        return result

    def put(self, key: str, result: GraderResult) -> None:
        if not self._enabled or self._conn is None:
            return

        if result.status != GraderStatus.GRADED:
            self._stats.skipped_errors += 1
            return

        self._conn.execute(
            "INSERT OR REPLACE INTO grader_cache "
            "(cache_key, grader_type, result_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (key, result.grader_type, result.model_dump_json(), time.time()),
        )
        self._conn.commit()
        self._stats.puts += 1

    @property
    def stats(self) -> CacheStats:
        return self._stats

    def size(self) -> int:
        if not self._enabled or self._conn is None:
            return 0
        row = self._conn.execute("SELECT COUNT(*) FROM grader_cache").fetchone()
        return int(row[0]) if row else 0

    def clear(self) -> int:
        if not self._enabled or self._conn is None:
            return 0
        count = self.size()
        self._conn.execute("DELETE FROM grader_cache")
        self._conn.commit()
        return count

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
