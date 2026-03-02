from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest

from agrobr.datasets.producao_anual import PRODUCAO_ANUAL_INFO, ProducaoAnualDataset
from agrobr.exceptions import SourceUnavailableError

from .conftest import make_source


def _mock_df():
    return pd.DataFrame(
        [
            {
                "ano": 2023,
                "localidade": "Mato Grosso",
                "produto": "soja",
                "area_plantada": 12000000.0,
                "producao": 43000000.0,
                "rendimento": 3583.0,
                "fonte": "ibge_pam",
            },
        ]
    )


class TestProducaoAnualSpecific:
    def test_info_ibge_pam_priority(self):
        ibge_source = next(s for s in PRODUCAO_ANUAL_INFO.sources if s.name == "ibge_pam")
        conab_source = next(s for s in PRODUCAO_ANUAL_INFO.sources if s.name == "conab")
        assert ibge_source.priority < conab_source.priority


class TestProducaoAnualFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self):
        dataset = ProducaoAnualDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df = await dataset.fetch("soja")

        assert len(df) == 1
        assert "area_plantada" in df.columns
        assert "rendimento" in df.columns

    @pytest.mark.asyncio
    async def test_fetch_return_meta(self):
        dataset = ProducaoAnualDataset()
        dataset.info.sources[0].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("soja", return_meta=True)

        assert meta.dataset == "producao_anual"
        assert meta.contract_version == "1.0"
        assert meta.attempted_sources == ["ibge_pam"]
        assert meta.selected_source == "ibge_pam"
        assert meta.records_count == len(df)

    @pytest.mark.asyncio
    async def test_fetch_invalid_produto(self):
        dataset = ProducaoAnualDataset()
        with pytest.raises(ValueError, match="não suportado"):
            await dataset.fetch("aveia")


class TestProducaoAnualNormalize:
    @pytest.mark.asyncio
    async def test_normalize_adds_produto_fonte(self):
        df = _mock_df().drop(columns=["produto", "fonte"])
        dataset = ProducaoAnualDataset()
        dataset.info.sources[0].fetch_fn = make_source(df)

        result = await dataset.fetch("soja")

        assert result["produto"].iloc[0] == "soja"
        assert result["fonte"].iloc[0] == "ibge_pam"


class TestProducaoAnualFallback:
    @pytest.mark.asyncio
    async def test_ibge_fails_falls_back_to_conab(self):
        dataset = ProducaoAnualDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))
        dataset.info.sources[1].fetch_fn = make_source(_mock_df())

        df, meta = await dataset.fetch("soja", return_meta=True)

        assert len(df) == 1
        assert meta.attempted_sources == ["ibge_pam", "conab"]
        assert meta.selected_source == "conab"

    @pytest.mark.asyncio
    async def test_all_sources_fail(self):
        dataset = ProducaoAnualDataset()
        dataset.info.sources[0].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))
        dataset.info.sources[1].fetch_fn = AsyncMock(side_effect=httpx.ConnectError("test"))

        with pytest.raises(SourceUnavailableError):
            await dataset.fetch("soja")
