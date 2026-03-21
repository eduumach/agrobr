from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.ibama.models import COLUNAS_SAIDA, COLUNAS_SAIDA_GEO, MAX_FEATURES_GEO
from agrobr.ibama.parser import PARSER_VERSION, parse_embargos_csv

CSV_DIR = Path(__file__).parent.parent / "golden_data" / "ibama" / "embargos_sample"
GEO_DIR = Path(__file__).parent.parent / "golden_data" / "ibama" / "embargos_geo_sample"


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1


class TestParseEmbargosCsv:
    def test_valid_csv(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_embargos_csv([csv_bytes])

        assert len(df) == 10
        for col in COLUNAS_SAIDA:
            assert col in df.columns, f"Missing column: {col}"

    def test_golden_data_columns(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(CSV_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_embargos_csv([csv_bytes])

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_area_is_float(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_embargos_csv([csv_bytes])

        assert pd.api.types.is_float_dtype(df["area_desmatada_ha"])

    def test_uf_is_uppercase(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_embargos_csv([csv_bytes])

        for val in df["uf"].dropna():
            if val:
                assert val == val.upper()

    def test_empty_pages_returns_empty_dataframe(self):
        df = parse_embargos_csv([])

        assert len(df) == 0
        for col in COLUNAS_SAIDA:
            assert col in df.columns

    def test_invalid_csv_raises(self):
        with pytest.raises(ParseError):
            parse_embargos_csv([b""])

    def test_missing_required_columns_raises(self):
        csv = b"id,nome,valor\n1,teste,100\n"
        with pytest.raises(ParseError, match="Colunas obrigatorias ausentes"):
            parse_embargos_csv([csv])

    def test_count_matches_golden(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(CSV_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_embargos_csv([csv_bytes])

        assert len(df) == expected["count"]

    def test_multi_page_concat(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_embargos_csv([csv_bytes, csv_bytes])

        assert len(df) == 20

    def test_non_null_columns(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(CSV_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_embargos_csv([csv_bytes])

        for col in expected["non_null_columns"]:
            non_null = df[col].notna()
            non_empty = df[col].astype(str).str.strip() != ""
            assert (non_null & non_empty).all(), f"Column {col} has nulls/empty"


gpd = pytest.importorskip("geopandas")


class TestParseEmbargosGeojson:
    def _parse(self):
        from agrobr.ibama.parser import parse_embargos_geojson

        data = GEO_DIR.joinpath("response.geojson").read_bytes()
        return parse_embargos_geojson(data)

    def test_valid_geojson(self):
        gdf = self._parse()
        assert len(gdf) >= 5

    def test_columns_match_schema(self):
        gdf = self._parse()
        for col in COLUNAS_SAIDA_GEO:
            assert col in gdf.columns, f"Missing column: {col}"

    def test_geometry_exists(self):
        gdf = self._parse()
        assert "geometry" in gdf.columns

    def test_crs_4326(self):
        gdf = self._parse()
        assert gdf.crs.to_epsg() == 4326

    def test_uf_uppercase(self):
        gdf = self._parse()
        for val in gdf["uf"].dropna():
            if val:
                assert val == val.upper()

    def test_empty_features_returns_empty_geodataframe(self):
        from agrobr.ibama.parser import parse_embargos_geojson

        data = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        gdf = parse_embargos_geojson(data)

        assert len(gdf) == 0
        assert isinstance(gdf, gpd.GeoDataFrame)
        for col in COLUNAS_SAIDA_GEO:
            assert col in gdf.columns

    def test_invalid_json_raises(self):
        from agrobr.ibama.parser import parse_embargos_geojson

        with pytest.raises(ParseError):
            parse_embargos_geojson(b"not json at all {{{")

    def test_missing_required_columns_raises(self):
        from agrobr.ibama.parser import parse_embargos_geojson

        data = json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-54.0, -3.0]},
                        "properties": {"id": 1, "nome": "test"},
                    }
                ],
            }
        ).encode()
        with pytest.raises(ParseError, match="Colunas obrigatorias ausentes"):
            parse_embargos_geojson(data)

    def test_geopandas_not_installed(self):
        from agrobr.ibama.parser import parse_embargos_geojson

        with (
            patch(
                "agrobr.ibama.parser.check_geopandas",
                side_effect=ImportError(
                    "geopandas is required for geo functions. Install with: pip install agrobr[geo]"
                ),
            ),
            pytest.raises(ImportError, match="agrobr\\[geo\\]"),
        ):
            parse_embargos_geojson(b"{}")

    def test_truncation_warning(self):
        from agrobr.ibama.parser import parse_embargos_geojson

        data = GEO_DIR.joinpath("response.geojson").read_bytes()
        geojson = json.loads(data)
        features = geojson["features"]
        geojson["features"] = features * (MAX_FEATURES_GEO // len(features) + 1)
        assert len(geojson["features"]) >= MAX_FEATURES_GEO
        big_data = json.dumps(geojson).encode()

        with patch("agrobr.ibama.parser.logger") as mock_logger:
            parse_embargos_geojson(big_data)

        truncation_calls = [
            c
            for c in mock_logger.warning.call_args_list
            if c[0][0] == "ibama_embargos_geo_truncated"
        ]
        assert len(truncation_calls) == 1

    def test_null_geometry_warning(self):
        from agrobr.ibama.parser import parse_embargos_geojson

        data = json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": None,
                        "properties": {
                            "numero_tad": "123",
                            "data_tad": "2024-01-01",
                            "sig_uf": "MT",
                            "qtd_area_desmatada": "10.5",
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-54.0, -3.0]},
                        "properties": {
                            "numero_tad": "456",
                            "data_tad": "2024-02-01",
                            "sig_uf": "PA",
                            "qtd_area_desmatada": "20.0",
                        },
                    },
                ],
            }
        ).encode()

        with patch("agrobr.ibama.parser.logger") as mock_logger:
            gdf = parse_embargos_geojson(data)

        assert len(gdf) == 2
        null_calls = [
            c
            for c in mock_logger.warning.call_args_list
            if c[0][0] == "ibama_embargos_null_geometry"
        ]
        assert len(null_calls) == 1
        assert null_calls[0][1]["null_count"] == 1
