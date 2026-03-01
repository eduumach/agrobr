from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from agrobr.utils.result import finalize_result


@pytest.fixture()
def sample_df():
    return pd.DataFrame({"col": [1, 2, 3]})


@pytest.fixture()
def sample_meta():
    return {"source": "test", "records": 3}


class TestFinalizeResultPandas:
    def test_returns_df_by_default(self, sample_df):
        result = finalize_result(sample_df)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_returns_df_with_meta(self, sample_df, sample_meta):
        df, meta = finalize_result(sample_df, sample_meta, return_meta=True)
        pd.testing.assert_frame_equal(df, sample_df)
        assert meta is sample_meta

    def test_returns_df_when_as_polars_false(self, sample_df, sample_meta):
        result = finalize_result(sample_df, sample_meta, as_polars=False, return_meta=False)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_meta_none_no_return_meta(self, sample_df):
        result = finalize_result(sample_df, None, as_polars=False)
        pd.testing.assert_frame_equal(result, sample_df)

    def test_meta_none_with_return_meta(self, sample_df):
        df, meta = finalize_result(sample_df, None, return_meta=True)
        pd.testing.assert_frame_equal(df, sample_df)
        assert meta is None


class TestFinalizeResultPolars:
    def test_returns_polars_df(self, sample_df):
        pl = pytest.importorskip("polars")
        result = finalize_result(sample_df, as_polars=True)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 1)

    def test_returns_polars_with_meta(self, sample_df, sample_meta):
        pl = pytest.importorskip("polars")
        result_df, meta = finalize_result(sample_df, sample_meta, as_polars=True, return_meta=True)
        assert isinstance(result_df, pl.DataFrame)
        assert meta is sample_meta

    def test_polars_import_error_fallback(self, sample_df):
        with patch.dict("sys.modules", {"polars": None}):
            result = finalize_result(sample_df, as_polars=True)
            pd.testing.assert_frame_equal(result, sample_df)

    def test_polars_import_error_fallback_with_meta(self, sample_df, sample_meta):
        with patch.dict("sys.modules", {"polars": None}):
            df, meta = finalize_result(sample_df, sample_meta, as_polars=True, return_meta=True)
            pd.testing.assert_frame_equal(df, sample_df)
            assert meta is sample_meta
