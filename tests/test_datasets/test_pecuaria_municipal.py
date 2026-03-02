from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest

from agrobr.datasets.deterministic import deterministic
from agrobr.datasets.pecuaria_municipal import PecuariaMunicipalDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 2022,
                "localidade": "Mato Grosso",
                "localidade_cod": 51,
                "especie": "bovino",
                "valor": 32000000.0,
                "unidade": "Cabeças",
                "fonte": "ibge_ppm",
            },
        ]
    )


class TestPecuariaMunicipalFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = PecuariaMunicipalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("bovino")

        assert len(df) == 1
        assert "valor" in df.columns
        assert "especie" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = PecuariaMunicipalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("bovino", return_meta=True)

        assert meta.dataset == "pecuaria_municipal"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_ppm"]
        assert meta.selected_source == "ibge_ppm"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = PecuariaMunicipalDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestPecuariaMunicipalKwargs:
    @pytest.mark.asyncio
    async def test_passes_ano_kwarg(self):
        dataset = PecuariaMunicipalDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("bovino", ano=2022)

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["ano"] == 2022

    @pytest.mark.asyncio
    async def test_passes_nivel_kwarg(self):
        dataset = PecuariaMunicipalDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("bovino", nivel="municipio")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["nivel"] == "municipio"

    @pytest.mark.asyncio
    async def test_passes_uf_kwarg(self):
        dataset = PecuariaMunicipalDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("bovino", uf="MT")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["uf"] == "MT"


class TestPecuariaMunicipalSnapshot:
    @pytest.mark.asyncio
    async def test_snapshot_sets_ano(self):
        dataset = PecuariaMunicipalDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic(snapshot="2023-06-15"):
            await dataset.fetch("bovino")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["ano"] == 2022


class TestPecuariaMunicipalSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = PecuariaMunicipalDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("bovino")
