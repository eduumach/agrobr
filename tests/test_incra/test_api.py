from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agrobr.incra import api

QUILOMBOLAS_DIR = Path(__file__).parent.parent / "golden_data" / "incra" / "quilombolas_sample"
QUILOMBOLAS_GEO_DIR = (
    Path(__file__).parent.parent / "golden_data" / "incra" / "quilombolas_geo_sample"
)


def _csv_bytes() -> bytes:
    return QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()


def _geojson_bytes() -> bytes:
    return QUILOMBOLAS_GEO_DIR.joinpath("response.geojson").read_bytes()


class TestQuilombolas:
    @pytest.mark.asyncio
    async def test_returns_dataframe(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            df = await api.quilombolas()

        assert len(df) == 10
        assert "codigo" in df.columns
        assert "nome" in df.columns
        assert "area_ha" in df.columns
        assert "uf" in df.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            df, meta = await api.quilombolas(return_meta=True)

        assert meta.source == "incra"
        assert meta.records_count == len(df)
        assert meta.parser_version == 1
        assert meta.fetch_timestamp is not None
        assert "incra_wfs" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_source_method_csv(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            _, meta = await api.quilombolas(return_meta=True)

        assert meta.source_method == "httpx+wfs+csv"

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.quilombolas(uf="INVALID")

    @pytest.mark.asyncio
    async def test_invalid_bbox_raises(self):
        with pytest.raises(ValueError, match="BBOX"):
            await api.quilombolas(bbox=(10.0, 5.0, 5.0, 10.0))

    @pytest.mark.asyncio
    async def test_passes_uf_to_client(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ) as mock_fetch:
            await api.quilombolas(uf="GO")

        assert mock_fetch.call_args.kwargs["uf"] == "GO"

    @pytest.mark.asyncio
    async def test_uf_case_insensitive(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ) as mock_fetch:
            await api.quilombolas(uf="go")

        assert mock_fetch.call_args.kwargs["uf"] == "GO"


gpd = pytest.importorskip("geopandas")


class TestQuilombolasGeo:
    @pytest.mark.asyncio
    async def test_returns_geodataframe(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf = await api.quilombolas_geo()

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) >= 10
        assert "codigo" in gdf.columns
        assert "geometry" in gdf.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf, meta = await api.quilombolas_geo(return_meta=True)

        assert meta.source == "incra"
        assert meta.source_method == "httpx+wfs+geojson"
        assert meta.records_count == len(gdf)
        assert "incra_wfs_geo" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.quilombolas_geo(uf="INVALID")

    @pytest.mark.asyncio
    async def test_invalid_bbox_raises(self):
        with pytest.raises(ValueError, match="BBOX"):
            await api.quilombolas_geo(bbox=(10.0, 5.0, 5.0, 10.0))

    @pytest.mark.asyncio
    async def test_geometry_preserved(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf = await api.quilombolas_geo()

        assert "geometry" in gdf.columns
        assert gdf.geometry.is_valid.all()

    @pytest.mark.asyncio
    async def test_client_receives_only_bbox(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ) as mock_fetch:
            await api.quilombolas_geo(uf="GO", fase="Titulada", bbox=(-60.0, -15.0, -50.0, -10.0))

        call_kwargs = mock_fetch.call_args.kwargs
        assert "uf" not in call_kwargs
        assert "fase" not in call_kwargs
        assert call_kwargs["bbox"] == (-60.0, -15.0, -50.0, -10.0)

    @pytest.mark.asyncio
    async def test_post_filter_by_uf(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf = await api.quilombolas_geo(uf="GO")

        assert len(gdf) == 2
        assert (gdf["uf"] == "GO").all()

    @pytest.mark.asyncio
    async def test_post_filter_by_fase(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf = await api.quilombolas_geo(fase="Titulada")

        assert len(gdf) == 5
        assert (gdf["fase"] == "Titulada").all()

    @pytest.mark.asyncio
    async def test_post_filter_combined_uf_fase(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf = await api.quilombolas_geo(uf="GO", fase="Titulada")

        assert len(gdf) == 1
        assert (gdf["uf"] == "GO").all()
        assert (gdf["fase"] == "Titulada").all()

    @pytest.mark.asyncio
    async def test_post_filter_no_match_returns_empty(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf = await api.quilombolas_geo(uf="AC")

        assert len(gdf) == 0
        assert isinstance(gdf, gpd.GeoDataFrame)

    @pytest.mark.asyncio
    async def test_post_filter_meta_reflects_filtered_count(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            gdf, meta = await api.quilombolas_geo(uf="SP", return_meta=True)

        assert len(gdf) == 2
        assert meta.records_count == 2

    @pytest.mark.asyncio
    async def test_no_return_meta_returns_gdf_only(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_quilombolas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://cmr.funai.gov.br/geoserver/ows"),
        ):
            result = await api.quilombolas_geo()

        assert isinstance(result, gpd.GeoDataFrame)
