from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.posicionamento_fundos import (
    POSICIONAMENTO_FUNDOS_INFO,
    PosicionamentoFundosDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _make_df(**overrides):
    row = {
        "data": pd.Timestamp("2026-06-02"),
        "commodity": "soja",
        "contrato": "SOYBEANS - CHICAGO BOARD OF TRADE",
        "codigo_cftc": "005602",
        "open_interest": 1054882,
        "managed_money_long": 264854,
        "managed_money_short": 109074,
        "managed_money_spread": 71474,
        "managed_money_net": 155780,
        "producer_long": 226895,
        "producer_short": 477906,
        "swap_long": 137395,
        "swap_short": 27302,
        "other_long": 81696,
        "other_short": 52131,
        "nonreportable_long": 67713,
        "nonreportable_short": 48259,
        "change_managed_money_long": 1690,
        "change_managed_money_short": -8533,
        "change_open_interest": 6324,
    }
    row.update(overrides)
    df = pd.DataFrame([row])
    for col in df.columns:
        if col.startswith("change_"):
            df[col] = df[col].astype("Int64")
    return df


class TestPosicionamentoFundosFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_df(self):
        dataset = PosicionamentoFundosDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch("soja")

        assert len(df) == 1
        assert "managed_money_net" in df.columns
        assert df.iloc[0]["commodity"] == "soja"

    @pytest.mark.asyncio
    async def test_params_passthrough(self):
        mock_fn = make_source(_make_df())
        dataset = PosicionamentoFundosDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch("soja", start="2026-01-01", end="2026-06-01", combined=True)

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["start"] == "2026-01-01"
        assert call_kwargs["end"] == "2026-06-01"
        assert call_kwargs["combined"] is True

    @pytest.mark.asyncio
    async def test_return_meta(self):
        dataset = PosicionamentoFundosDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.dataset == "posicionamento_fundos"
        assert meta.contract_version == "1.0"
        assert "cftc" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_snapshot_define_end(self):
        mock_fn = make_source(_make_df())
        dataset = PosicionamentoFundosDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        from agrobr.datasets.deterministic import deterministic

        async with deterministic("2020-06-15"):
            await dataset.fetch("soja")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["end"] == "2020-06-15"

    @pytest.mark.asyncio
    async def test_end_explicito_vence_snapshot(self):
        mock_fn = make_source(_make_df())
        dataset = PosicionamentoFundosDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        from agrobr.datasets.deterministic import deterministic

        async with deterministic("2020-06-15"):
            await dataset.fetch("soja", end="2019-12-31")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["end"] == "2019-12-31"

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = PosicionamentoFundosDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")


class TestPosicionamentoFundosValidation:
    def test_invalid_produto(self):
        dataset = PosicionamentoFundosDataset()
        with pytest.raises(ValueError, match="banana_inexistente"):
            dataset._validate_produto("banana_inexistente")


class TestPosicionamentoFundosInfo:
    def test_source_cftc(self):
        assert len(POSICIONAMENTO_FUNDOS_INFO.sources) == 1
        assert POSICIONAMENTO_FUNDOS_INFO.sources[0].name == "cftc"

    def test_products_count(self):
        assert len(POSICIONAMENTO_FUNDOS_INFO.products) == 12

    def test_license_livre(self):
        assert POSICIONAMENTO_FUNDOS_INFO.license == "livre"

    def test_update_frequency_weekly(self):
        assert POSICIONAMENTO_FUNDOS_INFO.update_frequency == "weekly"


class TestPosicionamentoFundosFetchFunction:
    @pytest.mark.asyncio
    async def test_fetch_cftc_forwards_params(self):
        df = _make_df()
        meta = mock_source_meta()
        with patch("agrobr.cftc.cot", new_callable=AsyncMock, return_value=(df, meta)) as mock_fn:
            from agrobr.datasets.posicionamento_fundos import _fetch_cftc_cot

            await _fetch_cftc_cot("soja", start="2026-01-01", end="2026-06-01", combined=True)

        mock_fn.assert_called_once_with(
            "soja",
            start="2026-01-01",
            end="2026-06-01",
            combined=True,
            return_meta=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_cftc_defaults(self):
        df = _make_df()
        meta = mock_source_meta()
        with patch("agrobr.cftc.cot", new_callable=AsyncMock, return_value=(df, meta)) as mock_fn:
            from agrobr.datasets.posicionamento_fundos import _fetch_cftc_cot

            await _fetch_cftc_cot("soja")

        _, kwargs = mock_fn.call_args
        assert kwargs["start"] is None
        assert kwargs["end"] is None
        assert kwargs["combined"] is False
