from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.lista_suja.models import COLUNAS_SAIDA
from agrobr.lista_suja.parser import PARSER_VERSION, parse_empregadores

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "lista_suja" / "empregadores_sample"


def _make_xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "EMPREGADOR": ["Fazenda X", "Empresa Y", "Sitio Z", "Rural W", "Agro V"],
            "CPF/CNPJ": [
                "12345678901",
                "98765432101",
                "11122233344",
                "55566677788",
                "99988877766",
            ],
            "ESTABELECIMENTO": ["Faz. X", "Emp. Y", "Sit. Z", "Rur. W", "Agr. V"],
            "UF": ["MT", "PA", "MA", "GO", "TO"],
            "MUNICÍPIO": ["Sinop", "Maraba", "Balsas", "Jatai", "Palmas"],
            "CNAE": ["0111", "0112", "0113", "0114", "0115"],
            "DATA DA INCLUSÃO": pd.to_datetime(
                ["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01"]
            ),
            "TRABALHADORES ENVOLVIDOS": [5, 12, 3, 8, 15],
        }
    )


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1


class TestParseEmpregadores:
    def test_valid_xlsx(self):
        xlsx_data = _make_xlsx(_sample_df())
        df = parse_empregadores(xlsx_data)
        assert len(df) == 5
        assert "empregador" in df.columns
        assert "uf" in df.columns

    def test_golden_data_columns(self):
        expected = json.loads(GOLDEN_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        xlsx_data = _make_xlsx(_sample_df())
        df = parse_empregadores(xlsx_data)

        for col in expected["columns"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_count_matches_golden(self):
        expected = json.loads(GOLDEN_DIR.joinpath("expected.json").read_text(encoding="utf-8"))
        xlsx_data = _make_xlsx(_sample_df())
        df = parse_empregadores(xlsx_data)

        assert len(df) == expected["count"]

    def test_empty_xlsx(self):
        empty = pd.DataFrame(columns=["EMPREGADOR", "CPF/CNPJ", "UF"])
        xlsx_data = _make_xlsx(empty)
        df = parse_empregadores(xlsx_data)
        assert len(df) == 0

    def test_types_datetime(self):
        xlsx_data = _make_xlsx(_sample_df())
        df = parse_empregadores(xlsx_data)
        assert pd.api.types.is_datetime64_any_dtype(df["data_inclusao"])

    def test_types_numeric(self):
        xlsx_data = _make_xlsx(_sample_df())
        df = parse_empregadores(xlsx_data)
        assert pd.api.types.is_numeric_dtype(df["trabalhadores_resgatados"])

    def test_uf_uppercase(self):
        xlsx_data = _make_xlsx(_sample_df())
        df = parse_empregadores(xlsx_data)
        for val in df["uf"].dropna():
            if val:
                assert val == val.upper()

    def test_no_columns_raises(self):
        bad_df = pd.DataFrame({"foo": [1], "bar": [2]})
        xlsx_data = _make_xlsx(bad_df)
        with pytest.raises(ParseError):
            parse_empregadores(xlsx_data)

    def test_output_columns_subset_of_schema(self):
        xlsx_data = _make_xlsx(_sample_df())
        df = parse_empregadores(xlsx_data)
        for col in df.columns:
            assert col in COLUNAS_SAIDA, f"Unexpected column: {col}"
