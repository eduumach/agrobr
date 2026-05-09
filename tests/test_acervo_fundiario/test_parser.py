from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from agrobr.acervo_fundiario import parser
from agrobr.acervo_fundiario.models import (
    ASSENTAMENTOS_COLUNAS_SAIDA,
    SIGEF_COLUNAS_SAIDA,
    SIGEF_COLUNAS_SAIDA_GEO,
    SNCI_COLUNAS_SAIDA,
)
from agrobr.exceptions import ParseError


class TestParseSigef:
    def test_columns_match_contract(self, synthetic_sigef_zip):
        df = parser.parse_sigef(synthetic_sigef_zip)
        assert list(df.columns) == SIGEF_COLUNAS_SAIDA

    def test_uf_id_mapped_to_sigla(self, synthetic_sigef_zip):
        df = parser.parse_sigef(synthetic_sigef_zip)
        assert df["uf"].unique().tolist() == ["ES"]

    def test_uf_id_dropped(self, synthetic_sigef_zip):
        df = parser.parse_sigef(synthetic_sigef_zip)
        assert "uf_id" not in df.columns

    def test_dates_are_datetime(self, synthetic_sigef_zip):
        df = parser.parse_sigef(synthetic_sigef_zip)
        assert pd.api.types.is_datetime64_any_dtype(df["data_submissao"])
        assert pd.api.types.is_datetime64_any_dtype(df["data_aprovacao"])

    def test_encoding_latin1_preserves_accents(self, synthetic_sigef_zip):
        df = parser.parse_sigef(synthetic_sigef_zip)
        assert all("São" in v for v in df["nome_area"])

    def test_row_count(self, synthetic_sigef_zip):
        df = parser.parse_sigef(synthetic_sigef_zip)
        assert len(df) == 5


class TestParseSigefGeo:
    def test_returns_geodataframe(self, synthetic_sigef_zip):
        gpd = pytest.importorskip("geopandas")
        gdf = parser.parse_sigef_geo(synthetic_sigef_zip)
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_columns_include_geometry(self, synthetic_sigef_zip):
        gdf = parser.parse_sigef_geo(synthetic_sigef_zip)
        assert list(gdf.columns) == SIGEF_COLUNAS_SAIDA_GEO

    def test_crs_sirgas_2000(self, synthetic_sigef_zip):
        gdf = parser.parse_sigef_geo(synthetic_sigef_zip)
        assert str(gdf.crs).upper().endswith("4674")

    def test_geometries_valid(self, synthetic_sigef_zip):
        gdf = parser.parse_sigef_geo(synthetic_sigef_zip)
        assert gdf.geometry.is_valid.all()

    def test_bbox_filters(self, synthetic_sigef_zip):
        gdf_full = parser.parse_sigef_geo(synthetic_sigef_zip)
        gdf_filtered = parser.parse_sigef_geo(
            synthetic_sigef_zip, bbox=(-40.4, -20.5, -40.2, -19.5)
        )
        assert len(gdf_filtered) < len(gdf_full)


class TestParseSnci:
    def test_columns_match_contract(self, synthetic_snci_zip):
        df = parser.parse_snci(synthetic_snci_zip)
        assert list(df.columns) == SNCI_COLUNAS_SAIDA

    def test_uf_already_sigla(self, synthetic_snci_zip):
        df = parser.parse_snci(synthetic_snci_zip)
        assert df["uf"].unique().tolist() == ["GO"]

    def test_dates_are_datetime(self, synthetic_snci_zip):
        df = parser.parse_snci(synthetic_snci_zip)
        assert pd.api.types.is_datetime64_any_dtype(df["data_certificacao"])

    def test_area_is_numeric(self, synthetic_snci_zip):
        df = parser.parse_snci(synthetic_snci_zip)
        assert pd.api.types.is_numeric_dtype(df["area_peca_tecnica"])


class TestParseAssentamentos:
    def test_columns_match_contract(self, synthetic_assentamentos_zip):
        df = parser.parse_assentamentos(synthetic_assentamentos_zip)
        assert list(df.columns) == ASSENTAMENTOS_COLUNAS_SAIDA

    def test_no_filter_returns_all_rows(self, synthetic_assentamentos_zip):
        df = parser.parse_assentamentos(synthetic_assentamentos_zip)
        assert len(df) == 4

    def test_uf_filter_returns_subset(self, synthetic_assentamentos_zip):
        df = parser.parse_assentamentos(synthetic_assentamentos_zip, uf="MG")
        assert len(df) == 2
        assert df["uf"].unique().tolist() == ["MG"]

    def test_uf_filter_unknown_returns_empty(self, synthetic_assentamentos_zip):
        df = parser.parse_assentamentos(synthetic_assentamentos_zip, uf="SP")
        assert len(df) == 0

    def test_dirty_uf_data_preserved_not_filtered(self, synthetic_assentamentos_zip):
        df = parser.parse_assentamentos(synthetic_assentamentos_zip)
        assert "MB" in df["uf"].values


class TestSchemaDriftDetection:
    def test_missing_required_raises(self, tmp_path: Path):
        pytest.importorskip("geopandas")
        import geopandas as gpd
        import pyogrio
        from shapely.geometry import Polygon

        df = pd.DataFrame({"some_col": ["x"]})
        gdf = gpd.GeoDataFrame(df, geometry=[Polygon([(0, 0), (1, 0), (1, 1)])], crs="EPSG:4674")
        shp_dir = tmp_path / "broken_layer"
        shp_dir.mkdir()
        pyogrio.write_dataframe(gdf, shp_dir / "broken.shp", encoding="latin1")
        zip_path = tmp_path / "broken.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for f in shp_dir.iterdir():
                zf.write(f, f.name)

        with pytest.raises(ParseError, match="Colunas obrigatorias"):
            parser.parse_sigef(zip_path)


class TestParserVersion:
    def test_parser_version_is_2(self):
        assert parser.PARSER_VERSION == 2
