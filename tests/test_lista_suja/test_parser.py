from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.lista_suja.models import COLUNAS_SAIDA
from agrobr.lista_suja.parser import PARSER_VERSION, parse_empregadores

_HEADER = [
    "ID",
    "Ano da\nação\nfiscal",
    "UF",
    "Empregador",
    "CNPJ/CPF",
    "Estabelecimento",
    "Trabalhadores\nenvolvidos",
    "CNAE",
    "Decisão\nadministrativa",
    "Inclusão no\nCadastro de\nEmpregadores",
]

_ROWS = [
    ["1", "2023", "MT", "Fazenda X", "12345678901", "Faz. X", "5", "0111", "Sim", "01/01/2023"],
    ["2", "2023", "PA", "Empresa Y", "98765432101", "Emp. Y", "12", "0112", "Sim", "01/02/2023"],
    ["3", "2023", "MA", "Sitio Z", "11122233344", "Sit. Z", "3", "0113", "Sim", "01/03/2023"],
    ["4", "2023", "GO", "Rural W", "55566677788", "Rur. W", "8", "0114", "Sim", "01/04/2023"],
    ["5", "2023", "TO", "Agro V", "99988877766", "Agr. V", "15", "0115", "Sim", "01/05/2023"],
]


def _mock_pdf_data() -> bytes:
    return b"%PDF-mock"


def _make_mock_pdf(header: list[str], rows: list[list[str]]):
    table = [header] + rows
    page = MagicMock()
    page.extract_table.return_value = table
    pdf = MagicMock()
    pdf.pages = [page]
    pdf.close = MagicMock()
    return pdf


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 2


class TestParseEmpregadores:
    def test_valid_pdf(self):
        pdf = _make_mock_pdf(_HEADER, _ROWS)
        with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
            mock_plumber = MagicMock()
            mock_plumber.open.return_value = pdf
            mock_check.return_value = mock_plumber
            df = parse_empregadores(_mock_pdf_data())

        assert len(df) == 5
        assert "empregador" in df.columns
        assert "uf" in df.columns

    def test_empty_pdf(self):
        page = MagicMock()
        page.extract_table.return_value = None
        pdf = MagicMock()
        pdf.pages = [page]
        pdf.close = MagicMock()

        with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
            mock_plumber = MagicMock()
            mock_plumber.open.return_value = pdf
            mock_check.return_value = mock_plumber
            df = parse_empregadores(_mock_pdf_data())

        assert len(df) == 0

    def test_types_numeric(self):
        pdf = _make_mock_pdf(_HEADER, _ROWS)
        with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
            mock_plumber = MagicMock()
            mock_plumber.open.return_value = pdf
            mock_check.return_value = mock_plumber
            df = parse_empregadores(_mock_pdf_data())

        assert pd.api.types.is_numeric_dtype(df["trabalhadores_resgatados"])

    def test_uf_uppercase(self):
        pdf = _make_mock_pdf(_HEADER, _ROWS)
        with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
            mock_plumber = MagicMock()
            mock_plumber.open.return_value = pdf
            mock_check.return_value = mock_plumber
            df = parse_empregadores(_mock_pdf_data())

        for val in df["uf"].dropna():
            if val:
                assert val == val.upper()

    def test_no_columns_raises(self):
        bad_header = ["ID", "foo", "bar"]
        bad_rows = [["1", "x", "y"]]
        pdf = _make_mock_pdf(bad_header, bad_rows)

        with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
            mock_plumber = MagicMock()
            mock_plumber.open.return_value = pdf
            mock_check.return_value = mock_plumber
            with pytest.raises(ParseError):
                parse_empregadores(_mock_pdf_data())

    def test_output_columns_subset_of_schema(self):
        pdf = _make_mock_pdf(_HEADER, _ROWS)
        with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
            mock_plumber = MagicMock()
            mock_plumber.open.return_value = pdf
            mock_check.return_value = mock_plumber
            df = parse_empregadores(_mock_pdf_data())

        for col in df.columns:
            assert col in COLUNAS_SAIDA, f"Unexpected column: {col}"


def _make_pdf_from_tables(tables: list):
    pages = []
    for t in tables:
        page = MagicMock()
        page.extract_table.return_value = t
        pages.append(page)
    pdf = MagicMock()
    pdf.pages = pages
    pdf.close = MagicMock()
    return pdf


def _parse_with_pdf(pdf):
    with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
        mock_plumber = MagicMock()
        mock_plumber.open.return_value = pdf
        mock_check.return_value = mock_plumber
        return parse_empregadores(_mock_pdf_data())


class TestParseEmpregadoresEdgeCases:
    def test_no_header_returns_empty(self):
        df = _parse_with_pdf(_make_pdf_from_tables([[["foo", "bar"], ["1", "2"]]]))
        assert len(df) == 0
        assert list(df.columns) == COLUNAS_SAIDA

    def test_row_with_wrong_column_count_skipped(self):
        df = _parse_with_pdf(_make_pdf_from_tables([[_HEADER, _ROWS[0], ["x", "y"]]]))
        assert len(df) == 1

    def test_multipage_aggregates_rows(self):
        df = _parse_with_pdf(_make_pdf_from_tables([[_HEADER, _ROWS[0]], [_ROWS[1]]]))
        assert len(df) == 2

    def test_empty_first_cell_skipped(self):
        empty_row = [""] + ["x"] * 9
        df = _parse_with_pdf(_make_pdf_from_tables([[_HEADER, empty_row, _ROWS[0]]]))
        assert len(df) == 1

    def test_corrupt_pdf_raises(self):
        with patch("agrobr.lista_suja.parser._check_pdfplumber") as mock_check:
            mock_plumber = MagicMock()
            mock_plumber.open.side_effect = Exception("corrupt")
            mock_check.return_value = mock_plumber
            with pytest.raises(ParseError):
                parse_empregadores(_mock_pdf_data())
