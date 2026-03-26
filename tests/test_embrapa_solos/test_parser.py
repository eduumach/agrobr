from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from agrobr.embrapa_solos.parser import PARSER_VERSION, parse_mapa_csv, parse_perfis_csv

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "golden_data" / "embrapa_solos"


@pytest.fixture
def perfis_pages():
    return [(GOLDEN_DIR / "perfis_sample.csv").read_bytes()]


@pytest.fixture
def mapa_pages():
    return [(GOLDEN_DIR / "mapa_sample.csv").read_bytes()]


class TestParsePerfis:
    def test_columns(self, perfis_pages):
        df = parse_perfis_csv(perfis_pages)
        assert "uf" in df.columns
        assert "ph_h2o" in df.columns
        assert "latitude" in df.columns

    def test_row_count(self, perfis_pages):
        df = parse_perfis_csv(perfis_pages)
        assert len(df) == 10

    def test_numeric_coercion(self, perfis_pages):
        df = parse_perfis_csv(perfis_pages)
        assert pd.api.types.is_numeric_dtype(df["latitude"])
        assert pd.api.types.is_numeric_dtype(df["ph_h2o"])

    def test_uf_uppercase(self, perfis_pages):
        df = parse_perfis_csv(perfis_pages)
        for uf in df["uf"].dropna():
            assert uf == uf.upper()

    def test_empty_pages(self):
        df = parse_perfis_csv([])
        assert df.empty


class TestParseMapa:
    def test_columns(self, mapa_pages):
        df = parse_mapa_csv(mapa_pages)
        assert "classe_dom" in df.columns
        assert "area_km2" in df.columns
        assert "fid" in df.columns

    def test_row_count(self, mapa_pages):
        df = parse_mapa_csv(mapa_pages)
        assert len(df) == 10

    def test_area_numeric(self, mapa_pages):
        df = parse_mapa_csv(mapa_pages)
        assert pd.api.types.is_numeric_dtype(df["area_km2"])

    def test_empty_pages(self):
        df = parse_mapa_csv([])
        assert df.empty


def test_parser_version():
    assert PARSER_VERSION == 1
