from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.rnc.parser import PARSER_VERSION, parse_protegidas_csv, parse_registradas_csv

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "golden_data" / "rnc"


@pytest.fixture
def registradas_bytes():
    return (GOLDEN_DIR / "registradas_sample.csv").read_bytes()


@pytest.fixture
def protegidas_bytes():
    return (GOLDEN_DIR / "protegidas_sample.csv").read_bytes()


class TestParseRegistradasCsv:
    def test_golden_columns(self, registradas_bytes):
        df = parse_registradas_csv(registradas_bytes)
        expected = [
            "cultivar",
            "nome_comum",
            "nome_cientifico",
            "grupo",
            "situacao",
            "nr_formulario",
            "nr_registro",
            "data_registro",
            "data_validade",
            "mantenedor",
        ]
        assert list(df.columns) == expected

    def test_golden_row_count(self, registradas_bytes):
        df = parse_registradas_csv(registradas_bytes)
        assert len(df) == 25

    def test_dates_are_datetime(self, registradas_bytes):
        df = parse_registradas_csv(registradas_bytes)
        assert pd.api.types.is_datetime64_any_dtype(df["data_registro"])
        assert pd.api.types.is_datetime64_any_dtype(df["data_validade"])

    def test_strings_are_stripped(self, registradas_bytes):
        df = parse_registradas_csv(registradas_bytes)
        for col in ["cultivar", "nome_comum", "mantenedor"]:
            values = df[col].dropna()
            if len(values) > 0:
                assert not any(v != v.strip() for v in values)

    def test_empty_csv_raises(self):
        with pytest.raises(ParseError):
            parse_registradas_csv(b"")

    def test_missing_columns_raises(self):
        bad_csv = b"FOO,BAR\n1,2\n"
        with pytest.raises(ParseError, match="ausentes"):
            parse_registradas_csv(bad_csv)


class TestParseProtegidasCsv:
    def test_golden_columns(self, protegidas_bytes):
        df = parse_protegidas_csv(protegidas_bytes)
        expected = [
            "cultivar",
            "nome_cientifico",
            "nome_comum",
            "nr_processo",
            "situacao",
            "nr_certificado",
            "inicio_protecao",
            "termino_protecao",
            "titular",
            "representante_legal",
            "melhoristas",
        ]
        assert list(df.columns) == expected

    def test_golden_row_count(self, protegidas_bytes):
        df = parse_protegidas_csv(protegidas_bytes)
        assert len(df) == 25

    def test_dates_are_datetime(self, protegidas_bytes):
        df = parse_protegidas_csv(protegidas_bytes)
        assert pd.api.types.is_datetime64_any_dtype(df["inicio_protecao"])
        assert pd.api.types.is_datetime64_any_dtype(df["termino_protecao"])


def test_parser_version():
    assert PARSER_VERSION == 1
