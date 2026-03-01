from __future__ import annotations

import math

import pytest

from agrobr.normalize.numeric import parse_numeric_br, safe_float


class TestGuards:
    def test_none(self):
        assert parse_numeric_br(None) is None

    def test_empty_string(self):
        assert parse_numeric_br("") is None

    def test_dash(self):
        assert parse_numeric_br("-") is None

    def test_whitespace_only(self):
        assert parse_numeric_br("   ") is None


class TestPassthrough:
    def test_int(self):
        assert parse_numeric_br(42) == 42.0

    def test_float(self):
        assert parse_numeric_br(42.5) == 42.5

    def test_zero_int(self):
        assert parse_numeric_br(0) == 0.0

    def test_bool_true(self):
        assert parse_numeric_br(True) == 1.0

    def test_bool_false(self):
        assert parse_numeric_br(False) == 0.0

    def test_nan_passthrough(self):
        result = parse_numeric_br(float("nan"))
        assert result is not None
        assert math.isnan(result)


class TestFormatoBR:
    def test_milhar_e_decimal(self):
        assert parse_numeric_br("1.234,56") == 1234.56

    def test_virgula_decimal_sem_milhar(self):
        assert parse_numeric_br("1234,56") == 1234.56

    def test_negativo_br(self):
        assert parse_numeric_br("-1.234,56") == -1234.56

    def test_multiplos_grupos_milhar(self):
        assert parse_numeric_br("1.234.567.890,99") == 1234567890.99

    def test_decimal_br_pequeno(self):
        assert parse_numeric_br("0,001") == 0.001

    def test_valor_real_anp(self):
        assert parse_numeric_br("3517,6") == 3517.6

    def test_valor_real_anp_milhar(self):
        assert parse_numeric_br("500.000,50") == pytest.approx(500000.50)


class TestStringsSimples:
    def test_inteiro_string(self):
        assert parse_numeric_br("50000") == 50000.0

    def test_zero_string(self):
        assert parse_numeric_br("0") == 0.0

    def test_negativo_dot(self):
        assert parse_numeric_br("-42.5") == -42.5

    def test_formato_us_passthrough(self):
        assert parse_numeric_br("1234.56") == 1234.56


class TestWhitespace:
    def test_espacos_ao_redor(self):
        assert parse_numeric_br("  1234,56  ") == 1234.56

    def test_espaco_interno_milhar(self):
        assert parse_numeric_br("1 234,56") == 1234.56


class TestLimitacoes:
    def test_us_thousands_interpreted_as_br_decimal(self):
        assert parse_numeric_br("1,234") == 1.234

    def test_nbsp_not_stripped(self):
        assert parse_numeric_br("1\u00a0234,56") is None


class TestInvalidos:
    def test_texto(self):
        assert parse_numeric_br("abc") is None

    def test_en_dash(self):
        assert parse_numeric_br("\u2013") is None

    def test_em_dash(self):
        assert parse_numeric_br("\u2014") is None

    def test_so_virgula(self):
        assert parse_numeric_br(",") is None

    def test_so_ponto(self):
        assert parse_numeric_br(".") is None

    def test_formato_us_milhares(self):
        assert parse_numeric_br("1,234,567") is None


class TestSafeFloatGuards:
    def test_none(self):
        assert safe_float(None) is None

    def test_nan_as_none(self):
        assert safe_float(float("nan")) is None

    def test_nan_passthrough(self):
        result = safe_float(float("nan"), nan_as_none=False)
        assert result is not None
        assert math.isnan(result)

    def test_int(self):
        assert safe_float(42) == 42.0

    def test_float(self):
        assert safe_float(3.14) == 3.14

    def test_empty_string(self):
        assert safe_float("") is None

    def test_whitespace(self):
        assert safe_float("   ") is None


class TestSafeFloatNullMarkers:
    @pytest.mark.parametrize(
        "marker", ["-", "\u2013", "\u2014", "...", "n.d.", "n/d", "nd", "n.d", "*"]
    )
    def test_default_markers(self, marker):
        assert safe_float(marker) is None

    def test_custom_markers(self):
        assert safe_float("N/A", null_markers=frozenset({"n/a"})) is None

    def test_custom_markers_numeric_sentinel(self):
        assert safe_float("99", null_markers=frozenset({"99"})) is None
        assert safe_float("99") == 99.0


class TestSafeFloatStrip:
    def test_strip_percent(self):
        assert safe_float("85,5%", strip="%") == 85.5

    def test_strip_currency(self):
        assert safe_float("R$1.234,56", strip=("R$", "%")) == 1234.56

    def test_strip_parens_asterisk(self):
        assert safe_float("(123,4)*", strip=("(", ")", "*")) == 123.4

    def test_no_strip_default(self):
        assert safe_float("100") == 100.0


class TestSafeFloatZeroAsNone:
    def test_zero_float(self):
        assert safe_float(0.0, treat_zero_as_none=True) is None

    def test_zero_int(self):
        assert safe_float(0, treat_zero_as_none=True) is None

    def test_zero_string(self):
        assert safe_float("0", treat_zero_as_none=True) is None

    def test_zero_preserved_by_default(self):
        assert safe_float(0) == 0.0
        assert safe_float("0") == 0.0


class TestSafeFloatBRFormat:
    def test_comma_and_dot(self):
        assert safe_float("1.234,56") == 1234.56

    def test_comma_only(self):
        assert safe_float("1234,56") == 1234.56

    def test_multiple_dots(self):
        assert safe_float("1.234.567") == 1234567.0

    def test_abiove_3digit_heuristic(self):
        assert safe_float("150.000") == 150000.0
        assert safe_float("12.500") == 12500.0

    def test_decimal_passthrough_2digits(self):
        assert safe_float("3.14") == 3.14

    def test_decimal_passthrough_4digits(self):
        assert safe_float("3.1416") == 3.1416

    def test_spaces_stripped(self):
        assert safe_float("  1.234,56  ") == 1234.56

    def test_internal_spaces(self):
        assert safe_float("1 234,56") == 1234.56


class TestSafeFloatInvalid:
    def test_text(self):
        assert safe_float("abc") is None

    def test_only_comma(self):
        assert safe_float(",") is None

    def test_only_dot(self):
        assert safe_float(".") is None
