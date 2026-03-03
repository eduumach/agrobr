from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.zarc.models import COLUNAS_SAIDA
from agrobr.zarc.parser import parse_tabua_risco

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "zarc" / "tabua_risco_sample"


def _load_golden_csv() -> bytes:
    return (GOLDEN_DIR / "response.csv").read_bytes()


class TestParseTabuaRisco:
    def test_parse_returns_dataframe(self):
        df = parse_tabua_risco(_load_golden_csv())
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 19

    def test_parse_columns_match(self):
        df = parse_tabua_risco(_load_golden_csv())
        assert df.columns.tolist() == COLUNAS_SAIDA

    def test_parse_cultura_normalized(self):
        df = parse_tabua_risco(_load_golden_csv())
        culturas = df["cultura"].unique().tolist()
        assert "soja" in culturas
        assert "milho_1" in culturas
        assert "trigo" in culturas
        assert "Soja" not in culturas

    def test_parse_safra_format(self):
        df = parse_tabua_risco(_load_golden_csv())
        non_perene = df[df["safra"] != "perene"]
        for safra in non_perene["safra"].unique():
            assert "/" in safra
            parts = safra.split("/")
            assert len(parts) == 2
            assert parts[0].isdigit() and parts[1].isdigit()

    def test_parse_perene_safra(self):
        df = parse_tabua_risco(_load_golden_csv())
        perene = df[df["safra"] == "perene"]
        assert len(perene) == 4
        perene_culturas = sorted(perene["cultura"].unique().tolist())
        assert "cafe_arabica" in perene_culturas
        assert "cana" in perene_culturas

    def test_parse_dec_values_valid(self):
        df = parse_tabua_risco(_load_golden_csv())
        dec_cols = [f"dec{i}" for i in range(1, 37)]
        for col in dec_cols:
            vals = set(df[col].unique())
            assert vals <= {0, 20, 30, 40}, f"{col} has unexpected values: {vals}"

    def test_parse_solo_ciclo_int(self):
        df = parse_tabua_risco(_load_golden_csv())
        assert df["solo_codigo"].dtype in (int, "int64", "int32")
        assert df["ciclo_codigo"].dtype in (int, "int64", "int32")

    def test_parse_geocodigo_7_digits(self):
        df = parse_tabua_risco(_load_golden_csv())
        for geo in df["geocodigo"].unique():
            assert len(str(geo)) == 7, f"geocodigo {geo} != 7 chars"

    def test_parse_empty_csv(self):
        df = parse_tabua_risco(b"")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert df.columns.tolist() == COLUNAS_SAIDA

    def test_parse_missing_column_raises(self):
        csv_bytes = b"col1;col2;col3\na;b;c\n"
        with pytest.raises(ParseError, match="Missing columns"):
            parse_tabua_risco(csv_bytes)
