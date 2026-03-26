from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from agrobr.rnc.cache import TTL_SECONDS, read_cached, write_cache


@pytest.fixture
def cache_dir(tmp_path):
    d = tmp_path / "rnc"
    d.mkdir()
    with patch("agrobr.rnc.cache._cache_dir", return_value=d):
        yield d


def test_write_then_read(cache_dir):  # noqa: ARG001
    df = pd.DataFrame({"cultivar": ["Soja1"], "data_registro": ["01/01/2020"]})
    write_cache("registradas", df)
    result = read_cached("registradas")
    assert result is not None
    assert len(result) == 1
    assert result["cultivar"].iloc[0] == "Soja1"


def test_read_nonexistent(cache_dir):  # noqa: ARG001
    assert read_cached("nope") is None


def test_stale_cache_returns_none(cache_dir):
    df = pd.DataFrame({"cultivar": ["X"]})
    write_cache("registradas", df)
    import os
    import time as _time

    path = cache_dir / "registradas.csv"
    old_time = _time.time() - TTL_SECONDS - 100
    os.utime(path, (old_time, old_time))
    assert read_cached("registradas") is None
    assert not path.exists()


def test_corrupt_cache_returns_none(cache_dir):
    path = cache_dir / "registradas.csv"
    path.write_bytes(b"\x80\x81\x82\xff\xfe\x00\x01")
    assert read_cached("registradas") is None


def test_date_round_trip(cache_dir):  # noqa: ARG001
    df = pd.DataFrame(
        {
            "cultivar": ["A"],
            "data_registro": pd.to_datetime(["2020-01-15"]),
            "data_validade": pd.to_datetime(["2035-01-15"]),
        }
    )
    write_cache("registradas", df)
    result = read_cached("registradas")
    assert result is not None
    assert pd.api.types.is_datetime64_any_dtype(result["data_registro"])
