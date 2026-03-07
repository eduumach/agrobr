from unittest.mock import patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.desmatamento import (
    DESMATAMENTO_INFO,
    DesmatamentoDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _make_prodes_df(**overrides):
    row = {
        "ano": 2023,
        "uf": "MT",
        "classe": "DESFLORESTAMENTO",
        "area_km2": 1234.56,
        "satelite": "LANDSAT",
        "sensor": "OLI",
        "bioma": "Cerrado",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _make_deter_df(**overrides):
    row = {
        "data": pd.Timestamp("2024-06-15"),
        "classe": "DESMATAMENTO_CR",
        "uf": "PA",
        "municipio": "Altamira",
        "municipio_id": 1500602,
        "area_km2": 5.42,
        "satelite": "CBERS-4A",
        "sensor": "WFI",
        "bioma": "Amazônia",
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestDesmatamentoFetch:
    @pytest.mark.asyncio
    async def test_fetch_prodes_returns_df(self):
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_prodes_df())
        df = await dataset.fetch("Cerrado", tipo="prodes")

        assert len(df) == 1
        assert "ano" in df.columns
        assert "area_km2" in df.columns
        assert df.iloc[0]["area_km2"] == 1234.56

    @pytest.mark.asyncio
    async def test_fetch_deter_returns_df(self):
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_deter_df())
        df = await dataset.fetch("Amazônia", tipo="deter")

        assert len(df) == 1
        assert "data" in df.columns
        assert "classe" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_prodes_params_passthrough(self):
        mock_fn = make_source(_make_prodes_df())
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch("Cerrado", tipo="prodes", ano=2022, uf="MT")

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["ano"] == 2022
        assert call_kwargs["uf"] == "MT"
        assert call_kwargs["tipo"] == "prodes"

    @pytest.mark.asyncio
    async def test_fetch_deter_params_passthrough(self):
        mock_fn = make_source(_make_deter_df())
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch(
            "Amazônia",
            tipo="deter",
            data_inicio="2024-01-01",
            data_fim="2024-06-30",
            classe="DESMATAMENTO_CR",
        )

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["data_inicio"] == "2024-01-01"
        assert call_kwargs["data_fim"] == "2024-06-30"
        assert call_kwargs["classe"] == "DESMATAMENTO_CR"

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_prodes_df())
        df, meta = await dataset.fetch("Cerrado", return_meta=True)

        assert meta.dataset == "desmatamento"
        assert meta.contract_version == "1.0"
        assert "inpe" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = make_source(
            _make_prodes_df(), raises=httpx.ConnectError("connection failed")
        )
        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("Cerrado")


class TestDesmatamentoValidation:
    @pytest.mark.asyncio
    async def test_invalid_tipo(self):
        dataset = DesmatamentoDataset()
        with pytest.raises(ValueError, match="tipo deve ser"):
            await dataset.fetch("Cerrado", tipo="invalido")

    @pytest.mark.asyncio
    async def test_deter_invalid_bioma(self):
        dataset = DesmatamentoDataset()
        with pytest.raises(ValueError, match="DETER só está disponível"):
            await dataset.fetch("Caatinga", tipo="deter")

    @pytest.mark.asyncio
    async def test_bioma_normalization(self):
        mock_fn = make_source(_make_prodes_df())
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = mock_fn
        await dataset.fetch("cerrado", tipo="prodes")

        call_args = mock_fn.call_args[0]
        assert call_args[0] == "Cerrado"


class TestDesmatamentoContract:
    @pytest.mark.asyncio
    async def test_contract_dispatch(self):
        dataset = DesmatamentoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_make_prodes_df())

        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch("Cerrado", tipo="prodes")
            mock_has.assert_called_with("desmatamento_prodes")
            mock_validate.assert_called_once()

        dataset.info.sources[0].fetch_fn = make_source(_make_deter_df())

        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch("Amazônia", tipo="deter")
            mock_has.assert_called_with("desmatamento_deter")
            mock_validate.assert_called_once()


class TestDesmatamentoInfo:
    def test_sources(self):
        assert len(DESMATAMENTO_INFO.sources) == 1
        assert DESMATAMENTO_INFO.sources[0].name == "inpe"

    def test_products(self):
        assert "Cerrado" in DESMATAMENTO_INFO.products
        assert "Amazônia" in DESMATAMENTO_INFO.products
        assert len(DESMATAMENTO_INFO.products) == 6

    def test_license(self):
        assert DESMATAMENTO_INFO.license == "livre"
