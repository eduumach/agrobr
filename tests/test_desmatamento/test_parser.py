from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from agrobr.desmatamento.models import (
    COLUNAS_SAIDA_DETER_GEO,
    COLUNAS_SAIDA_PRODES_GEO,
    MAX_FEATURES_GEO,
)
from agrobr.desmatamento.parser import PARSER_VERSION, parse_deter_csv, parse_prodes_csv
from agrobr.exceptions import ParseError

PRODES_DIR = Path(__file__).parent.parent / "golden_data" / "desmatamento" / "prodes_sample"
PRODES_GEO_DIR = Path(__file__).parent.parent / "golden_data" / "desmatamento" / "prodes_geo_sample"
DETER_DIR = Path(__file__).parent.parent / "golden_data" / "desmatamento" / "deter_sample"
DETER_GEO_DIR = Path(__file__).parent.parent / "golden_data" / "desmatamento" / "deter_geo_sample"


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1


class TestParseProdesCsv:
    def test_valid_csv(self):
        csv_bytes = PRODES_DIR.joinpath("response.csv").read_bytes()
        df = parse_prodes_csv(csv_bytes, "Cerrado")

        assert len(df) >= 5
        assert "ano" in df.columns
        assert "area_km2" in df.columns
        assert "uf" in df.columns
        assert "bioma" in df.columns

    def test_golden_data_columns(self):
        csv_bytes = PRODES_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(PRODES_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_prodes_csv(csv_bytes, "Cerrado")

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_golden_data_ufs(self):
        csv_bytes = PRODES_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(PRODES_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_prodes_csv(csv_bytes, "Cerrado")

        ufs = sorted(df["uf"].dropna().unique().tolist())
        for u in expected["ufs_expected"]:
            assert u in ufs, f"Missing uf: {u}"

    def test_area_non_negative(self):
        csv_bytes = PRODES_DIR.joinpath("response.csv").read_bytes()
        df = parse_prodes_csv(csv_bytes, "Cerrado")

        assert (df["area_km2"] >= 0).all()

    def test_bioma_column(self):
        csv_bytes = PRODES_DIR.joinpath("response.csv").read_bytes()
        df = parse_prodes_csv(csv_bytes, "Cerrado")

        assert (df["bioma"] == "Cerrado").all()

    def test_ano_is_numeric(self):
        csv_bytes = PRODES_DIR.joinpath("response.csv").read_bytes()
        df = parse_prodes_csv(csv_bytes, "Cerrado")

        assert pd.api.types.is_integer_dtype(df["ano"])

    def test_empty_csv_raises(self):
        with pytest.raises(ParseError):
            parse_prodes_csv(b"year,area_km,state\n", "Cerrado")

    def test_invalid_csv_raises(self):
        with pytest.raises(ParseError):
            parse_prodes_csv(b"invalid data", "Cerrado")

    def test_missing_columns_raises(self):
        csv = b"id,nome,valor\n1,teste,100\n"
        with pytest.raises(ParseError, match="Colunas obrigatorias ausentes"):
            parse_prodes_csv(csv, "Cerrado")


class TestParseDeterCsv:
    def test_valid_csv(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        df = parse_deter_csv(csv_bytes, "Amazônia")

        assert len(df) >= 5
        assert "data" in df.columns
        assert "area_km2" in df.columns
        assert "uf" in df.columns
        assert "classe" in df.columns
        assert "bioma" in df.columns

    def test_golden_data_columns(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(DETER_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_deter_csv(csv_bytes, "Amazônia")

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_golden_data_ufs(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(DETER_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_deter_csv(csv_bytes, "Amazônia")

        ufs = sorted(df["uf"].dropna().unique().tolist())
        for u in expected["ufs_expected"]:
            assert u in ufs, f"Missing uf: {u}"

    def test_golden_data_classes(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        expected = json.loads(DETER_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        df = parse_deter_csv(csv_bytes, "Amazônia")

        classes = sorted(df["classe"].dropna().unique().tolist())
        for c in expected["classes_expected"]:
            assert c in classes, f"Missing class: {c}"

    def test_area_non_negative(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        df = parse_deter_csv(csv_bytes, "Amazônia")

        assert (df["area_km2"] >= 0).all()

    def test_bioma_column(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        df = parse_deter_csv(csv_bytes, "Amazônia")

        assert (df["bioma"] == "Amazônia").all()

    def test_data_column_is_date(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        df = parse_deter_csv(csv_bytes, "Amazônia")

        for val in df["data"].dropna():
            assert hasattr(val, "year")

    def test_municipio_id_is_ibge(self):
        csv_bytes = DETER_DIR.joinpath("response.csv").read_bytes()
        df = parse_deter_csv(csv_bytes, "Amazônia")

        valid_ids = df["municipio_id"].dropna()
        assert len(valid_ids) > 0
        for mid in valid_ids:
            assert mid > 1000000

    def test_empty_csv_raises(self):
        with pytest.raises(ParseError):
            parse_deter_csv(b"view_date,areamunkm,uf\n", "Amazônia")

    def test_invalid_csv_raises(self):
        with pytest.raises(ParseError):
            parse_deter_csv(b"invalid data", "Amazônia")

    def test_missing_columns_raises(self):
        csv = b"id,nome,valor\n1,teste,100\n"
        with pytest.raises(ParseError, match="Colunas obrigatorias ausentes"):
            parse_deter_csv(csv, "Amazônia")


gpd = pytest.importorskip("geopandas")


class TestParseDeterGeojson:
    def _parse(self, bioma: str = "Amazônia"):
        from agrobr.desmatamento.parser import parse_deter_geojson

        data = DETER_GEO_DIR.joinpath("response.geojson").read_bytes()
        return parse_deter_geojson(data, bioma)

    def test_valid_geojson(self):
        gdf = self._parse()
        assert len(gdf) >= 5
        assert "data" in gdf.columns
        assert "area_km2" in gdf.columns
        assert "uf" in gdf.columns
        assert "classe" in gdf.columns
        assert "bioma" in gdf.columns

    def test_output_columns_match_schema(self):
        gdf = self._parse()
        for col in COLUNAS_SAIDA_DETER_GEO:
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

    def test_area_non_negative(self):
        gdf = self._parse()
        assert (gdf["area_km2"] >= 0).all()

    def test_bioma_column(self):
        gdf = self._parse()
        assert (gdf["bioma"] == "Amazônia").all()

    def test_data_column_is_date(self):
        gdf = self._parse()
        for val in gdf["data"].dropna():
            assert hasattr(val, "year")

    def test_municipio_id_is_ibge(self):
        gdf = self._parse()
        valid_ids = gdf["municipio_id"].dropna()
        assert len(valid_ids) > 0
        for mid in valid_ids:
            assert mid > 1000000

    def test_empty_geojson_raises(self):
        from agrobr.desmatamento.parser import parse_deter_geojson

        data = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        with pytest.raises(ParseError):
            parse_deter_geojson(data, "Amazônia")

    def test_invalid_json_raises(self):
        from agrobr.desmatamento.parser import parse_deter_geojson

        with pytest.raises(ParseError):
            parse_deter_geojson(b"not json at all {{{", "Amazônia")

    def test_missing_columns_raises(self):
        from agrobr.desmatamento.parser import parse_deter_geojson

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
            parse_deter_geojson(data, "Amazônia")

    def test_geopandas_not_installed(self):
        from agrobr.desmatamento.parser import parse_deter_geojson

        with (
            patch(
                "agrobr.desmatamento.parser.check_geopandas",
                side_effect=ImportError(
                    "geopandas is required for deter_geo(). Install with: pip install agrobr[geo]"
                ),
            ),
            pytest.raises(ImportError, match="agrobr\\[geo\\]"),
        ):
            parse_deter_geojson(b"{}", "Amazônia")

    def test_truncation_warning(self):
        from agrobr.desmatamento.parser import parse_deter_geojson

        data = DETER_GEO_DIR.joinpath("response.geojson").read_bytes()
        geojson = json.loads(data)
        features = geojson["features"]
        geojson["features"] = features * (MAX_FEATURES_GEO // len(features) + 1)
        assert len(geojson["features"]) >= MAX_FEATURES_GEO
        big_data = json.dumps(geojson).encode()

        with patch("agrobr.desmatamento.parser.logger") as mock_logger:
            gdf = parse_deter_geojson(big_data, "Amazônia")

        assert len(gdf) >= MAX_FEATURES_GEO
        mock_logger.warning.assert_called_once()
        call_kwargs = mock_logger.warning.call_args
        assert call_kwargs[0][0] == "desmatamento_deter_geo_truncated"


class TestParseProdesGeojson:
    def _parse(self, bioma: str = "Cerrado"):
        from agrobr.desmatamento.parser import parse_prodes_geojson

        data = PRODES_GEO_DIR.joinpath("response.geojson").read_bytes()
        return parse_prodes_geojson(data, bioma)

    def test_valid_geojson(self):
        gdf = self._parse()
        assert len(gdf) >= 5
        assert "ano" in gdf.columns
        assert "area_km2" in gdf.columns
        assert "uf" in gdf.columns
        assert "bioma" in gdf.columns

    def test_output_columns_match_schema(self):
        gdf = self._parse()
        for col in COLUNAS_SAIDA_PRODES_GEO:
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

    def test_area_non_negative(self):
        gdf = self._parse()
        assert (gdf["area_km2"] >= 0).all()

    def test_bioma_column(self):
        gdf = self._parse()
        assert (gdf["bioma"] == "Cerrado").all()

    def test_ano_is_numeric(self):
        gdf = self._parse()
        import pandas as pd

        assert pd.api.types.is_integer_dtype(gdf["ano"])

    def test_empty_geojson_raises(self):
        from agrobr.desmatamento.parser import parse_prodes_geojson

        data = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        with pytest.raises(ParseError):
            parse_prodes_geojson(data, "Cerrado")

    def test_invalid_json_raises(self):
        from agrobr.desmatamento.parser import parse_prodes_geojson

        with pytest.raises(ParseError):
            parse_prodes_geojson(b"not json at all {{{", "Cerrado")

    def test_missing_columns_raises(self):
        from agrobr.desmatamento.parser import parse_prodes_geojson

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
            parse_prodes_geojson(data, "Cerrado")

    def test_geopandas_not_installed(self):
        from agrobr.desmatamento.parser import parse_prodes_geojson

        with (
            patch(
                "agrobr.desmatamento.parser.check_geopandas",
                side_effect=ImportError(
                    "geopandas is required for geo functions. Install with: pip install agrobr[geo]"
                ),
            ),
            pytest.raises(ImportError, match="agrobr\\[geo\\]"),
        ):
            parse_prodes_geojson(b"{}", "Cerrado")

    def test_truncation_warning(self):
        from agrobr.desmatamento.parser import parse_prodes_geojson

        data = PRODES_GEO_DIR.joinpath("response.geojson").read_bytes()
        geojson = json.loads(data)
        features = geojson["features"]
        geojson["features"] = features * (MAX_FEATURES_GEO // len(features) + 1)
        assert len(geojson["features"]) >= MAX_FEATURES_GEO
        big_data = json.dumps(geojson).encode()

        with patch("agrobr.desmatamento.parser.logger") as mock_logger:
            gdf = parse_prodes_geojson(big_data, "Cerrado")

        assert len(gdf) >= MAX_FEATURES_GEO
        mock_logger.warning.assert_called_once()
        call_kwargs = mock_logger.warning.call_args
        assert call_kwargs[0][0] == "desmatamento_prodes_geo_truncated"
