from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest

from agrobr.datasets.preco_diario import PRECO_DIARIO_INFO, PrecoDiarioDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_df():
    return pd.DataFrame(
        [
            {
                "data": pd.Timestamp("2025-01-15"),
                "valor": 145.30,
                "unidade": "R$/saca 60kg",
                "produto": "soja",
                "fonte": "cepea",
                "praca": "Paranaguá",
            },
            {
                "data": pd.Timestamp("2025-01-14"),
                "valor": 144.80,
                "unidade": "R$/saca 60kg",
                "produto": "soja",
                "fonte": "cepea",
                "praca": "Paranaguá",
            },
        ]
    )


class TestPrecoDiarioSpecific:
    def test_info_cepea_priority(self):
        cepea_source = next(s for s in PRECO_DIARIO_INFO.sources if s.name == "cepea")
        cache_source = next(s for s in PRECO_DIARIO_INFO.sources if s.name == "cache")
        assert cepea_source.priority < cache_source.priority


class TestPrecoDiarioFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = PrecoDiarioDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("soja")

        assert len(df) == 2
        assert "data" in df.columns
        assert "valor" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = PrecoDiarioDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.dataset == "preco_diario"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["cepea"]
        assert meta.selected_source == "cepea"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = PrecoDiarioDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestPrecoDiarioNormalize:
    @pytest.mark.asyncio
    async def test_normalize_sorts_descending(self):
        df = pd.DataFrame(
            [
                {
                    "data": pd.Timestamp("2025-01-10"),
                    "valor": 140.0,
                    "unidade": "R$/saca 60kg",
                },
                {
                    "data": pd.Timestamp("2025-01-15"),
                    "valor": 145.0,
                    "unidade": "R$/saca 60kg",
                },
            ]
        )
        dataset = PrecoDiarioDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        result = await dataset.fetch("soja")

        assert result["data"].iloc[0] > result["data"].iloc[1]

    @pytest.mark.asyncio
    async def test_normalize_adds_produto_fonte(self):
        df = pd.DataFrame(
            [
                {
                    "data": pd.Timestamp("2025-01-15"),
                    "valor": 145.0,
                    "unidade": "R$/saca 60kg",
                },
            ]
        )
        dataset = PrecoDiarioDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        result = await dataset.fetch("soja")

        assert result["produto"].iloc[0] == "soja"
        assert result["fonte"].iloc[0] == "cepea"

    @pytest.mark.asyncio
    async def test_normalize_missing_required_raises(self):
        df = pd.DataFrame(
            [
                {
                    "data": pd.Timestamp("2025-01-15"),
                    "unidade": "R$/saca 60kg",
                },
            ]
        )
        dataset = PrecoDiarioDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        with pytest.raises(ValueError, match="Missing required column"):
            await dataset.fetch("soja")


class TestPrecoDiarioFallback:
    @pytest.mark.asyncio
    async def test_cepea_fails_falls_back_to_cache(self):
        dataset = PrecoDiarioDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))
        cache_meta = mock_source_meta()
        dataset.info.sources[1].fetch_fn = make_source(_mock_df(), cache_meta)

        df, meta = await dataset.fetch("soja", return_meta=True)

        assert len(df) == 2
        assert meta.attempted_sources == ["cepea", "cache"]
        assert meta.selected_source == "cache"
        assert meta.from_cache is True

    @pytest.mark.asyncio
    async def test_all_sources_fail(self):
        dataset = PrecoDiarioDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))
        dataset.info.sources[1].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")
