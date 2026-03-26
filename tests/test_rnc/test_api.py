from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "golden_data" / "rnc"


def _registradas_bytes():
    return (GOLDEN_DIR / "registradas_sample.csv").read_bytes()


def _protegidas_bytes():
    return (GOLDEN_DIR / "protegidas_sample.csv").read_bytes()


@pytest.mark.asyncio
async def test_registradas_returns_dataframe():
    with patch("agrobr.rnc.client.fetch_registradas", new_callable=AsyncMock) as mock:
        mock.return_value = (_registradas_bytes(), "https://example.com")

        from agrobr.rnc import registradas

        df = await registradas()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 25
        assert "cultivar" in df.columns


@pytest.mark.asyncio
async def test_registradas_filter_cultivar():
    with patch("agrobr.rnc.client.fetch_registradas", new_callable=AsyncMock) as mock:
        mock.return_value = (_registradas_bytes(), "https://example.com")

        from agrobr.rnc import registradas

        df = await registradas(cultivar="Bonella")
        assert len(df) > 0
        assert all("Bonella" in v for v in df["cultivar"].values)


@pytest.mark.asyncio
async def test_registradas_return_meta():
    with patch("agrobr.rnc.client.fetch_registradas", new_callable=AsyncMock) as mock:
        mock.return_value = (_registradas_bytes(), "https://example.com")

        from agrobr.rnc import registradas

        result = await registradas(return_meta=True)
        assert isinstance(result, tuple)
        assert len(result) == 2
        df, meta = result
        assert isinstance(df, pd.DataFrame)
        assert meta.source == "rnc"


@pytest.mark.asyncio
async def test_registradas_as_polars():
    polars = pytest.importorskip("polars")
    with patch("agrobr.rnc.client.fetch_registradas", new_callable=AsyncMock) as mock:
        mock.return_value = (_registradas_bytes(), "https://example.com")

        from agrobr.rnc import registradas

        df = await registradas(as_polars=True)
        assert isinstance(df, polars.DataFrame)


@pytest.mark.asyncio
async def test_protegidas_returns_dataframe():
    with patch("agrobr.rnc.client.fetch_protegidas", new_callable=AsyncMock) as mock:
        mock.return_value = (_protegidas_bytes(), "https://example.com")

        from agrobr.rnc import protegidas

        df = await protegidas()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 25
        assert "titular" in df.columns


@pytest.mark.asyncio
async def test_protegidas_filter_situacao():
    with patch("agrobr.rnc.client.fetch_protegidas", new_callable=AsyncMock) as mock:
        mock.return_value = (_protegidas_bytes(), "https://example.com")

        from agrobr.rnc import protegidas

        df = await protegidas(situacao="DEFINITIVA")
        assert isinstance(df, pd.DataFrame)
        for v in df["situacao"].values:
            assert "DEFINITIVA" in v
