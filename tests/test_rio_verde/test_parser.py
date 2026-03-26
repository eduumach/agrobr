from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.rio_verde.parser import PARSER_VERSION, parse_ensaio_soja_from_text

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "golden_data" / "rio_verde"


@pytest.fixture
def golden_data():
    with open(GOLDEN_DIR / "ensaio_soja_pages.json", encoding="utf-8") as f:
        return json.load(f)


class TestParseEnsaioSoja:
    def test_golden_columns(self, golden_data):
        df = parse_ensaio_soja_from_text(golden_data["pages"], golden_data["safra"])
        expected = [
            "safra",
            "empresa",
            "cultivar",
            "grupo_maturacao",
            "ciclo_dias",
            "produtividade_1_epoca_sc_ha",
            "produtividade_2_epoca_sc_ha",
            "produtividade_3_epoca_sc_ha",
            "produtividade_4_epoca_sc_ha",
            "produtividade_media_sc_ha",
        ]
        assert list(df.columns) == expected

    def test_golden_row_count(self, golden_data):
        df = parse_ensaio_soja_from_text(golden_data["pages"], golden_data["safra"])
        assert len(df) > 50

    def test_safra_column(self, golden_data):
        df = parse_ensaio_soja_from_text(golden_data["pages"], golden_data["safra"])
        assert all(df["safra"] == "2025/2026")

    def test_numeric_produtividade(self, golden_data):
        df = parse_ensaio_soja_from_text(golden_data["pages"], golden_data["safra"])
        assert pd.api.types.is_numeric_dtype(df["produtividade_media_sc_ha"])
        assert pd.api.types.is_numeric_dtype(df["ciclo_dias"])

    def test_media_in_range(self, golden_data):
        df = parse_ensaio_soja_from_text(golden_data["pages"], golden_data["safra"])
        medias = df["produtividade_media_sc_ha"].dropna()
        assert all(medias > 30)
        assert all(medias < 150)

    def test_empty_pages_raises(self):
        with pytest.raises(ParseError):
            parse_ensaio_soja_from_text([], "2025/2026")

    def test_no_data_pages_raises(self):
        with pytest.raises(ParseError):
            parse_ensaio_soja_from_text(["no data here"], "2025/2026")


_DATA_LINE = "Brasmax BRMX Guepardo IPRO 6.7 7.1 103 97,9 98,8 92,6 84,7 93,5"


class TestSectionDetectionResilience:
    def test_case_insensitive_entry(self):
        pages = ["competição de cultivares de SOJA\n" + _DATA_LINE]
        df = parse_ensaio_soja_from_text(pages, "2025/2026")
        assert len(df) == 1

    def test_accent_free_entry(self):
        pages = ["Competicao de Cultivares de Soja\n" + _DATA_LINE]
        df = parse_ensaio_soja_from_text(pages, "2025/2026")
        assert len(df) == 1

    def test_resultados_midline_no_exit(self):
        pages = [
            "Competição de Cultivares de Soja\n"
            + _DATA_LINE
            + "\n"
            + "Tabela com Resultados parciais da safra\n"
            + _DATA_LINE.replace("Guepardo", "Ativa")
        ]
        df = parse_ensaio_soja_from_text(pages, "2025/2026")
        assert len(df) == 2


def test_parser_version():
    assert PARSER_VERSION == 1
