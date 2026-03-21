from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.funai.models import COLUNAS_SAIDA, COLUNAS_SAIDA_GEO, MAX_FEATURES_GEO
from agrobr.funai.parser import PARSER_VERSION, parse_terras_indigenas_csv

CSV_DIR = Path(__file__).parent.parent / "golden_data" / "funai" / "terras_indigenas_sample"
GEO_DIR = Path(__file__).parent.parent / "golden_data" / "funai" / "terras_indigenas_geo_sample"


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1


class TestParseTerrasIndigenasCsv:
    def test_valid_csv(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_terras_indigenas_csv(csv_bytes)

        assert len(df) == 10
        for col in COLUNAS_SAIDA:
            assert col in df.columns, f"Missing column: {col}"

    def test_golden_data_columns(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(CSV_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_terras_indigenas_csv(csv_bytes)

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_area_ha_is_float_positive(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_terras_indigenas_csv(csv_bytes)

        assert pd.api.types.is_float_dtype(df["area_ha"])
        assert (df["area_ha"].dropna() > 0).all()

    def test_uf_is_uppercase(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_terras_indigenas_csv(csv_bytes)

        for val in df["uf"].dropna():
            assert val == val.upper()

    def test_data_atualizacao_is_datetime(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        df = parse_terras_indigenas_csv(csv_bytes)

        assert pd.api.types.is_datetime64_any_dtype(df["data_atualizacao"])

    def test_empty_csv_returns_empty_dataframe(self):
        csv_bytes = b"terrai_codigo,terrai_nome,etnia_nome,municipio_nome,uf_sigla,superficie_perimetro_ha,fase_ti,modalidade_ti,data_atualizacao\n"
        df = parse_terras_indigenas_csv(csv_bytes)

        assert len(df) == 0
        for col in COLUNAS_SAIDA:
            assert col in df.columns

    def test_invalid_csv_raises(self):
        with pytest.raises(ParseError):
            parse_terras_indigenas_csv(b"")

    def test_missing_required_columns_raises(self):
        csv = b"id,nome,valor\n1,teste,100\n"
        with pytest.raises(ParseError, match="Colunas obrigatorias ausentes"):
            parse_terras_indigenas_csv(csv)

    def test_non_null_columns(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(CSV_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_terras_indigenas_csv(csv_bytes)

        for col in expected["non_null_columns"]:
            assert df[col].notna().all(), f"Column {col} has nulls"

    def test_count_matches_golden(self):
        csv_bytes = CSV_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(CSV_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_terras_indigenas_csv(csv_bytes)

        assert len(df) == expected["count"]


gpd = pytest.importorskip("geopandas")


class TestParseTerrasIndigenasGeojson:
    def _parse(self):
        from agrobr.funai.parser import parse_terras_indigenas_geojson

        data = GEO_DIR.joinpath("response.geojson").read_bytes()
        return parse_terras_indigenas_geojson(data)

    def test_valid_geojson(self):
        gdf = self._parse()
        assert len(gdf) >= 10

    def test_columns_match_schema(self):
        gdf = self._parse()
        for col in COLUNAS_SAIDA_GEO:
            assert col in gdf.columns, f"Missing column: {col}"

    def test_geometry_exists(self):
        gdf = self._parse()
        assert "geometry" in gdf.columns

    def test_geometry_is_valid(self):
        gdf = self._parse()
        assert gdf.geometry.is_valid.all()

    def test_crs_4326(self):
        gdf = self._parse()
        assert gdf.crs.to_epsg() == 4326

    def test_area_ha_non_negative(self):
        gdf = self._parse()
        assert (gdf["area_ha"].dropna() >= 0).all()

    def test_uf_uppercase(self):
        gdf = self._parse()
        for val in gdf["uf"].dropna():
            assert val == val.upper()

    def test_empty_features_returns_empty_geodataframe(self):
        from agrobr.funai.parser import parse_terras_indigenas_geojson

        data = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        gdf = parse_terras_indigenas_geojson(data)

        assert len(gdf) == 0
        assert isinstance(gdf, gpd.GeoDataFrame)
        for col in COLUNAS_SAIDA_GEO:
            assert col in gdf.columns

    def test_invalid_json_raises(self):
        from agrobr.funai.parser import parse_terras_indigenas_geojson

        with pytest.raises(ParseError):
            parse_terras_indigenas_geojson(b"not json at all {{{")

    def test_missing_required_columns_raises(self):
        from agrobr.funai.parser import parse_terras_indigenas_geojson

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
            parse_terras_indigenas_geojson(data)

    def test_geopandas_not_installed(self):
        from agrobr.funai.parser import parse_terras_indigenas_geojson

        with (
            patch(
                "agrobr.funai.parser.check_geopandas",
                side_effect=ImportError(
                    "geopandas is required for geo functions. Install with: pip install agrobr[geo]"
                ),
            ),
            pytest.raises(ImportError, match="agrobr\\[geo\\]"),
        ):
            parse_terras_indigenas_geojson(b"{}")

    def test_truncation_warning(self):
        from agrobr.funai.parser import parse_terras_indigenas_geojson

        data = GEO_DIR.joinpath("response.geojson").read_bytes()
        geojson = json.loads(data)
        features = geojson["features"]
        geojson["features"] = features * (MAX_FEATURES_GEO // len(features) + 1)
        assert len(geojson["features"]) >= MAX_FEATURES_GEO
        big_data = json.dumps(geojson).encode()

        with patch("agrobr.funai.parser.logger") as mock_logger:
            gdf = parse_terras_indigenas_geojson(big_data)

        assert len(gdf) >= MAX_FEATURES_GEO
        mock_logger.warning.assert_called_once()
        call_kwargs = mock_logger.warning.call_args
        assert call_kwargs[0][0] == "funai_terras_indigenas_geo_truncated"

    def test_data_atualizacao_is_datetime(self):
        gdf = self._parse()
        assert pd.api.types.is_datetime64_any_dtype(gdf["data_atualizacao"])

    def test_non_null_columns(self):
        expected = json.loads(GEO_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        gdf = self._parse()
        for col in expected["non_null_columns"]:
            assert gdf[col].notna().all(), f"Column {col} has nulls"
