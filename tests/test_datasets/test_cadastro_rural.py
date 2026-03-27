"""Testes para o dataset cadastro_rural (SICAR)."""

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.datasets.cadastro_rural import CadastroRuralDataset

from .conftest import mock_source_meta


def _mock_df():
    return pd.DataFrame(
        [
            {
                "cod_imovel": "DF-0100001-ABC",
                "status": "AT",
                "data_criacao": pd.Timestamp("2020-01-15"),
                "data_atualizacao": pd.Timestamp("2023-06-10"),
                "area_ha": 150.5,
                "condicao": "",
                "uf": "DF",
                "municipio": "BRASILIA",
                "cod_municipio_ibge": 5300108,
                "modulos_fiscais": 3.0,
                "tipo": "IRU",
            },
            {
                "cod_imovel": "DF-0100002-DEF",
                "status": "PE",
                "data_criacao": pd.Timestamp("2021-03-20"),
                "data_atualizacao": pd.NaT,
                "area_ha": 85.0,
                "condicao": "",
                "uf": "DF",
                "municipio": "BRASILIA",
                "cod_municipio_ibge": 5300108,
                "modulos_fiscais": 1.7,
                "tipo": "IRU",
            },
        ]
    )


def _mock_meta():
    meta = AsyncMock()
    meta.source_url = "https://geoserver.car.gov.br/geoserver/sicar/wfs"
    meta.fetched_at = None
    meta.parser_version = 1
    return meta


class TestCadastroRuralDataset:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = CadastroRuralDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(return_value=(_mock_df(), _mock_meta()))

        df = await dataset.fetch("DF")

        assert len(df) == 2
        assert "cod_imovel" in df.columns
        assert "area_ha" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = CadastroRuralDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(return_value=(_mock_df(), _mock_meta()))

        df, meta = await dataset.fetch("DF", return_meta=True)

        assert meta.dataset == "cadastro_rural"
        assert meta.contract_version == "1.0"
        assert "sicar" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_passes_filters(self):
        mock_fn = AsyncMock(return_value=(_mock_df(), _mock_meta()))
        dataset = CadastroRuralDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch(
            "MT",
            municipio="Sorriso",
            status="AT",
            tipo="IRU",
            area_min=100.0,
        )

        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs["municipio"] == "Sorriso"
        assert call_kwargs["status"] == "AT"
        assert call_kwargs["tipo"] == "IRU"
        assert call_kwargs["area_min"] == 100.0

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        dataset = CadastroRuralDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("XX")

    @pytest.mark.asyncio
    async def test_products_are_27_ufs(self):
        dataset = CadastroRuralDataset()
        assert len(dataset.info.products) == 27
        assert "MT" in dataset.info.products
        assert "DF" in dataset.info.products
        assert "SP" in dataset.info.products

    @pytest.mark.asyncio
    async def test_dataset_name(self):
        dataset = CadastroRuralDataset()
        assert dataset.info.name == "cadastro_rural"

    @pytest.mark.asyncio
    async def test_source_is_sicar(self):
        dataset = CadastroRuralDataset()
        assert dataset.info.sources[0].name == "sicar"
        assert dataset.info.sources[0].priority == 1


class TestCadastroRuralNormalize:
    @pytest.mark.asyncio
    async def test_return_meta_snapshot(self):
        from agrobr.datasets.deterministic import deterministic

        dataset = CadastroRuralDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(return_value=(_mock_df(), _mock_meta()))

        async with deterministic("2024-01-15"):
            df, meta = await dataset.fetch("DF", return_meta=True)

        assert meta.snapshot == "2024-01-15"

    @pytest.mark.asyncio
    async def test_snapshot_sets_criado_apos(self):
        from agrobr.datasets.deterministic import deterministic

        mock_fn = AsyncMock(return_value=(_mock_df(), _mock_meta()))
        dataset = CadastroRuralDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("DF")

        _, kwargs = mock_fn.call_args
        assert kwargs["criado_apos"] == "2024-06-15"

    @pytest.mark.asyncio
    async def test_snapshot_does_not_override_explicit_criado_apos(self):
        from agrobr.datasets.deterministic import deterministic

        mock_fn = AsyncMock(return_value=(_mock_df(), _mock_meta()))
        dataset = CadastroRuralDataset()
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2024-06-15"):
            await dataset.fetch("DF", criado_apos="2023-01-01")

        _, kwargs = mock_fn.call_args
        assert kwargs["criado_apos"] == "2023-01-01"


class TestCadastroRuralPublicAPI:
    @pytest.mark.asyncio
    async def test_public_function_delegates(self):
        from agrobr.datasets.cadastro_rural import cadastro_rural

        with patch.object(CadastroRuralDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = _mock_df()
            await cadastro_rural("MT", municipio="Sorriso", status="AT")

            mock_fetch.assert_called_once_with(
                "MT",
                municipio="Sorriso",
                status="AT",
                tipo=None,
                area_min=None,
                area_max=None,
                criado_apos=None,
                return_meta=False,
            )


class TestCadastroRuralRegistered:
    def test_registered_in_registry(self):
        from agrobr.datasets.registry import list_datasets

        assert "cadastro_rural" in list_datasets()

    def test_contract_registered(self):
        from agrobr.contracts import has_contract

        assert has_contract("cadastro_rural")

    def test_contract_same_as_sicar_imoveis(self):
        from agrobr.contracts import get_contract

        c1 = get_contract("cadastro_rural")
        c2 = get_contract("sicar_imoveis")
        assert c1 is c2


class TestCadastroRuralFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_sicar_forwards_all_params(self):
        df = _mock_df()
        meta = mock_source_meta()
        with patch(
            "agrobr.alt.sicar.imoveis", new_callable=AsyncMock, return_value=(df, meta)
        ) as mock_fn:
            from agrobr.datasets.cadastro_rural import _fetch_sicar

            await _fetch_sicar(
                "PR",
                municipio="Londrina",
                status="ativo",
                tipo="rural",
                area_min=10.0,
                area_max=1000.0,
                criado_apos="2024-01-01",
            )
        mock_fn.assert_called_once_with(
            "PR",
            municipio="Londrina",
            status="ativo",
            tipo="rural",
            area_min=10.0,
            area_max=1000.0,
            criado_apos="2024-01-01",
            return_meta=True,
        )
