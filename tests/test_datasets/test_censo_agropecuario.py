from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.censo_agropecuario import CensoAgropecuarioDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 2017,
                "localidade": "Brasil",
                "localidade_cod": 1,
                "tema": "efetivo_rebanho",
                "categoria": "bovino",
                "variavel": "numero_estabelecimentos",
                "valor": 2500000.0,
                "unidade": "Estabelecimentos",
                "fonte": "ibge_censo_agro",
            },
        ]
    )


class TestCensoAgropecuarioFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = CensoAgropecuarioDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("efetivo_rebanho")

        assert len(df) == 1
        assert "tema" in df.columns
        assert "valor" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = CensoAgropecuarioDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("efetivo_rebanho", return_meta=True)

        assert meta.dataset == "censo_agropecuario"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_censo_agro"]
        assert meta.selected_source == "ibge_censo_agro"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = CensoAgropecuarioDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestCensoAgropecuarioKwargs:
    @pytest.mark.asyncio
    async def test_passes_uf_kwarg(self):
        dataset = CensoAgropecuarioDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("efetivo_rebanho", uf="MG")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["uf"] == "MG"

    @pytest.mark.asyncio
    async def test_passes_nivel_kwarg(self):
        dataset = CensoAgropecuarioDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("efetivo_rebanho", nivel="municipio")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["nivel"] == "municipio"


class TestCensoAgropecuarioSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = CensoAgropecuarioDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("efetivo_rebanho")


class TestCensoAgropecuarioFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_ibge_censo_agro_forwards_params(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.censo_agro", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.censo_agropecuario import _fetch_ibge_censo_agro

            await _fetch_ibge_censo_agro("efetivo_rebanho", uf="MG", nivel="municipio")
        mock_fn.assert_called_once_with(
            "efetivo_rebanho", uf="MG", nivel="municipio", return_meta=True
        )

    @pytest.mark.asyncio
    async def test_fetch_ibge_censo_agro_defaults(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.censo_agro", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.censo_agropecuario import _fetch_ibge_censo_agro

            await _fetch_ibge_censo_agro("uso_terra")
        _, kwargs = mock_fn.call_args
        assert kwargs["uf"] is None
        assert kwargs["nivel"] == "uf"
