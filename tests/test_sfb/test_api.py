from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agrobr.sfb import api

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "sfb" / "cnfp_sample"


def _geojson_bytes() -> bytes:
    return GOLDEN_DIR.joinpath("response.geojson").read_bytes()


def _arcgis_json_bytes() -> bytes:
    data = json.loads(_geojson_bytes())
    arcgis: dict[str, list[dict[str, object]]] = {"features": []}
    for feat in data["features"]:
        arcgis["features"].append({"attributes": feat["properties"]})
    return json.dumps(arcgis).encode()


class TestCnfp:
    @pytest.mark.asyncio
    async def test_cnfp_returns_dataframe(self):
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://mapas.florestal.gov.br/arcgis"),
        ):
            df = await api.cnfp()

        assert len(df) == 5
        assert "nome" in df.columns
        assert "uf" in df.columns

    @pytest.mark.asyncio
    async def test_cnfp_return_meta(self):
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://mapas.florestal.gov.br/arcgis"),
        ):
            df, meta = await api.cnfp(return_meta=True)

        assert meta.source == "sfb"
        assert meta.source_method == "httpx+arcgis+json"
        assert meta.records_count == len(df)
        assert meta.parser_version == 1
        assert "sfb_cnfp" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_cnfp_uf_filter(self):
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://mapas.florestal.gov.br/arcgis"),
        ) as mock_fetch:
            await api.cnfp(uf="PA")

        call_kwargs = mock_fetch.call_args[1]
        assert "uf='PA'" in call_kwargs["where"]

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.cnfp(uf="INVALID")

    @pytest.mark.asyncio
    async def test_cnfp_as_polars(self):
        pl = pytest.importorskip("polars")
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://mapas.florestal.gov.br/arcgis"),
        ):
            result = await api.cnfp(as_polars=True)

        assert isinstance(result, pl.DataFrame)


class TestCnfpGeo:
    @pytest.fixture(autouse=True)
    def _skip_no_geopandas(self):
        pytest.importorskip("geopandas")

    @pytest.mark.asyncio
    async def test_cnfp_geo_returns_geodataframe(self):
        import geopandas as local_gpd

        geojson = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([geojson], "https://mapas.florestal.gov.br/arcgis"),
        ):
            gdf = await api.cnfp_geo()

        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) == 5
        assert "geometry" in gdf.columns

    @pytest.mark.asyncio
    async def test_cnfp_geo_return_meta(self):
        geojson = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([geojson], "https://mapas.florestal.gov.br/arcgis"),
        ):
            gdf, meta = await api.cnfp_geo(return_meta=True)

        assert meta.source == "sfb"
        assert meta.source_method == "httpx+arcgis+geojson"
        assert "sfb_cnfp_geo" in meta.attempted_sources


class TestConcessoes:
    @pytest.mark.asyncio
    async def test_concessoes_dataframe(self):
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://mapas.florestal.gov.br/arcgis"),
        ):
            df = await api.concessoes()

        assert len(df) > 0
