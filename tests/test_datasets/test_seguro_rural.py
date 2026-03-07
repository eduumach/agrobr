from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.seguro_rural import SEGURO_RURAL_INFO, SeguroRuralDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_apolices_df():
    return pd.DataFrame(
        {
            "nr_apolice": ["AP001"],
            "ano_apolice": [2023],
            "uf": ["MT"],
            "municipio": ["Sorriso"],
            "cd_ibge": ["5107925"],
            "cultura": ["SOJA"],
            "classificacao": ["Grão"],
            "area_total": [100.0],
            "valor_premio": [5000.0],
            "valor_subvencao": [2000.0],
            "valor_limite_garantia": [50000.0],
            "valor_indenizacao": [0.0],
            "evento": [None],
            "produtividade_estimada": [3500.0],
            "produtividade_segurada": [2800.0],
            "nivel_cobertura": [0.8],
            "taxa": [0.05],
            "seguradora": ["MAPFRE"],
        }
    )


def _mock_sinistros_df():
    return pd.DataFrame(
        {
            "nr_apolice": ["AP002"],
            "ano_apolice": [2023],
            "uf": ["RS"],
            "municipio": ["Cruz Alta"],
            "cd_ibge": ["4306106"],
            "cultura": ["SOJA"],
            "classificacao": ["Grão"],
            "evento": ["SECA"],
            "area_total": [50.0],
            "valor_indenizacao": [25000.0],
            "valor_premio": [3000.0],
            "valor_subvencao": [1200.0],
            "valor_limite_garantia": [30000.0],
            "produtividade_estimada": [3200.0],
            "produtividade_segurada": [2560.0],
            "nivel_cobertura": [0.8],
            "seguradora": ["ALIANÇA"],
        }
    )


class TestSeguroRuralFetch:
    @pytest.mark.asyncio
    async def test_fetch_apolices_default(self):
        dataset = SeguroRuralDataset()
        mock_fn = make_source(_mock_apolices_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        df = await dataset.fetch()

        assert len(df) == 1
        assert "nr_apolice" in df.columns
        _, kwargs = mock_fn.call_args
        assert kwargs["tipo"] == "apolices"

    @pytest.mark.asyncio
    async def test_fetch_sinistros(self):
        dataset = SeguroRuralDataset()
        mock_fn = make_source(_mock_sinistros_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        df = await dataset.fetch(tipo="sinistros")

        assert len(df) == 1
        _, kwargs = mock_fn.call_args
        assert kwargs["tipo"] == "sinistros"

    @pytest.mark.asyncio
    async def test_invalid_tipo(self):
        dataset = SeguroRuralDataset()

        with pytest.raises(ValueError, match="tipo deve ser"):
            await dataset.fetch(tipo="outro")

    @pytest.mark.asyncio
    async def test_produto_maps_to_cultura(self):
        dataset = SeguroRuralDataset()
        mock_fn = make_source(_mock_apolices_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("soja")

        args, _ = mock_fn.call_args
        assert args[0] == "soja"

    @pytest.mark.asyncio
    async def test_meta_apolices(self):
        dataset = SeguroRuralDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_apolices_df())

        df, meta = await dataset.fetch(return_meta=True)

        assert meta.dataset == "seguro_rural"
        assert meta.contract_version == "1.0"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_meta_sinistros(self):
        dataset = SeguroRuralDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_sinistros_df())

        df, meta = await dataset.fetch(tipo="sinistros", return_meta=True)

        assert meta.dataset == "seguro_rural"
        assert meta.selected_source == "mapa_psr"

    @pytest.mark.asyncio
    async def test_contract_validation_per_tipo(self):
        dataset = SeguroRuralDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_apolices_df())

        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch(tipo="apolices")
            mock_has.assert_called_with("mapa_psr_apolices")
            mock_validate.assert_called_once()

        dataset.info.sources[0].fetch_fn = make_source(_mock_sinistros_df())

        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch(tipo="sinistros")
            mock_has.assert_called_with("mapa_psr_sinistros")
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_evento_passthrough(self):
        dataset = SeguroRuralDataset()
        mock_fn = make_source(_mock_apolices_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch(tipo="apolices", evento="SECA")

        _, kwargs = mock_fn.call_args
        assert kwargs["evento"] == "SECA"
        assert kwargs["tipo"] == "apolices"

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = SeguroRuralDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch()


class TestSeguroRuralInfo:
    def test_products_empty(self):
        assert SEGURO_RURAL_INFO.products == []

    def test_license_livre(self):
        assert SEGURO_RURAL_INFO.license == "livre"
