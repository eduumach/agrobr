from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agrobr.ana import api

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "ana" / "pivos_sample"


def _geojson_bytes() -> bytes:
    return GOLDEN_DIR.joinpath("response.geojson").read_bytes()


def _arcgis_json_bytes() -> bytes:
    data = json.loads(_geojson_bytes())
    arcgis: dict[str, list[dict[str, object]]] = {"features": []}
    for feat in data["features"]:
        arcgis["features"].append({"attributes": feat["properties"]})
    return json.dumps(arcgis).encode()


class TestPivosIrrigacao:
    @pytest.mark.asyncio
    async def test_pivos_returns_dataframe(self):
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://portal1.snirh.gov.br/arcgis"),
        ):
            df = await api.pivos_irrigacao()

        assert len(df) == 5
        assert "municipio" in df.columns
        assert "estado" in df.columns

    @pytest.mark.asyncio
    async def test_pivos_return_meta(self):
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://portal1.snirh.gov.br/arcgis"),
        ):
            df, meta = await api.pivos_irrigacao(return_meta=True)

        assert meta.source == "ana"
        assert meta.source_method == "httpx+arcgis+json"
        assert meta.records_count == len(df)
        assert meta.parser_version == 1
        assert "ana_pivos_irrigacao" in meta.attempted_sources

    @pytest.mark.asyncio
    async def test_pivos_uf_filter(self):
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://portal1.snirh.gov.br/arcgis"),
        ) as mock_fetch:
            await api.pivos_irrigacao(uf="MT")

        call_kwargs = mock_fetch.call_args[1]
        assert "NM_ESTADO='Mato Grosso'" in call_kwargs["where"]

    @pytest.mark.asyncio
    async def test_invalid_uf_raises(self):
        with pytest.raises(ValueError, match="UF invalida"):
            await api.pivos_irrigacao(uf="INVALID")

    @pytest.mark.asyncio
    async def test_pivos_as_polars(self):
        pl = pytest.importorskip("polars")
        arcgis = _arcgis_json_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://portal1.snirh.gov.br/arcgis"),
        ):
            result = await api.pivos_irrigacao(as_polars=True)

        assert isinstance(result, pl.DataFrame)


class TestPivosIrrigacaoGeo:
    @pytest.fixture(autouse=True)
    def _skip_no_geopandas(self):
        pytest.importorskip("geopandas")

    @pytest.mark.asyncio
    async def test_pivos_geo_returns_geodataframe(self):
        import geopandas as local_gpd

        geojson = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([geojson], "https://portal1.snirh.gov.br/arcgis"),
        ):
            gdf = await api.pivos_irrigacao_geo()

        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) == 5
        assert "geometry" in gdf.columns

    @pytest.mark.asyncio
    async def test_pivos_geo_return_meta(self):
        geojson = _geojson_bytes()
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([geojson], "https://portal1.snirh.gov.br/arcgis"),
        ):
            gdf, meta = await api.pivos_irrigacao_geo(return_meta=True)

        assert meta.source == "ana"
        assert meta.source_method == "httpx+arcgis+geojson"
        assert "ana_pivos_irrigacao_geo" in meta.attempted_sources


class TestHidrografia:
    @pytest.mark.asyncio
    async def test_hidrografia_requires_bbox(self):
        arcgis = _arcgis_json_bytes()
        bbox = (-50.0, -15.0, -45.0, -10.0)
        with patch.object(
            api.client,
            "fetch_layer",
            new_callable=AsyncMock,
            return_value=([arcgis], "https://portal1.snirh.gov.br/arcgis"),
        ) as mock_fetch:
            await api.hidrografia(bbox=bbox)

        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs["bbox"] == bbox
