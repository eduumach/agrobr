from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agrobr.funai import api

CSV_DIR = Path(__file__).parent.parent / "golden_data" / "funai" / "terras_indigenas_sample"
GEO_DIR = Path(__file__).parent.parent / "golden_data" / "funai" / "terras_indigenas_geo_sample"


def _csv_bytes() -> bytes:
    return CSV_DIR.joinpath("response.csv").read_bytes()


def _geojson_bytes() -> bytes:
    return GEO_DIR.joinpath("response.geojson").read_bytes()


class TestTerrasIndigenas:
    @pytest.mark.asyncio
    async def test_returns_dataframe(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            df = await api.terras_indigenas()

        assert len(df) == 10
        assert "codigo" in df.columns
        assert "nome" in df.columns
        assert "uf" in df.columns
        assert "area_ha" in df.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            df, meta = await api.terras_indigenas(return_meta=True)

        assert meta.source == "funai"
        assert meta.source_method == "httpx+wfs+csv"
        assert meta.records_count == len(df)
        assert meta.parser_version == 1
        assert meta.fetch_timestamp is not None
        assert "funai_geoserver" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_as_polars(self):
        pl = pytest.importorskip("polars")
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            result = await api.terras_indigenas(as_polars=True)

        assert isinstance(result, pl.DataFrame)

    @pytest.mark.asyncio
    async def test_filter_uf_passthrough(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ) as mock_fetch:
            await api.terras_indigenas(uf="MT")

        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["uf"] == "MT"

    @pytest.mark.asyncio
    async def test_filter_fase_passthrough(self):
        csv_bytes = _csv_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas",
            new_callable=AsyncMock,
            return_value=(csv_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ) as mock_fetch:
            await api.terras_indigenas(fase="Regularizada")

        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["fase"] == "Regularizada"

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.terras_indigenas(uf="INVALID")

    @pytest.mark.asyncio
    async def test_invalid_fase_raises(self):
        with pytest.raises(ValueError, match="Fase invalida"):
            await api.terras_indigenas(fase="FaseInexistente")


class TestTerrasIndigenasGeo:
    @pytest.fixture(autouse=True)
    def _skip_no_geopandas(self):
        pytest.importorskip("geopandas")

    @pytest.mark.asyncio
    async def test_returns_geodataframe(self):
        import geopandas as local_gpd

        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf = await api.terras_indigenas_geo()

        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) >= 10
        assert "geometry" in gdf.columns

    @pytest.mark.asyncio
    async def test_return_meta(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf, meta = await api.terras_indigenas_geo(return_meta=True)

        assert meta.source == "funai"
        assert meta.source_method == "httpx+wfs+geojson"
        assert meta.records_count == len(gdf)
        assert "funai_geoserver_geo" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_bbox_passthrough(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ) as mock_fetch:
            await api.terras_indigenas_geo(bbox=(-60.0, -15.0, -50.0, -10.0))

        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["bbox"] == (-60.0, -15.0, -50.0, -10.0)

    @pytest.mark.asyncio
    async def test_client_receives_only_bbox(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ) as mock_fetch:
            await api.terras_indigenas_geo(
                uf="MT", fase="Regularizada", bbox=(-60.0, -15.0, -50.0, -10.0)
            )

        call_kwargs = mock_fetch.call_args[1]
        assert "uf" not in call_kwargs
        assert "fase" not in call_kwargs
        assert call_kwargs["bbox"] == (-60.0, -15.0, -50.0, -10.0)

    @pytest.mark.asyncio
    async def test_post_filter_by_fase(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf = await api.terras_indigenas_geo(fase="Regularizada")

        assert len(gdf) == 6
        assert (gdf["fase"] == "Regularizada").all()

    @pytest.mark.asyncio
    async def test_post_filter_by_fase_single(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf = await api.terras_indigenas_geo(fase="Em Estudo")

        assert len(gdf) == 1

    @pytest.mark.asyncio
    async def test_post_filter_no_match_returns_empty(self):
        import geopandas as local_gpd

        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf = await api.terras_indigenas_geo(uf="AC")

        assert len(gdf) == 0
        assert isinstance(gdf, local_gpd.GeoDataFrame)

    @pytest.mark.asyncio
    async def test_post_filter_combined_uf_fase(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf = await api.terras_indigenas_geo(uf="MT", fase="Homologada")

        assert len(gdf) == 2
        assert (gdf["uf"] == "MT").all()
        assert (gdf["fase"] == "Homologada").all()

    @pytest.mark.asyncio
    async def test_post_filter_meta_reflects_filtered_count(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf, meta = await api.terras_indigenas_geo(fase="Declarada", return_meta=True)

        assert len(gdf) == 1
        assert meta.records_count == 1

    @pytest.mark.asyncio
    async def test_geometry_preserved(self):
        geojson_bytes = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(geojson_bytes, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf = await api.terras_indigenas_geo()

        assert "geometry" in gdf.columns
        assert gdf.geometry.is_valid.all()

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.terras_indigenas_geo(uf="123")

    @pytest.mark.asyncio
    async def test_invalid_fase_raises(self):
        with pytest.raises(ValueError, match="Fase invalida"):
            await api.terras_indigenas_geo(fase="NaoExiste")

    @pytest.mark.asyncio
    async def test_empty_result(self):
        import geopandas as local_gpd

        empty_geojson = b'{"type": "FeatureCollection", "features": []}'
        with patch.object(
            api.client,
            "fetch_terras_indigenas_geo",
            new_callable=AsyncMock,
            return_value=(empty_geojson, "https://geoserver.funai.gov.br/geoserver/Funai/ows"),
        ):
            gdf = await api.terras_indigenas_geo()

        assert len(gdf) == 0
        assert isinstance(gdf, local_gpd.GeoDataFrame)
