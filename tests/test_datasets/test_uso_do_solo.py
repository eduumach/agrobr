from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.uso_do_solo import (
    USO_DO_SOLO_INFO,
    UsodoSoloDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _make_cobertura_df(**overrides):
    row = {
        "bioma": "Cerrado",
        "estado": "MT",
        "classe_id": 3,
        "classe": "Formação Florestal",
        "nivel_0": "Floresta",
        "ano": 2022,
        "area_ha": 150000.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _make_transicao_df(**overrides):
    row = {
        "bioma": "Cerrado",
        "estado": "MT",
        "classe_de_id": 3,
        "classe_de": "Formação Florestal",
        "classe_para_id": 15,
        "classe_para": "Pastagem",
        "periodo": "2020-2021",
        "area_ha": 5000.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestUsodoSoloFetch:
    @pytest.mark.asyncio
    async def test_fetch_cobertura_returns_df(self):
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_cobertura_df())
        df = await dataset.fetch(tipo="cobertura")

        assert len(df) == 1
        assert "bioma" in df.columns
        assert "area_ha" in df.columns
        assert df.iloc[0]["area_ha"] == 150000.0

    @pytest.mark.asyncio
    async def test_fetch_transicao_returns_df(self):
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_transicao_df())
        df = await dataset.fetch(tipo="transicao")

        assert len(df) == 1
        assert "classe_de" in df.columns
        assert "classe_para" in df.columns
        assert "periodo" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_cobertura_params(self):
        mock_fn = make_source(_make_cobertura_df())
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch(tipo="cobertura", bioma="Cerrado", estado="MT", ano=2022, classe_id=3)

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["bioma"] == "Cerrado"
        assert call_kwargs["estado"] == "MT"
        assert call_kwargs["ano"] == 2022
        assert call_kwargs["classe_id"] == 3

    @pytest.mark.asyncio
    async def test_fetch_cobertura_municipal(self):
        df_municipal = _make_cobertura_df()
        df_municipal["municipio"] = "Cuiabá"
        mock_fn = make_source(df_municipal)
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        df = await dataset.fetch(tipo="cobertura", nivel="municipio", municipio="Cuiabá")

        assert len(df) == 1
        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["nivel"] == "municipio"
        assert call_kwargs["municipio"] == "Cuiabá"

    @pytest.mark.asyncio
    async def test_fetch_transicao_params(self):
        mock_fn = make_source(_make_transicao_df())
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch(
            tipo="transicao",
            periodo="2020-2021",
            classe_de_id=3,
            classe_para_id=15,
        )

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["periodo"] == "2020-2021"
        assert call_kwargs["classe_de_id"] == 3
        assert call_kwargs["classe_para_id"] == 15

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_cobertura_df())
        df, meta = await dataset.fetch(tipo="cobertura", return_meta=True)

        assert meta.dataset == "uso_do_solo"
        assert meta.contract_version == "1.0"
        assert "mapbiomas" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_cobertura_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch(tipo="cobertura")


class TestUsodoSoloValidation:
    @pytest.mark.asyncio
    async def test_invalid_tipo(self):
        dataset = UsodoSoloDataset()
        with pytest.raises(ValueError, match="tipo deve ser"):
            await dataset.fetch(tipo="invalido")


class TestUsodoSoloContract:
    @pytest.mark.asyncio
    async def test_contract_dispatch(self):
        dataset = UsodoSoloDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_cobertura_df())

        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch(tipo="cobertura")
            mock_has.assert_called_with("mapbiomas_cobertura")
            mock_validate.assert_called_once()

        dataset.info.sources[0].fetch_fn = make_source(_make_transicao_df())

        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch(tipo="transicao")
            mock_has.assert_called_with("mapbiomas_transicao")
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_contract_skipped_for_municipal(self):
        dataset = UsodoSoloDataset()
        df_municipal = _make_cobertura_df()
        df_municipal["municipio"] = "Cuiabá"
        dataset.info.sources[0].fetch_fn = make_source(df_municipal)

        with patch("agrobr.contracts.validate_dataset") as mock_validate:
            await dataset.fetch(tipo="cobertura", nivel="municipio")
            mock_validate.assert_not_called()


class TestUsodoSoloInfo:
    def test_sources(self):
        assert len(USO_DO_SOLO_INFO.sources) == 1
        assert USO_DO_SOLO_INFO.sources[0].name == "mapbiomas"

    def test_products_empty(self):
        assert USO_DO_SOLO_INFO.products == []

    def test_license(self):
        assert USO_DO_SOLO_INFO.license == "livre"


class TestUsodoSoloFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_mapbiomas_cobertura(self):
        df = _make_cobertura_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.mapbiomas.cobertura", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.uso_do_solo import _fetch_mapbiomas

            await _fetch_mapbiomas("soja", tipo="cobertura", bioma="Cerrado", estado="GO", ano=2020)
        mock_fn.assert_called_once_with(
            bioma="Cerrado",
            estado="GO",
            ano=2020,
            classe_id=None,
            nivel="estado",
            municipio=None,
            return_meta=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_mapbiomas_transicao(self):
        df = _make_transicao_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.mapbiomas.transicao", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.uso_do_solo import _fetch_mapbiomas

            await _fetch_mapbiomas("soja", tipo="transicao", bioma="Amazonia", estado="PA")
        mock_fn.assert_called_once_with(
            bioma="Amazonia",
            estado="PA",
            periodo=None,
            classe_de_id=None,
            classe_para_id=None,
            return_meta=True,
        )
