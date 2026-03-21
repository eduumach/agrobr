from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agrobr.ibama import api

CSV_DIR = Path(__file__).parent.parent / "golden_data" / "ibama" / "embargos_sample"
GEO_DIR = Path(__file__).parent.parent / "golden_data" / "ibama" / "embargos_geo_sample"


def _csv_bytes() -> bytes:
    return CSV_DIR.joinpath("response.csv").read_bytes()


def _geojson_bytes() -> bytes:
    return GEO_DIR.joinpath("response.geojson").read_bytes()


class TestEmbargos:
    @pytest.mark.asyncio
    async def test_returns_dataframe(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_embargos",
            new_callable=AsyncMock,
            return_value=([csv_bytes], "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            df = await api.embargos()

        assert len(df) == 10
        assert "numero_tad" in df.columns
        assert "uf" in df.columns
        assert "data_embargo" in df.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_embargos",
            new_callable=AsyncMock,
            return_value=([csv_bytes], "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            df, meta = await api.embargos(return_meta=True)

        assert meta.source == "ibama"
        assert meta.source_method == "httpx+wfs+csv"
        assert meta.records_count == len(df)
        assert meta.parser_version == 1
        assert meta.fetch_timestamp is not None
        assert "ibama_geoserver" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_embargos",
            new_callable=AsyncMock,
            return_value=([csv_bytes], "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            result = await api.embargos(as_polars=True)

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.asyncio
    async def test_uf_filter_passthrough(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_embargos",
            new_callable=AsyncMock,
            return_value=([csv_bytes], "https://siscom.ibama.gov.br/geoserver/wfs"),
        ) as mock_fetch:
            await api.embargos(uf="MT")

        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["uf"] == "MT"

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.embargos(uf="INVALID")

    @pytest.mark.asyncio
    async def test_dedup_by_numero_tad(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_embargos",
            new_callable=AsyncMock,
            return_value=([csv_bytes, csv_bytes], "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            df = await api.embargos()

        assert len(df) == 10

    @pytest.mark.asyncio
    async def test_empty_result(self):
        with patch.object(
            api.client,
            "fetch_embargos",
            new_callable=AsyncMock,
            return_value=([], "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            df = await api.embargos()

        assert len(df) == 0


class TestEmbargosGeo:
    @pytest.fixture(autouse=True)
    def _skip_no_geopandas(self):
        pytest.importorskip("geopandas")

    @pytest.mark.asyncio
    async def test_returns_geodataframe(self):
        import geopandas as local_gpd

        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_embargos_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            gdf = await api.embargos_geo()

        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) >= 5
        assert "geometry" in gdf.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_embargos_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            gdf, meta = await api.embargos_geo(return_meta=True)

        assert meta.source == "ibama"
        assert meta.source_method == "httpx+wfs+geojson"
        assert meta.records_count == len(gdf)
        assert "ibama_geoserver_geo" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_bbox_passthrough(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_embargos_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://siscom.ibama.gov.br/geoserver/wfs"),
        ) as mock_fetch:
            await api.embargos_geo(bbox=(-60.0, -15.0, -50.0, -10.0))

        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["bbox"] == (-60.0, -15.0, -50.0, -10.0)

    @pytest.mark.asyncio
    async def test_geometry_preserved(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_embargos_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            gdf = await api.embargos_geo()

        assert "geometry" in gdf.columns

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.embargos_geo(uf="123")

    @pytest.mark.asyncio
    async def test_empty_result(self):
        import geopandas as local_gpd

        empty_geojson = b'{"type": "FeatureCollection", "features": []}'
        with patch.object(
            api.client,
            "fetch_embargos_geo",
            new_callable=AsyncMock,
            return_value=(empty_geojson, "https://siscom.ibama.gov.br/geoserver/wfs"),
        ):
            gdf = await api.embargos_geo()

        assert len(gdf) == 0
        assert isinstance(gdf, local_gpd.GeoDataFrame)
