from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agrobr.bcb import ptax_api

GOLDEN = Path(__file__).resolve().parent.parent / "golden_data" / "bcb" / "ptax_sample.json"
SAMPLE = json.loads(GOLDEN.read_text(encoding="utf-8"))
SAMPLE_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo"


def _mock_fetch():
    return AsyncMock(return_value=(SAMPLE["value"], SAMPLE_URL))


class TestPtaxBasic:
    @pytest.mark.asyncio
    async def test_returns_dataframe_with_correct_columns(self):
        with patch.object(ptax_api.ptax_client, "fetch_ptax", _mock_fetch()):
            df = await ptax_api.ptax(data_inicial="02/01/2026", data_final="08/01/2026")

        assert len(df) == 5
        assert "cotacao_compra" in df.columns
        assert "cotacao_venda" in df.columns
        assert "data_hora" in df.columns
        assert "data" in df.columns
        assert "cotacaoCompra" not in df.columns

    @pytest.mark.asyncio
    async def test_cotacao_values(self):
        with patch.object(ptax_api.ptax_client, "fetch_ptax", _mock_fetch()):
            df = await ptax_api.ptax(data_inicial="02/01/2026", data_final="08/01/2026")

        assert df.iloc[0]["cotacao_compra"] == pytest.approx(6.0513)
        assert df.iloc[0]["cotacao_venda"] == pytest.approx(6.0519)

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty_df(self):
        with patch.object(
            ptax_api.ptax_client,
            "fetch_ptax",
            AsyncMock(return_value=([], SAMPLE_URL)),
        ):
            df = await ptax_api.ptax(data="01/01/2026")

        assert len(df) == 0


class TestPtaxMeta:
    @pytest.mark.asyncio
    async def test_return_meta(self):
        with patch.object(ptax_api.ptax_client, "fetch_ptax", _mock_fetch()):
            df, meta = await ptax_api.ptax(
                data_inicial="02/01/2026", data_final="08/01/2026", return_meta=True
            )

        assert meta.source == "bcb_ptax"
        assert meta.attempted_sources == ["bcb_ptax"]
        assert meta.selected_source == "bcb_ptax"
        assert meta.source_method == "httpx"
        assert meta.records_count == 5
        assert meta.fetch_timestamp is not None

    @pytest.mark.asyncio
    async def test_schema_version(self):
        with patch.object(ptax_api.ptax_client, "fetch_ptax", _mock_fetch()):
            _, meta = await ptax_api.ptax(
                data_inicial="02/01/2026", data_final="08/01/2026", return_meta=True
            )

        assert meta.schema_version == "1.0"


class TestPtaxPolars:
    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        with patch.object(ptax_api.ptax_client, "fetch_ptax", _mock_fetch()):
            result = await ptax_api.ptax(
                data_inicial="02/01/2026", data_final="08/01/2026", as_polars=True
            )

        assert isinstance(result, pl.DataFrame)
        assert "cotacao_compra" in result.columns


class TestPtaxDateParsing:
    @pytest.mark.asyncio
    async def test_data_hora_is_datetime(self):
        with patch.object(ptax_api.ptax_client, "fetch_ptax", _mock_fetch()):
            df = await ptax_api.ptax(data_inicial="02/01/2026", data_final="08/01/2026")

        import pandas as pd

        assert pd.api.types.is_datetime64_any_dtype(df["data_hora"])

    @pytest.mark.asyncio
    async def test_date_column_extracted(self):
        with patch.object(ptax_api.ptax_client, "fetch_ptax", _mock_fetch()):
            df = await ptax_api.ptax(data_inicial="02/01/2026", data_final="08/01/2026")

        from datetime import date

        assert df.iloc[0]["data"] == date(2026, 1, 2)
