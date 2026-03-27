from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.deterministic import deterministic
from agrobr.datasets.silvicultura import (
    SILVICULTURA_INFO,
    SilviculturaDataset,
    silvicultura,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 2022,
                "localidade": "Minas Gerais",
                "localidade_cod": 31,
                "produto": "eucalipto_folha",
                "valor": 800000.0,
                "unidade": "Toneladas",
                "fonte": "ibge_silvicultura",
            },
        ]
    )


class TestSilviculturaInfo:
    def test_single_source(self):
        assert len(SILVICULTURA_INFO.sources) == 1
        assert SILVICULTURA_INFO.sources[0].name == "ibge_silvicultura"

    def test_license_livre(self):
        assert SILVICULTURA_INFO.license == "livre"


class TestSilviculturaFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("eucalipto_folha")

        assert len(df) == 1
        assert "valor" in df.columns
        assert "unidade" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("eucalipto_folha", return_meta=True)

        assert meta.dataset == "silvicultura"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_silvicultura"]
        assert meta.selected_source == "ibge_silvicultura"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = SilviculturaDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("soja")

    @pytest.mark.asyncio
    async def test_snapshot_sets_ano_minus_1(self):
        dataset = SilviculturaDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("eucalipto_folha")

        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] == 2023

    @pytest.mark.asyncio
    async def test_snapshot_does_not_override_explicit_ano(self):
        dataset = SilviculturaDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("eucalipto_folha", ano=2021)

        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] == 2021


class TestSilviculturaKwargs:
    @pytest.mark.asyncio
    async def test_passes_variavel_kwarg(self):
        mock_fn = make_source(_mock_df())
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("eucalipto_folha", variavel="valor_producao")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["variavel"] == "valor_producao"

    @pytest.mark.asyncio
    async def test_passes_nivel_and_uf(self):
        mock_fn = make_source(_mock_df())
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("eucalipto_folha", nivel="municipio", uf="MG")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["nivel"] == "municipio"
        assert call_kwargs["uf"] == "MG"


class TestSilviculturaSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = SilviculturaDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            pd.DataFrame(), raises=httpx.ConnectError("test")
        )

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("eucalipto_folha")


class TestSilviculturaPublicAPI:
    @pytest.mark.asyncio
    async def test_public_function_delegates(self):
        with patch.object(SilviculturaDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = _mock_df()
            await silvicultura("eucalipto_folha", ano=2022, nivel="uf", uf="MG")

            mock_fetch.assert_called_once_with(
                "eucalipto_folha",
                ano=2022,
                nivel="uf",
                uf="MG",
                variavel="quantidade_produzida",
                return_meta=False,
            )

    @pytest.mark.asyncio
    async def test_public_function_return_meta(self):
        with patch.object(SilviculturaDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (_mock_df(), mock_source_meta())
            result = await silvicultura("eucalipto_folha", return_meta=True)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], pd.DataFrame)


class TestSilviculturaFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_ibge_silvicultura_forwards_params(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.silvicultura", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.silvicultura import _fetch_ibge_silvicultura

            await _fetch_ibge_silvicultura(
                "eucalipto_folha", ano=2022, nivel="municipio", uf="MG", variavel="valor_producao"
            )
        mock_fn.assert_called_once_with(
            "eucalipto_folha",
            ano=2022,
            nivel="municipio",
            uf="MG",
            variavel="valor_producao",
            return_meta=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_ibge_silvicultura_defaults(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.silvicultura", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.silvicultura import _fetch_ibge_silvicultura

            await _fetch_ibge_silvicultura("carvao")
        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] is None
        assert kwargs["nivel"] == "uf"
        assert kwargs["uf"] is None
        assert kwargs["variavel"] == "quantidade_produzida"
