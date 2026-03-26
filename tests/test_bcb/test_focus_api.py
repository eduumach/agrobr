from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.bcb import focus_api

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "bcb"
FOCUS_SAMPLE_URL = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"


def _load_golden_focus() -> list[dict]:
    with open(GOLDEN_DIR / "focus_sample.json", encoding="utf-8") as f:
        return json.load(f)["value"]


class TestFocusBasic:
    @pytest.mark.asyncio
    async def test_returns_dataframe_with_correct_columns(self):
        with patch.object(
            focus_api.focus_client,
            "fetch_focus",
            new_callable=AsyncMock,
            return_value=(_load_golden_focus(), FOCUS_SAMPLE_URL),
        ):
            df = await focus_api.focus()

        assert isinstance(df, pd.DataFrame)
        expected_cols = [
            "indicador",
            "data",
            "data_referencia",
            "media",
            "mediana",
            "desvio_padrao",
            "minimo",
            "maximo",
            "numero_respondentes",
            "base_calculo",
        ]
        assert list(df.columns) == expected_cols
        assert len(df) == 5


class TestFocusColumnRenaming:
    @pytest.mark.asyncio
    async def test_columns_renamed_from_api(self):
        with patch.object(
            focus_api.focus_client,
            "fetch_focus",
            new_callable=AsyncMock,
            return_value=(_load_golden_focus(), FOCUS_SAMPLE_URL),
        ):
            df = await focus_api.focus()

        assert "Indicador" not in df.columns
        assert "indicador" in df.columns
        assert "DesvioPadrao" not in df.columns
        assert "desvio_padrao" in df.columns
        assert "numeroRespondentes" not in df.columns
        assert "numero_respondentes" in df.columns

    @pytest.mark.asyncio
    async def test_values_preserved(self):
        with patch.object(
            focus_api.focus_client,
            "fetch_focus",
            new_callable=AsyncMock,
            return_value=(_load_golden_focus(), FOCUS_SAMPLE_URL),
        ):
            df = await focus_api.focus()

        row = df.iloc[0]
        assert row["indicador"] == "PIB Agropecuário"
        assert row["media"] == pytest.approx(3.5)
        assert row["mediana"] == pytest.approx(3.48)
        assert row["numero_respondentes"] == 85


class TestFocusReturnMeta:
    @pytest.mark.asyncio
    async def test_return_meta_tuple(self):
        with patch.object(
            focus_api.focus_client,
            "fetch_focus",
            new_callable=AsyncMock,
            return_value=(_load_golden_focus(), FOCUS_SAMPLE_URL),
        ):
            result = await focus_api.focus(return_meta=True)

        assert isinstance(result, tuple)
        df, meta = result
        assert isinstance(df, pd.DataFrame)
        assert meta.source == "bcb_focus"
        assert meta.source_method == "httpx"
        assert meta.records_count == len(df)
        assert meta.attempted_sources == ["bcb_focus"]
        assert meta.selected_source == "bcb_focus"


class TestFocusAsPolars:
    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        with patch.object(
            focus_api.focus_client,
            "fetch_focus",
            new_callable=AsyncMock,
            return_value=(_load_golden_focus(), FOCUS_SAMPLE_URL),
        ):
            result = await focus_api.focus(as_polars=True)

        assert isinstance(result, pl.DataFrame)


class TestFocusDateParsing:
    @pytest.mark.asyncio
    async def test_data_parsed_as_datetime(self):
        with patch.object(
            focus_api.focus_client,
            "fetch_focus",
            new_callable=AsyncMock,
            return_value=(_load_golden_focus(), FOCUS_SAMPLE_URL),
        ):
            df = await focus_api.focus()

        assert pd.api.types.is_datetime64_any_dtype(df["data"])
        first_date = df["data"].iloc[0]
        assert first_date.year == 2026
        assert first_date.month == 3
        assert first_date.day == 21


class TestFocusEmptyRecords:
    @pytest.mark.asyncio
    async def test_empty_records_returns_empty_dataframe(self):
        with patch.object(
            focus_api.focus_client,
            "fetch_focus",
            new_callable=AsyncMock,
            return_value=([], FOCUS_SAMPLE_URL),
        ):
            df = await focus_api.focus()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "indicador" in df.columns
