from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.acervo_fundiario import api

GOLDEN = Path(__file__).resolve().parent.parent / "golden_data" / "acervo_fundiario"


def _sigef_bytes() -> bytes:
    return (GOLDEN / "sigef_sample" / "response.gml").read_bytes()


def _snci_bytes() -> bytes:
    return (GOLDEN / "snci_sample" / "response.gml").read_bytes()


def _assentamentos_bytes() -> bytes:
    return (GOLDEN / "assentamentos_sample" / "response.gml").read_bytes()


# ---------------------------------------------------------------------------
# SIGEF
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSigef:
    @patch.object(api.client, "fetch_sigef", new_callable=AsyncMock)
    async def test_returns_dataframe(self, mock_fetch):
        mock_fetch.return_value = (_sigef_bytes(), "https://test")
        df = await api.sigef("GO")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5

    @patch.object(api.client, "fetch_sigef", new_callable=AsyncMock)
    async def test_return_meta(self, mock_fetch):
        mock_fetch.return_value = (_sigef_bytes(), "https://test")
        df, meta = await api.sigef("GO", return_meta=True)
        assert isinstance(df, pd.DataFrame)
        assert meta.source == "acervo_fundiario"
        assert meta.source_method == "httpx+wfs+gml2"
        assert meta.records_count == 5

    @patch.object(api.client, "fetch_sigef", new_callable=AsyncMock)
    async def test_as_polars(self, mock_fetch):
        pl = pytest.importorskip("polars")
        mock_fetch.return_value = (_sigef_bytes(), "https://test")
        result = await api.sigef("GO", as_polars=True)
        assert isinstance(result, pl.DataFrame)

    @patch.object(api.client, "fetch_sigef", new_callable=AsyncMock)
    async def test_tipo_publico(self, mock_fetch):
        mock_fetch.return_value = (_sigef_bytes(), "https://test")
        await api.sigef("GO", tipo="publico")
        mock_fetch.assert_called_once_with("GO", "publico", bbox=None)

    async def test_invalid_uf(self):
        with pytest.raises(ValueError):
            await api.sigef("XX")

    async def test_invalid_tipo(self):
        with pytest.raises(ValueError):
            await api.sigef("GO", tipo="invalido")


@pytest.mark.asyncio
class TestSigefGeo:
    @patch.object(api.client, "fetch_sigef", new_callable=AsyncMock)
    async def test_returns_geodataframe(self, mock_fetch):
        gpd = pytest.importorskip("geopandas")
        mock_fetch.return_value = (
            (GOLDEN / "sigef_geo_sample" / "response.gml").read_bytes(),
            "https://test",
        )
        gdf = await api.sigef_geo("GO")
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 3

    @patch.object(api.client, "fetch_sigef", new_callable=AsyncMock)
    async def test_geo_calls_with_geo_flag(self, mock_fetch):
        pytest.importorskip("geopandas")
        mock_fetch.return_value = (
            (GOLDEN / "sigef_geo_sample" / "response.gml").read_bytes(),
            "https://test",
        )
        await api.sigef_geo("GO")
        mock_fetch.assert_called_once_with("GO", "particular", bbox=None, geo=True)


# ---------------------------------------------------------------------------
# SNCI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSnci:
    @patch.object(api.client, "fetch_snci", new_callable=AsyncMock)
    async def test_returns_dataframe(self, mock_fetch):
        mock_fetch.return_value = (_snci_bytes(), "https://test")
        df = await api.snci("GO")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5

    @patch.object(api.client, "fetch_snci", new_callable=AsyncMock)
    async def test_return_meta(self, mock_fetch):
        mock_fetch.return_value = (_snci_bytes(), "https://test")
        df, meta = await api.snci("GO", return_meta=True)
        assert meta.source == "acervo_fundiario"
        assert meta.records_count == 5

    @patch.object(api.client, "fetch_snci", new_callable=AsyncMock)
    async def test_tipo_publico(self, mock_fetch):
        mock_fetch.return_value = (_snci_bytes(), "https://test")
        await api.snci("GO", tipo="publico")
        mock_fetch.assert_called_once_with("GO", "publico", bbox=None)

    async def test_invalid_tipo(self):
        with pytest.raises(ValueError):
            await api.snci("GO", tipo="invalido")


@pytest.mark.asyncio
class TestSnciGeo:
    @patch.object(api.client, "fetch_snci", new_callable=AsyncMock)
    async def test_returns_geodataframe(self, mock_fetch):
        gpd = pytest.importorskip("geopandas")
        mock_fetch.return_value = (
            (GOLDEN / "snci_geo_sample" / "response.gml").read_bytes(),
            "https://test",
        )
        gdf = await api.snci_geo("GO")
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 3


# ---------------------------------------------------------------------------
# Assentamentos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAssentamentos:
    @patch.object(api.client, "fetch_assentamentos", new_callable=AsyncMock)
    async def test_returns_dataframe(self, mock_fetch):
        mock_fetch.return_value = (_assentamentos_bytes(), "https://test")
        df = await api.assentamentos("GO")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5

    @patch.object(api.client, "fetch_assentamentos", new_callable=AsyncMock)
    async def test_return_meta(self, mock_fetch):
        mock_fetch.return_value = (_assentamentos_bytes(), "https://test")
        df, meta = await api.assentamentos("GO", return_meta=True)
        assert meta.source == "acervo_fundiario"
        assert meta.records_count == 5

    @patch.object(api.client, "fetch_assentamentos", new_callable=AsyncMock)
    async def test_with_bbox(self, mock_fetch):
        mock_fetch.return_value = (_assentamentos_bytes(), "https://test")
        await api.assentamentos("GO", bbox=(-50, -16, -49, -15))
        mock_fetch.assert_called_once_with("GO", bbox=(-50.0, -16.0, -49.0, -15.0))


@pytest.mark.asyncio
class TestAssentamentosGeo:
    @patch.object(api.client, "fetch_assentamentos", new_callable=AsyncMock)
    async def test_returns_geodataframe(self, mock_fetch):
        gpd = pytest.importorskip("geopandas")
        mock_fetch.return_value = (
            (GOLDEN / "assentamentos_geo_sample" / "response.gml").read_bytes(),
            "https://test",
        )
        gdf = await api.assentamentos_geo("GO")
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 3

    @patch.object(api.client, "fetch_assentamentos", new_callable=AsyncMock)
    async def test_return_meta(self, mock_fetch):
        gpd = pytest.importorskip("geopandas")
        mock_fetch.return_value = (
            (GOLDEN / "assentamentos_geo_sample" / "response.gml").read_bytes(),
            "https://test",
        )
        gdf, meta = await api.assentamentos_geo("GO", return_meta=True)
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert meta.source == "acervo_fundiario"
