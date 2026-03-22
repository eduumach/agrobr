from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from agrobr.sfb.parser import PARSER_VERSION, parse_layer_tabular

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "sfb" / "cnfp_sample"


def _geojson_bytes() -> bytes:
    return GOLDEN_DIR.joinpath("response.geojson").read_bytes()


def _geojson_to_arcgis_json(geojson_bytes: bytes) -> bytes:
    data = json.loads(geojson_bytes)
    arcgis: dict[str, list[dict[str, object]]] = {"features": []}
    for feat in data["features"]:
        arcgis["features"].append({"attributes": feat["properties"]})
    return json.dumps(arcgis).encode()


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1


class TestParseTabularCnfp:
    def test_tabular_cnfp(self):
        arcgis = _geojson_to_arcgis_json(_geojson_bytes())
        df = parse_layer_tabular([arcgis], layer_key="cnfp")

        assert len(df) == 5
        assert "nome" in df.columns
        assert "area_ha" in df.columns

    def test_columns(self):
        expected = json.loads(GOLDEN_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        arcgis = _geojson_to_arcgis_json(_geojson_bytes())
        df = parse_layer_tabular([arcgis], layer_key="cnfp")

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_area_is_numeric(self):
        arcgis = _geojson_to_arcgis_json(_geojson_bytes())
        df = parse_layer_tabular([arcgis], layer_key="cnfp")

        assert pd.api.types.is_float_dtype(df["area_ha"])

    def test_empty_pages(self):
        df = parse_layer_tabular([], layer_key="cnfp")

        assert len(df) == 0
        assert "fid" in df.columns


gpd = pytest.importorskip("geopandas")


class TestParseGeojsonCnfp:
    def _parse(self):
        from agrobr.sfb.parser import parse_layer_geojson

        data = _geojson_bytes()
        return parse_layer_geojson([data], layer_key="cnfp")

    def test_geojson_cnfp(self):
        gdf = self._parse()
        assert len(gdf) == 5

    def test_columns(self):
        expected = json.loads(GOLDEN_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        gdf = self._parse()

        for col in expected["columns"]:
            assert col in gdf.columns, f"Missing column: {col}"
        assert "geometry" in gdf.columns

    def test_crs_4326(self):
        gdf = self._parse()
        assert gdf.crs.to_epsg() == 4326

    def test_empty_pages(self):
        from agrobr.sfb.parser import parse_layer_geojson

        gdf = parse_layer_geojson([], layer_key="cnfp")

        assert len(gdf) == 0
        assert isinstance(gdf, gpd.GeoDataFrame)
