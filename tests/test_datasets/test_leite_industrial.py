from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest

from agrobr.datasets.leite_industrial import LeiteIndustrialDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        [
            {
                "trimestre": "202301",
                "localidade": "Minas Gerais",
                "localidade_cod": 31,
                "leite_adquirido": 1800000.0,
                "leite_industrializado": 1500000.0,
                "preco_medio": 2.45,
                "fonte": "ibge_leite_trimestral",
            },
        ]
    )


class TestLeiteIndustrialFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = LeiteIndustrialDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("leite")

        assert len(df) == 1
        assert "leite_adquirido" in df.columns
        assert "preco_medio" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = LeiteIndustrialDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("leite", return_meta=True)

        assert meta.dataset == "leite_industrial"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_leite_trimestral"]
        assert meta.selected_source == "ibge_leite_trimestral"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = LeiteIndustrialDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestLeiteIndustrialKwargs:
    @pytest.mark.asyncio
    async def test_passes_trimestre_kwarg(self):
        dataset = LeiteIndustrialDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("leite", trimestre="202301")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["trimestre"] == "202301"

    @pytest.mark.asyncio
    async def test_passes_uf_kwarg(self):
        dataset = LeiteIndustrialDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("leite", uf="MG")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["uf"] == "MG"


class TestLeiteIndustrialOnlyLeite:
    @pytest.mark.asyncio
    async def test_only_accepts_leite(self):
        dataset = LeiteIndustrialDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("carne")


class TestLeiteIndustrialSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = LeiteIndustrialDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("leite")


class TestLeiteIndustrialFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_ibge_leite_trimestral_forwards_params(self):
        from unittest.mock import patch

        from .conftest import mock_source_meta

        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.leite_trimestral",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.leite_industrial import _fetch_ibge_leite_trimestral

            await _fetch_ibge_leite_trimestral("leite", trimestre="202301", uf="MG")
        mock_fn.assert_called_once_with(trimestre="202301", uf="MG", return_meta=True)

    @pytest.mark.asyncio
    async def test_fetch_ibge_leite_trimestral_defaults(self):
        from unittest.mock import patch

        from .conftest import mock_source_meta

        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.leite_trimestral",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.leite_industrial import _fetch_ibge_leite_trimestral

            await _fetch_ibge_leite_trimestral("leite")
        _, kwargs = mock_fn.call_args
        assert kwargs["trimestre"] is None
        assert kwargs["uf"] is None
