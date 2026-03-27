from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.censo_agropecuario_legado import CensoAgropecuarioLegadoDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 1995,
                "localidade": "Brasil",
                "localidade_cod": 1,
                "tema": "tecnologia",
                "categoria": "irrigacao",
                "variavel": "numero_estabelecimentos",
                "valor": 100000.0,
                "unidade": "Estabelecimentos",
                "fonte": "ibge_censo_agro_legado",
            },
        ]
    )


class TestCensoAgropecuarioLegadoFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = CensoAgropecuarioLegadoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("tecnologia")

        assert len(df) == 1
        assert "tema" in df.columns
        assert "valor" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = CensoAgropecuarioLegadoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("tecnologia", return_meta=True)

        assert meta.dataset == "censo_agropecuario_legado"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_censo_agro_legado"]
        assert meta.selected_source == "ibge_censo_agro_legado"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = CensoAgropecuarioLegadoDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestCensoAgropecuarioLegadoKwargs:
    @pytest.mark.asyncio
    async def test_passes_uf_kwarg(self):
        dataset = CensoAgropecuarioLegadoDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("tecnologia", uf="RS")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["uf"] == "RS"

    @pytest.mark.asyncio
    async def test_passes_nivel_kwarg(self):
        dataset = CensoAgropecuarioLegadoDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("tecnologia", nivel="municipio")

        _, call_kwargs = mock_fn.call_args
        assert call_kwargs["nivel"] == "municipio"


class TestCensoAgropecuarioLegadoSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = CensoAgropecuarioLegadoDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("tecnologia")


class TestCensoAgropecuarioLegadoFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_ibge_censo_agro_legado_forwards_params(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.legacy_api.censo_agro_legado",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.censo_agropecuario_legado import _fetch_ibge_censo_agro_legado

            await _fetch_ibge_censo_agro_legado("tecnologia", uf="RS", nivel="municipio")
        mock_fn.assert_called_once_with("tecnologia", uf="RS", nivel="municipio", return_meta=True)

    @pytest.mark.asyncio
    async def test_fetch_ibge_censo_agro_legado_defaults(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.legacy_api.censo_agro_legado",
            new_callable=AsyncMock,
            return_value=(df, meta),
        ) as mock_fn:
            from agrobr.datasets.censo_agropecuario_legado import _fetch_ibge_censo_agro_legado

            await _fetch_ibge_censo_agro_legado("tecnologia")
        _, kwargs = mock_fn.call_args
        assert kwargs["uf"] is None
        assert kwargs["nivel"] == "uf"
