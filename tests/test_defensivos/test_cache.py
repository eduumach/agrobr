from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import pytest

from agrobr.defensivos import cache


@pytest.fixture()
def _patch_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cache, "_cache_dir", lambda: tmp_path)


@pytest.mark.usefixtures("_patch_cache_dir")
class TestCache:
    def test_round_trip(self):
        df = pd.DataFrame({"nr_registro": ["001", "002"], "marca": ["A", "B"]})
        cache.write_cache("formulados", df)
        result = cache.read_cached("formulados")
        assert result is not None
        assert len(result) == 2
        assert result.columns.tolist() == ["nr_registro", "marca"]

    def test_stale_cache_returns_none(self, tmp_path: Path):
        df = pd.DataFrame({"a": [1]})
        cache.write_cache("test", df)
        path = tmp_path / "test.parquet"
        old_mtime = time.time() - cache.TTL_SECONDS - 100
        import os

        os.utime(path, (old_mtime, old_mtime))
        result = cache.read_cached("test")
        assert result is None

    def test_missing_cache_returns_none(self):
        result = cache.read_cached("nonexistent")
        assert result is None

    def test_corrupt_parquet_returns_none(self, tmp_path: Path):
        path = tmp_path / "corrupt.parquet"
        path.write_bytes(b"not a parquet file")
        result = cache.read_cached("corrupt")
        assert result is None
        assert not path.exists()

    def test_invalidate(self, tmp_path: Path):
        df = pd.DataFrame({"a": [1]})
        cache.write_cache("file1", df)
        cache.write_cache("file2", df)
        assert len(list(tmp_path.glob("*.parquet"))) == 2
        cache.invalidate()
        assert len(list(tmp_path.glob("*.parquet"))) == 0

    def test_write_formulados_pair(self):
        form_df = pd.DataFrame({"nr_registro": ["001"], "marca": ["A"]})
        auth_df = pd.DataFrame({"nr_registro": ["001"], "cultura": ["SOJA"]})
        cache.write_formulados_pair(form_df, auth_df)
        f = cache.read_cached("formulados")
        a = cache.read_cached("autorizacoes")
        assert f is not None
        assert a is not None
        assert len(f) == 1
        assert len(a) == 1
