from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.incra.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    MAX_FEATURES_GEO,
    MAX_FEATURES_TABULAR,
)
from agrobr.incra.parser import PARSER_VERSION, parse_quilombolas_csv

QUILOMBOLAS_DIR = Path(__file__).parent.parent / "golden_data" / "incra" / "quilombolas_sample"
QUILOMBOLAS_GEO_DIR = (
    Path(__file__).parent.parent / "golden_data" / "incra" / "quilombolas_geo_sample"
)


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1


class TestParseQuilombolasCsv:
    def test_valid_csv(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        df = parse_quilombolas_csv(csv_bytes)

        assert len(df) == 10
        assert "codigo" in df.columns
        assert "nome" in df.columns
        assert "municipio" in df.columns
        assert "uf" in df.columns
        assert "area_ha" in df.columns

    def test_golden_data_columns(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(QUILOMBOLAS_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_quilombolas_csv(csv_bytes)

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_golden_data_count(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(QUILOMBOLAS_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_quilombolas_csv(csv_bytes)

        assert len(df) == expected["count"]

    def test_area_ha_is_float(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        df = parse_quilombolas_csv(csv_bytes)

        assert pd.api.types.is_float_dtype(df["area_ha"])

    def test_familias_is_int64_nullable(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        df = parse_quilombolas_csv(csv_bytes)

        assert df["familias"].dtype == pd.Int64Dtype()

    def test_titulado_values(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        df = parse_quilombolas_csv(csv_bytes)

        valid_values = {"T", "F"}
        for val in df["titulado"].dropna():
            assert val in valid_values, f"Unexpected titulado value: {val}"

    def test_dates_parse_correctly(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        df = parse_quilombolas_csv(csv_bytes)

        titled = df[df["titulado"] == "T"]
        assert titled["data_publicacao"].notna().all()

    def test_area_non_negative(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        df = parse_quilombolas_csv(csv_bytes)

        assert (df["area_ha"] >= 0).all()

    def test_non_null_columns(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(QUILOMBOLAS_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_quilombolas_csv(csv_bytes)

        for col in expected["non_null_columns"]:
            assert df[col].notna().all(), f"Column {col} has null values"

    def test_empty_csv_returns_empty_dataframe(self):
        csv = b"cd_quilomb,no_comunidade,no_municipio,sg_uf,nu_area_ha,nu_familia,ds_fase,st_titulad,dt_publica,dt_titulo\n"
        df = parse_quilombolas_csv(csv)

        assert len(df) == 0
        assert list(df.columns) == COLUNAS_SAIDA

    def test_invalid_csv_raises(self):
        with pytest.raises(ParseError):
            parse_quilombolas_csv(b"col1\n" + b"\xff\xfe" * 1000)

    def test_missing_columns_raises(self):
        csv = b"id,nome,valor\n1,teste,100\n"
        with pytest.raises(ParseError, match="Colunas obrigatorias ausentes"):
            parse_quilombolas_csv(csv)

    def test_output_columns_match(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        df = parse_quilombolas_csv(csv_bytes)

        for col in COLUNAS_SAIDA:
            assert col in df.columns, f"Missing column: {col}"

    def test_truncation_warning(self):
        csv_bytes = QUILOMBOLAS_DIR.joinpath("response.csv").read_bytes()
        header, *rows = csv_bytes.decode("utf-8").splitlines()
        n_repeats = MAX_FEATURES_TABULAR // len(rows) + 1
        big_csv = (header + "\n" + "\n".join(rows * n_repeats)).encode()

        with patch("agrobr.incra.parser.logger") as mock_logger:
            df = parse_quilombolas_csv(big_csv)

        assert len(df) >= MAX_FEATURES_TABULAR
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[0][0] == "incra_quilombolas_truncated"


gpd = pytest.importorskip("geopandas")


class TestParseQuilombolasGeojson:
    def _parse(self):
        from agrobr.incra.parser import parse_quilombolas_geojson

        data = QUILOMBOLAS_GEO_DIR.joinpath("response.geojson").read_bytes()
        return parse_quilombolas_geojson(data)

    def test_valid_geojson(self):
        gdf = self._parse()
        assert len(gdf) >= 10
        assert "codigo" in gdf.columns
        assert "nome" in gdf.columns
        assert "area_ha" in gdf.columns

    def test_output_columns_match_schema(self):
        gdf = self._parse()
        for col in COLUNAS_SAIDA_GEO:
            assert col in gdf.columns, f"Missing column: {col}"

    def test_geometry_column_exists(self):
        gdf = self._parse()
        assert "geometry" in gdf.columns

    def test_geometry_is_valid(self):
        gdf = self._parse()
        assert gdf.geometry.is_valid.all()

    def test_crs_is_4326(self):
        gdf = self._parse()
        assert gdf.crs.to_epsg() == 4326

    def test_area_ha_non_negative(self):
        gdf = self._parse()
        assert (gdf["area_ha"] >= 0).all()

    def test_familias_is_int64(self):
        gdf = self._parse()
        assert gdf["familias"].dtype == pd.Int64Dtype()

    def test_empty_features_returns_empty_geodataframe(self):
        from agrobr.incra.parser import parse_quilombolas_geojson

        data = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        gdf = parse_quilombolas_geojson(data)
        assert len(gdf) == 0

    def test_invalid_json_raises(self):
        from agrobr.incra.parser import parse_quilombolas_geojson

        with pytest.raises(ParseError):
            parse_quilombolas_geojson(b"not json at all {{{")

    def test_missing_columns_raises(self):
        from agrobr.incra.parser import parse_quilombolas_geojson

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
            parse_quilombolas_geojson(data)

    def test_geopandas_not_installed(self):
        from agrobr.incra.parser import parse_quilombolas_geojson

        with (
            patch(
                "agrobr.incra.parser.check_geopandas",
                side_effect=ImportError(
                    "geopandas is required for geo functions. Install with: pip install agrobr[geo]"
                ),
            ),
            pytest.raises(ImportError, match="agrobr\\[geo\\]"),
        ):
            parse_quilombolas_geojson(b"{}")

    def test_repair_invalid_geometry(self):
        from agrobr.incra.parser import parse_quilombolas_geojson

        bowtie = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0.0, 0.0], [2.0, 2.0], [0.0, 2.0], [2.0, 0.0], [0.0, 0.0]]
                        ],
                    },
                    "properties": {
                        "cd_quilomb": "TEST001",
                        "no_comunidade": "Test",
                        "no_municipio": "Test",
                        "sg_uf": "BA",
                        "nu_area_ha": 100.0,
                        "nu_familia": "10",
                        "ds_fase": "TITULADO",
                        "st_titulad": "T",
                        "dt_publica": "2020-01-01",
                        "dt_titulo": "2020-01-01",
                    },
                },
            ],
        }
        data = json.dumps(bowtie).encode()

        with patch("agrobr.incra.parser.logger") as mock_logger:
            gdf = parse_quilombolas_geojson(data)

        assert gdf.geometry.is_valid.all()
        repaired_calls = [
            c
            for c in mock_logger.warning.call_args_list
            if c[0][0] == "incra_quilombolas_geo_repaired"
        ]
        assert len(repaired_calls) == 1
        assert repaired_calls[0][1]["invalid"] == 1

    def test_truncation_warning(self):
        from agrobr.incra.parser import parse_quilombolas_geojson

        data = QUILOMBOLAS_GEO_DIR.joinpath("response.geojson").read_bytes()
        geojson = json.loads(data)
        features = geojson["features"]
        geojson["features"] = features * (MAX_FEATURES_GEO // len(features) + 1)
        assert len(geojson["features"]) >= MAX_FEATURES_GEO
        big_data = json.dumps(geojson).encode()

        with patch("agrobr.utils.geo.logger") as mock_logger:
            gdf = parse_quilombolas_geojson(big_data)

        assert len(gdf) >= MAX_FEATURES_GEO
        mock_logger.warning.assert_called_once()
        call_kwargs = mock_logger.warning.call_args
        assert call_kwargs[0][0] == "incra_quilombolas_geo_truncated"
