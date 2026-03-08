from unittest.mock import patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.oferta_demanda_global import (
    OFERTA_DEMANDA_GLOBAL_INFO,
    OfertaDemandaGlobalDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _make_df(**overrides):
    row = {
        "commodity_code": "2222000",
        "commodity": "soja",
        "country_code": "BR",
        "country": "Brazil",
        "market_year": 2024,
        "attribute": "Production",
        "attribute_br": "Produção",
        "value": 154000.0,
        "unit": "(1000 MT)",
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestOfertaDemandaGlobalFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_df(self):
        dataset = OfertaDemandaGlobalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df = await dataset.fetch("soja")

        assert len(df) == 1
        assert "commodity_code" in df.columns
        assert "market_year" in df.columns
        assert df.iloc[0]["value"] == 154000.0

    @pytest.mark.asyncio
    async def test_params_passthrough(self):
        mock_fn = make_source(_make_df())
        dataset = OfertaDemandaGlobalDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch(
            "soja",
            country="US",
            market_year=2023,
            attributes=["Production"],
            pivot=False,
            api_key="test-key",
        )

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["country"] == "US"
        assert call_kwargs["market_year"] == 2023
        assert call_kwargs["attributes"] == ["Production"]
        assert call_kwargs["pivot"] is False
        assert call_kwargs["api_key"] == "test-key"

    @pytest.mark.asyncio
    async def test_return_meta(self):
        dataset = OfertaDemandaGlobalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())
        df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.dataset == "oferta_demanda_global"
        assert meta.contract_version == "1.0"
        assert "usda" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_snapshot_default_year(self):
        mock_fn = make_source(_make_df())
        dataset = OfertaDemandaGlobalDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        from agrobr.datasets.deterministic import deterministic

        async with deterministic("2023-06-15"):
            await dataset.fetch("soja")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["market_year"] == 2023

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = OfertaDemandaGlobalDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")


class TestOfertaDemandaGlobalValidation:
    def test_invalid_produto(self):
        dataset = OfertaDemandaGlobalDataset()
        with pytest.raises(ValueError, match="banana_inexistente"):
            dataset._validate_produto("banana_inexistente")

    @pytest.mark.asyncio
    async def test_contract_skipped_when_pivot(self):
        dataset = OfertaDemandaGlobalDataset()
        pivot_df = pd.DataFrame(
            [{"commodity_code": "2222000", "commodity": "soja", "Production": 154000.0}]
        )
        dataset.info.sources[0].fetch_fn = make_source(pivot_df)

        with patch.object(dataset, "_validate_contract") as mock_validate:
            await dataset.fetch("soja", pivot=True)
            mock_validate.assert_not_called()

    @pytest.mark.asyncio
    async def test_contract_called_when_not_pivot(self):
        dataset = OfertaDemandaGlobalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_df())

        with patch.object(dataset, "_validate_contract") as mock_validate:
            await dataset.fetch("soja", pivot=False)
            mock_validate.assert_called_once()


class TestOfertaDemandaGlobalInfo:
    def test_source_usda(self):
        assert len(OFERTA_DEMANDA_GLOBAL_INFO.sources) == 1
        assert OFERTA_DEMANDA_GLOBAL_INFO.sources[0].name == "usda"

    def test_products_count(self):
        assert len(OFERTA_DEMANDA_GLOBAL_INFO.products) == 8

    def test_license_livre(self):
        assert OFERTA_DEMANDA_GLOBAL_INFO.license == "livre"
