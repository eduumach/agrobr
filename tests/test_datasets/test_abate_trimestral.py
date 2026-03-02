from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest

from agrobr.datasets.abate_trimestral import AbateTrimestralDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        [
            {
                "trimestre": "202303",
                "localidade": "Brasil",
                "localidade_cod": 1,
                "especie": "bovino",
                "animais_abatidos": 8500000.0,
                "peso_carcacas": 2200000.0,
                "fonte": "ibge_abate",
            },
        ]
    )


class TestAbateTrimestralFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = AbateTrimestralDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("bovino")

        assert len(df) == 1
        assert "animais_abatidos" in df.columns
        assert "peso_carcacas" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = AbateTrimestralDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("bovino", return_meta=True)

        assert meta.dataset == "abate_trimestral"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_abate"]
        assert meta.selected_source == "ibge_abate"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = AbateTrimestralDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestAbateTrimestralKwargs:
    @pytest.mark.asyncio
    async def test_passes_trimestre_kwarg(self):
        dataset = AbateTrimestralDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("bovino", trimestre="202303")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["trimestre"] == "202303"

    @pytest.mark.asyncio
    async def test_passes_uf_kwarg(self):
        dataset = AbateTrimestralDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("bovino", uf="SP")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["uf"] == "SP"


class TestAbateTrimestralSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = AbateTrimestralDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("bovino")
