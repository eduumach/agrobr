from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.futuros_agricolas import (
    FUTUROS_AGRICOLAS_INFO,
    FuturosAgricolasDataset,
)
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_ajustes_df():
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2025-03-05"]),
            "ticker": ["BGI"],
            "descricao": ["BOI GORDO"],
            "vencimento_codigo": ["G25"],
            "vencimento_mes": [2],
            "vencimento_ano": [2025],
            "ajuste_anterior": [310.0],
            "ajuste_atual": [312.5],
            "variacao": [2.5],
            "ajuste_por_contrato": [312.5],
            "unidade": ["BRL/@"],
        }
    )


def _mock_posicoes_df():
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2025-03-05"]),
            "ticker": ["BGI"],
            "descricao": ["BOI GORDO"],
            "ticker_completo": ["BGIG25"],
            "vencimento_codigo": ["G25"],
            "vencimento_mes": [2],
            "vencimento_ano": [2025],
            "tipo": ["futuro"],
            "posicoes_abertas": [50000],
            "variacao_posicoes": [1200],
            "unidade": ["BRL/@"],
        }
    )


class TestFuturosInfo:
    def test_products(self):
        assert len(FUTUROS_AGRICOLAS_INFO.products) == 7
        assert "boi" in FUTUROS_AGRICOLAS_INFO.products
        assert "soja_fob" in FUTUROS_AGRICOLAS_INFO.products

    def test_license_zona_cinza(self):
        assert FUTUROS_AGRICOLAS_INFO.license == "zona_cinza"


class TestFuturosFetch:
    @pytest.mark.asyncio
    async def test_fetch_ajustes_default(self):
        dataset = FuturosAgricolasDataset()
        mock_fn = make_source(_mock_ajustes_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        df = await dataset.fetch("boi", data="2025-03-05")

        assert len(df) == 1
        assert "ajuste_atual" in df.columns
        _, kwargs = mock_fn.call_args
        assert kwargs["tipo"] == "ajustes"

    @pytest.mark.asyncio
    async def test_fetch_historico(self):
        dataset = FuturosAgricolasDataset()
        mock_fn = make_source(_mock_ajustes_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        df = await dataset.fetch("boi", tipo="historico", inicio="2025-01-01", fim="2025-03-05")

        assert len(df) == 1
        _, kwargs = mock_fn.call_args
        assert kwargs["tipo"] == "historico"
        assert kwargs["inicio"] == "2025-01-01"
        assert kwargs["fim"] == "2025-03-05"

    @pytest.mark.asyncio
    async def test_fetch_posicoes(self):
        dataset = FuturosAgricolasDataset()
        mock_fn = make_source(_mock_posicoes_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        df = await dataset.fetch("boi", tipo="posicoes", data="2025-03-05")

        assert len(df) == 1
        assert "posicoes_abertas" in df.columns
        _, kwargs = mock_fn.call_args
        assert kwargs["tipo"] == "posicoes"

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = FuturosAgricolasDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_ajustes_df())

        df, meta = await dataset.fetch("boi", data="2025-03-05", return_meta=True)

        assert meta.dataset == "futuros_agricolas"
        assert meta.contract_version == "1.0"
        assert "b3" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = FuturosAgricolasDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("boi", data="2025-03-05")


class TestFuturosValidation:
    @pytest.mark.asyncio
    async def test_invalid_tipo(self):
        dataset = FuturosAgricolasDataset()

        with pytest.raises(ValueError, match="tipo deve ser"):
            await dataset.fetch("boi", tipo="outro")

    @pytest.mark.asyncio
    async def test_historico_requires_produto(self):
        dataset = FuturosAgricolasDataset()

        with pytest.raises(ValueError, match="produto é obrigatório"):
            await dataset.fetch(tipo="historico", inicio="2025-01-01", fim="2025-03-05")

    @pytest.mark.asyncio
    async def test_historico_requires_inicio_fim(self):
        dataset = FuturosAgricolasDataset()

        with pytest.raises(ValueError, match="inicio e fim"):
            await dataset.fetch("boi", tipo="historico")

    @pytest.mark.asyncio
    async def test_invalid_produto(self):
        dataset = FuturosAgricolasDataset()

        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("banana", data="2025-03-05")

    @pytest.mark.asyncio
    async def test_soja_fob_posicoes_raises(self):
        dataset = FuturosAgricolasDataset()

        with pytest.raises(ValueError, match="soja_fob"):
            await dataset.fetch("soja_fob", tipo="posicoes", data="2025-03-05")


class TestFuturosContract:
    @pytest.mark.asyncio
    async def test_contract_dispatch_ajustes_vs_posicoes(self):
        dataset = FuturosAgricolasDataset()

        dataset.info.sources[0].fetch_fn = make_source(_mock_ajustes_df())
        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch("boi", data="2025-03-05")
            mock_has.assert_called_with("ajuste_diario")
            mock_validate.assert_called_once()

        dataset.info.sources[0].fetch_fn = make_source(_mock_posicoes_df())
        with (
            patch("agrobr.contracts.has_contract", return_value=True) as mock_has,
            patch("agrobr.contracts.validate_dataset") as mock_validate,
        ):
            await dataset.fetch("boi", tipo="posicoes", data="2025-03-05")
            mock_has.assert_called_with("posicoes_abertas")
            mock_validate.assert_called_once()
