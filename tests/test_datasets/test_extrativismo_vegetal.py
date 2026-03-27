from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.deterministic import deterministic
from agrobr.datasets.extrativismo_vegetal import (
    EXTRATIVISMO_VEGETAL_INFO,
    ExtrativsmoVegetalDataset,
    extrativismo_vegetal,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 2022,
                "localidade": "Pará",
                "localidade_cod": 15,
                "produto": "acai",
                "valor": 1500000.0,
                "unidade": "Toneladas",
                "fonte": "ibge_extracao_vegetal",
            },
        ]
    )


class TestExtrativsmoVegetalInfo:
    def test_single_source(self):
        assert len(EXTRATIVISMO_VEGETAL_INFO.sources) == 1
        assert EXTRATIVISMO_VEGETAL_INFO.sources[0].name == "ibge_extracao_vegetal"

    def test_license_livre(self):
        assert EXTRATIVISMO_VEGETAL_INFO.license == "livre"


class TestExtrativsmoVegetalFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("acai")

        assert len(df) == 1
        assert "valor" in df.columns
        assert "unidade" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("acai", return_meta=True)

        assert meta.dataset == "extrativismo_vegetal"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_extracao_vegetal"]
        assert meta.selected_source == "ibge_extracao_vegetal"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = ExtrativsmoVegetalDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("soja")

    @pytest.mark.asyncio
    async def test_snapshot_sets_ano_minus_1(self):
        dataset = ExtrativsmoVegetalDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("acai")

        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] == 2023

    @pytest.mark.asyncio
    async def test_snapshot_does_not_override_explicit_ano(self):
        dataset = ExtrativsmoVegetalDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("acai", ano=2021)

        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] == 2021


class TestExtrativsmoVegetalKwargs:
    @pytest.mark.asyncio
    async def test_passes_variavel_kwarg(self):
        mock_fn = make_source(_mock_df())
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("acai", variavel="valor_producao")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["variavel"] == "valor_producao"

    @pytest.mark.asyncio
    async def test_passes_nivel_and_uf(self):
        mock_fn = make_source(_mock_df())
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("acai", nivel="municipio", uf="PA")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["nivel"] == "municipio"
        assert call_kwargs["uf"] == "PA"


class TestExtrativsmoVegetalSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = ExtrativsmoVegetalDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            pd.DataFrame(), raises=httpx.ConnectError("test")
        )

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("acai")


class TestExtrativsmoVegetalPublicAPI:
    @pytest.mark.asyncio
    async def test_public_function_delegates(self):
        with patch.object(ExtrativsmoVegetalDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = _mock_df()
            await extrativismo_vegetal("acai", ano=2022, nivel="uf", uf="PA")

            mock_fetch.assert_called_once_with(
                "acai",
                ano=2022,
                nivel="uf",
                uf="PA",
                variavel="quantidade_produzida",
                return_meta=False,
            )

    @pytest.mark.asyncio
    async def test_public_function_return_meta(self):
        with patch.object(ExtrativsmoVegetalDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (_mock_df(), mock_source_meta())
            result = await extrativismo_vegetal("acai", return_meta=True)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], pd.DataFrame)


class TestExtrativsmoVegetalFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_ibge_extracao_vegetal_forwards_params(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.extracao_vegetal", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.extrativismo_vegetal import _fetch_ibge_extracao_vegetal

            await _fetch_ibge_extracao_vegetal(
                "acai", ano=2022, nivel="municipio", uf="PA", variavel="valor_producao"
            )
        mock_fn.assert_called_once_with(
            "acai",
            ano=2022,
            nivel="municipio",
            uf="PA",
            variavel="valor_producao",
            return_meta=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_ibge_extracao_vegetal_defaults(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.ibge.extracao_vegetal", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.extrativismo_vegetal import _fetch_ibge_extracao_vegetal

            await _fetch_ibge_extracao_vegetal("castanha_para")
        _, kwargs = mock_fn.call_args
        assert kwargs["ano"] is None
        assert kwargs["nivel"] == "uf"
        assert kwargs["uf"] is None
        assert kwargs["variavel"] == "quantidade_produzida"
