from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.cftc import api as cftc_api
from agrobr.cftc.models import COLUNAS_SAIDA

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "cftc"
COT_URL = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"


def _load_golden() -> list[dict[str, str]]:
    with open(GOLDEN_DIR / "cot_sample.json", encoding="utf-8") as f:
        return json.load(f)


def _patch_fetch():
    return patch.object(
        cftc_api.client,
        "fetch_cot",
        new_callable=AsyncMock,
        return_value=(_load_golden(), COT_URL),
    )


class TestCotBasic:
    @pytest.mark.asyncio
    async def test_retorna_dataframe_com_colunas(self):
        with _patch_fetch():
            df = await cftc_api.cot()

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == COLUNAS_SAIDA
        assert len(df) == 6

    @pytest.mark.asyncio
    async def test_commodity_resolve_codigos(self):
        with _patch_fetch() as mock_fetch:
            await cftc_api.cot("soja")

        mock_fetch.assert_called_once_with(["005602"], start=None, end=None, combined=False)

    @pytest.mark.asyncio
    async def test_none_busca_todos_os_contratos(self):
        with _patch_fetch() as mock_fetch:
            await cftc_api.cot()

        codes = mock_fetch.call_args[0][0]
        assert len(codes) == 12

    @pytest.mark.asyncio
    async def test_commodity_invalida_raises(self):
        with pytest.raises(ValueError, match="sem contrato CFTC"):
            await cftc_api.cot("commodity_inexistente")

    @pytest.mark.asyncio
    async def test_start_end_combined_repassados(self):
        with _patch_fetch() as mock_fetch:
            await cftc_api.cot("milho", start="2026-01-01", end="2026-06-01", combined=True)

        mock_fetch.assert_called_once_with(
            ["002602"], start="2026-01-01", end="2026-06-01", combined=True
        )


class TestCotReturnMeta:
    @pytest.mark.asyncio
    async def test_return_meta_tuple(self):
        with _patch_fetch():
            result = await cftc_api.cot("soja", return_meta=True)

        assert isinstance(result, tuple)
        df, meta = result
        assert isinstance(df, pd.DataFrame)
        assert meta.source == "cftc"
        assert meta.source_method == "httpx"
        assert meta.source_url == COT_URL
        assert meta.records_count == len(df)
        assert meta.attempted_sources == ["cftc"]
        assert meta.selected_source == "cftc"


class TestCotAsPolars:
    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        with _patch_fetch():
            result = await cftc_api.cot("soja", as_polars=True)

        assert isinstance(result, pl.DataFrame)
