from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.mapbiomas_alerta.parser import PARSER_VERSION, parse_alertas

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "mapbiomas_alerta" / "alertas_sample"


def _load_records() -> list[dict]:
    return json.loads((GOLDEN_DIR / "response.json").read_text(encoding="utf-8"))


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1


class TestParseAlertas:
    def test_valid_records(self):
        records = _load_records()
        df = parse_alertas(records)
        assert len(df) == 5
        assert "alert_code" in df.columns
        assert "area_ha" in df.columns
        assert "uf" in df.columns

    def test_empty_records(self):
        df = parse_alertas([])
        assert len(df) == 0
        assert "alert_code" in df.columns

    def test_types(self):
        records = _load_records()
        df = parse_alertas(records)
        assert df["area_ha"].dtype == "float64"
        assert pd.api.types.is_datetime64_any_dtype(df["data_deteccao"])

    def test_rename(self):
        records = _load_records()
        df = parse_alertas(records)
        assert "alertCode" not in df.columns
        assert "alert_code" in df.columns
        assert "areaHa" not in df.columns

    def test_lat_lon(self):
        records = _load_records()
        df = parse_alertas(records)
        assert "lat" in df.columns
        assert "lon" in df.columns
        assert df["lat"].notna().all()

    def test_uf_uppercase(self):
        records = _load_records()
        df = parse_alertas(records)
        assert (df["uf"].str.isupper() | (df["uf"] == "")).all()

    def test_golden_data_columns(self):
        records = _load_records()
        expected = json.loads((GOLDEN_DIR / "expected.json").read_text(encoding="utf-8"))
        df = parse_alertas(records)

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_count_matches_golden(self):
        records = _load_records()
        expected = json.loads((GOLDEN_DIR / "expected.json").read_text(encoding="utf-8"))
        df = parse_alertas(records)

        assert len(df) == expected["count"]

    def test_missing_required_fields_raises(self):
        records = [{"foo": "bar"}]
        with pytest.raises(ParseError):
            parse_alertas(records)

    def test_null_coordenates(self):
        records = [
            {
                "alertCode": "X",
                "areaHa": 1.0,
                "detectedAt": "2024-01-01",
                "publishedAt": "2024-01-05",
                "statusName": "Publicado",
                "source": "DETER",
                "biome": "Amazonia",
                "state": "PA",
                "city": "Altamira",
                "coordenates": None,
            }
        ]
        df = parse_alertas(records)
        assert len(df) == 1
        assert pd.isna(df.iloc[0]["lat"])

    def test_geometry_wkt_stripped(self):
        records = _load_records()
        df = parse_alertas(records)
        assert "geometryWkt" not in df.columns
        assert "geometry" not in df.columns


class TestParseAlertasGeo:
    @pytest.fixture(autouse=True)
    def _skip_no_geopandas(self):
        pytest.importorskip("geopandas")

    def test_valid_records(self):
        import geopandas as local_gpd

        from agrobr.mapbiomas_alerta.parser import parse_alertas_geo

        records = _load_records()
        gdf = parse_alertas_geo(records)
        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) == 5
        assert "geometry" in gdf.columns
        assert gdf.crs.to_epsg() == 4326

    def test_empty_records(self):
        import geopandas as local_gpd

        from agrobr.mapbiomas_alerta.parser import parse_alertas_geo

        gdf = parse_alertas_geo([])
        assert isinstance(gdf, local_gpd.GeoDataFrame)
        assert len(gdf) == 0

    def test_null_wkt(self):
        from agrobr.mapbiomas_alerta.parser import parse_alertas_geo

        records = [
            {
                "alertCode": "X",
                "areaHa": 1.0,
                "detectedAt": "2024-01-01",
                "publishedAt": "2024-01-05",
                "statusName": "Publicado",
                "source": "DETER",
                "biome": "Amazonia",
                "state": "PA",
                "city": "Altamira",
                "coordenates": {"lat": -3.0, "lng": -52.0},
                "geometryWkt": None,
            }
        ]
        gdf = parse_alertas_geo(records)
        assert len(gdf) == 1
        assert gdf.geometry.isna().sum() == 1

    def test_invalid_wkt(self):
        from agrobr.mapbiomas_alerta.parser import parse_alertas_geo

        records = [
            {
                "alertCode": "X",
                "areaHa": 1.0,
                "detectedAt": "2024-01-01",
                "publishedAt": "2024-01-05",
                "statusName": "Publicado",
                "source": "DETER",
                "biome": "Amazonia",
                "state": "PA",
                "city": "Altamira",
                "coordenates": {"lat": -3.0, "lng": -52.0},
                "geometryWkt": "NOT_A_WKT",
            }
        ]
        gdf = parse_alertas_geo(records)
        assert len(gdf) == 1
        assert gdf.geometry.isna().sum() == 1

    def test_golden_geo_columns(self):
        from agrobr.mapbiomas_alerta.parser import parse_alertas_geo

        geo_dir = (
            Path(__file__).parent.parent / "golden_data" / "mapbiomas_alerta" / "alertas_geo_sample"
        )
        expected = json.loads((geo_dir / "expected.json").read_text(encoding="utf-8"))
        records = json.loads((geo_dir / "response.json").read_text(encoding="utf-8"))
        gdf = parse_alertas_geo(records)

        for col in expected["columns"]:
            assert col in gdf.columns, f"Missing column: {col}"
        assert gdf.crs.to_epsg() == expected["crs_epsg"]

    def test_missing_required_fields_raises(self):
        from agrobr.mapbiomas_alerta.parser import parse_alertas_geo

        records = [{"foo": "bar"}]
        with pytest.raises(ParseError):
            parse_alertas_geo(records)
