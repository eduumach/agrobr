from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest

from agrobr.datasets.balanco import BalancoDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        [
            {
                "produto": "soja",
                "safra": "2023/24",
                "estoque_inicial": 1200.0,
                "producao": 15000.0,
                "importacao": 50.0,
                "suprimento": 16250.0,
                "consumo": 5300.0,
                "exportacao": 9700.0,
                "estoque_final": 1250.0,
            },
        ]
    )


class TestBalancoFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = BalancoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("soja")

        assert len(df) == 1
        assert "estoque_inicial" in df.columns
        assert "producao" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = BalancoDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.dataset == "balanco"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["conab"]
        assert meta.selected_source == "conab"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = BalancoDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestBalancoNormalize:
    @pytest.mark.asyncio
    async def test_normalize_adds_produto_fonte(self):
        df = _mock_df().drop(columns=["produto"])
        dataset = BalancoDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        result = await dataset.fetch("soja")

        assert result["produto"].iloc[0] == "soja"
        assert result["fonte"].iloc[0] == "conab"

    @pytest.mark.asyncio
    async def test_normalize_empty_df(self):
        df = _mock_df().iloc[:0].copy()
        df["fonte"] = pd.Series(dtype="str")
        dataset = BalancoDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        result = await dataset.fetch("soja")

        assert len(result) == 0


class TestBalancoSourceFail:
    @pytest.mark.asyncio
    async def test_source_fails_raises(self):
        dataset = BalancoDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")


class TestBalancoFetchFunctions:
    @pytest.mark.asyncio
    async def test_fetch_conab_forwards_params(self):
        from unittest.mock import patch

        df = _mock_df()
        with patch("agrobr.conab.balanco", new_callable=AsyncMock, return_value=df) as mock_fn:
            from agrobr.datasets.balanco import _fetch_conab

            result_df, result_meta = await _fetch_conab("soja", safra="2023/24")
        mock_fn.assert_called_once_with(produto="soja", safra="2023/24")
        assert len(result_df) == 1
        assert result_meta is not None

    @pytest.mark.asyncio
    async def test_fetch_conab_defaults(self):
        from unittest.mock import patch

        df = _mock_df()
        with patch("agrobr.conab.balanco", new_callable=AsyncMock, return_value=df) as mock_fn:
            from agrobr.datasets.balanco import _fetch_conab

            await _fetch_conab("milho")
        _, kwargs = mock_fn.call_args
        assert kwargs["safra"] is None
