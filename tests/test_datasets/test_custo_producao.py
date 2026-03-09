"""Testes específicos para o dataset custo_producao (fetch com mock)."""

from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest

from agrobr.datasets.custo_producao import (
    CUSTO_PRODUCAO_INFO,
    CustoProducaoDataset,
    custo_producao,
)
from agrobr.datasets.deterministic import deterministic
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source, mock_source_meta


def _mock_df():
    return pd.DataFrame(
        [
            {
                "cultura": "soja",
                "uf": "MT",
                "safra": "2024/25",
                "tecnologia": "alta",
                "categoria": "Sementes",
                "item": "Semente",
                "unidade": "kg/ha",
                "quantidade_ha": 50.0,
                "preco_unitario": 5.50,
                "valor_ha": 275.0,
                "participacao_pct": 8.2,
            },
        ]
    )


class TestCustoProducaoInfo:
    def test_single_source_conab(self):
        assert len(CUSTO_PRODUCAO_INFO.sources) == 1
        assert CUSTO_PRODUCAO_INFO.sources[0].name == "conab"

    def test_license_livre(self):
        assert CUSTO_PRODUCAO_INFO.license == "livre"


class TestCustoProducaoFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = CustoProducaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())
        df = await dataset.fetch("soja", safra="2024/25")

        assert len(df) == 1
        assert "valor_ha" in df.columns
        assert df.iloc[0]["valor_ha"] == 275.0

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = CustoProducaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())
        df, meta = await dataset.fetch("soja", safra="2024/25", return_meta=True)

        assert meta.dataset == "custo_producao"
        assert meta.contract_version == "1.0"
        assert "conab" in meta.attempted_sources
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = CustoProducaoDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("banana")

    @pytest.mark.asyncio
    async def test_source_failure(self):
        dataset = CustoProducaoDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("down"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")

    @pytest.mark.asyncio
    async def test_snapshot_generates_safra(self):
        dataset = CustoProducaoDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2025-03-15"):
            await dataset.fetch("soja")

        _, kwargs = mock_fn.call_args
        assert kwargs["safra"] == "2024/25"

    @pytest.mark.asyncio
    async def test_snapshot_does_not_override_explicit_safra(self):
        dataset = CustoProducaoDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        async with deterministic("2025-03-15"):
            await dataset.fetch("soja", safra="2023/24")

        _, kwargs = mock_fn.call_args
        assert kwargs["safra"] == "2023/24"

    @pytest.mark.asyncio
    async def test_forwards_all_kwargs(self):
        dataset = CustoProducaoDataset()
        mock_fn = make_source(_mock_df())
        dataset.info.sources[0].fetch_fn = mock_fn

        await dataset.fetch("soja", uf="MT", safra="2024/25", tecnologia="media")

        _, kwargs = mock_fn.call_args
        assert kwargs["uf"] == "MT"
        assert kwargs["safra"] == "2024/25"
        assert kwargs["tecnologia"] == "media"


class TestCustoProducaoNormalize:
    @pytest.mark.asyncio
    async def test_normalize_adds_cultura(self):
        df = _mock_df().drop(columns=["cultura"])
        dataset = CustoProducaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        result = await dataset.fetch("soja")

        assert result["cultura"].iloc[0] == "soja"

    @pytest.mark.asyncio
    async def test_normalize_keeps_existing_cultura(self):
        dataset = CustoProducaoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        result = await dataset.fetch("soja")

        assert result["cultura"].iloc[0] == "soja"


class TestCustoProducaoPublicAPI:
    @pytest.mark.asyncio
    async def test_public_function_delegates(self):
        with patch.object(CustoProducaoDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = _mock_df()
            await custo_producao("soja", uf="MT", safra="2024/25")

            mock_fetch.assert_called_once_with(
                "soja",
                uf="MT",
                safra="2024/25",
                tecnologia="alta",
                return_meta=False,
            )

    @pytest.mark.asyncio
    async def test_public_function_return_meta(self):
        with patch.object(CustoProducaoDataset, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (_mock_df(), mock_source_meta())
            result = await custo_producao("soja", return_meta=True)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], pd.DataFrame)
