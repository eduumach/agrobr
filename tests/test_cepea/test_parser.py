"""Tests for CEPEA parser."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from agrobr.cepea.parsers.v1 import PRACAS, CepeaParserV1
from agrobr.exceptions import ParseError


class TestCepeaParserV1:
    """Tests for CepeaParserV1."""

    def setup_method(self):
        self.parser = CepeaParserV1()

    def test_can_parse_with_valid_html(self, sample_html_cepea):
        can_parse, confidence = self.parser.can_parse(sample_html_cepea)
        assert can_parse is True
        assert confidence >= 0.4

    def test_can_parse_with_empty_html(self, sample_html_empty):
        can_parse, confidence = self.parser.can_parse(sample_html_empty)
        assert can_parse is False or confidence < 0.4

    def test_parse_extracts_indicadores(self, sample_html_cepea):
        indicadores = self.parser.parse(sample_html_cepea, "soja")

        assert len(indicadores) == 2

        first = indicadores[0]
        assert first.data == date(2024, 2, 1)
        assert first.valor == Decimal("145.50")
        assert first.produto == "soja"
        assert first.unidade == "BRL/sc60kg"
        assert first.praca == "Paranaguá/PR"

    def test_parse_raises_on_empty_table(self, sample_html_empty):
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(sample_html_empty, "soja")

        assert "No tables found" in str(exc_info.value)

    def test_parse_date_formats(self):
        assert self.parser._parse_date("01/02/2024") == date(2024, 2, 1)
        assert self.parser._parse_date("01-02-2024") == date(2024, 2, 1)
        assert self.parser._parse_date("2024-02-01") == date(2024, 2, 1)
        assert self.parser._parse_date("invalid") is None

    def test_parse_decimal_formats(self):
        assert self.parser._parse_decimal("145,50") == Decimal("145.50")
        assert self.parser._parse_decimal("1.234,56") == Decimal("1234.56")
        assert self.parser._parse_decimal("R$ 145,50") == Decimal("145.50")
        assert self.parser._parse_decimal("invalid") is None
        assert self.parser._parse_decimal("-10") is None

    def test_detect_unidade_soja(self):
        unidade = self.parser._detect_unidade("soja", [])
        assert unidade == "BRL/sc60kg"

    def test_detect_unidade_boi(self):
        unidade = self.parser._detect_unidade("boi", [])
        assert unidade == "BRL/@"

    def test_parser_metadata(self):
        assert self.parser.version == 1
        assert self.parser.source == "cepea"
        assert self.parser.valid_from == date(2024, 1, 1)
        assert self.parser.valid_until is None

    def test_parse_excludes_usd_column(self):
        html = """
        <html><body>
        <table class="indicador" id="imagenet-indicador1">
            <tr>
                <th></th>
                <th>Valor R$*</th>
                <th>Var./Dia</th>
                <th>Var./Mês</th>
                <th>Valor US$*</th>
            </tr>
            <tr>
                <td>10/03/2024</td>
                <td>145,50</td>
                <td>+0,5%</td>
                <td>+1,2%</td>
                <td>28,50</td>
            </tr>
        </table>
        <p>Indicador CEPEA/ESALQ</p>
        </body></html>
        """
        indicadores = self.parser.parse(html, "soja")
        assert len(indicadores) == 1
        assert indicadores[0].valor == Decimal("145.50")

    def test_parse_var_dia_not_matched_as_date(self):
        html = """
        <html><body>
        <table class="indicador" id="imagenet-indicador1">
            <tr>
                <th></th>
                <th>Valor R$*</th>
                <th>Var./Dia</th>
                <th>Var./Mês</th>
                <th>Valor US$*</th>
            </tr>
            <tr>
                <td>15/03/2024</td>
                <td>130,00</td>
                <td>+0,2%</td>
                <td>+0,8%</td>
                <td>25,00</td>
            </tr>
        </table>
        <p>Indicador CEPEA/ESALQ</p>
        </body></html>
        """
        indicadores = self.parser.parse(html, "milho")
        assert indicadores[0].data == date(2024, 3, 15)

    def test_parse_populates_praca(self):
        html = """
        <html><body>
        <table class="indicador" id="imagenet-indicador1">
            <tr><th></th><th>Valor R$*</th><th>Var./Dia</th><th>Var./Mês</th><th>Valor US$*</th></tr>
            <tr><td>01/01/2024</td><td>100,00</td><td>+0,1%</td><td>+0,5%</td><td>20,00</td></tr>
        </table>
        <p>Indicador CEPEA/ESALQ</p>
        </body></html>
        """
        indicadores = self.parser.parse(html, "soja")
        assert indicadores[0].praca == PRACAS["soja"]

    def test_parse_unknown_produto_praca_none(self):
        html = """
        <html><body>
        <table class="indicador" id="imagenet-indicador1">
            <tr><th></th><th>Valor R$*</th><th>Var./Dia</th><th>Var./Mês</th><th>Valor US$*</th></tr>
            <tr><td>01/01/2024</td><td>100,00</td><td>+0,1%</td><td>+0,5%</td><td>20,00</td></tr>
        </table>
        <p>Indicador CEPEA/ESALQ</p>
        </body></html>
        """
        indicadores = self.parser.parse(html, "desconhecido")
        assert indicadores[0].praca is None
