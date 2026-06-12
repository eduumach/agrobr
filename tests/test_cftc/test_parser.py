from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from agrobr.cftc.models import CHANGE_COLUMNS, COLUNAS_SAIDA, POSITION_COLUMNS
from agrobr.cftc.parser import parse_cot
from agrobr.exceptions import ParseError

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "cftc"


def _load_golden() -> list[dict[str, str]]:
    with open(GOLDEN_DIR / "cot_sample.json", encoding="utf-8") as f:
        return json.load(f)


class TestParseCotGolden:
    def test_colunas_e_tamanho(self):
        df = parse_cot(_load_golden())

        assert list(df.columns) == COLUNAS_SAIDA
        assert len(df) == 6

    def test_dtypes(self):
        df = parse_cot(_load_golden())

        assert pd.api.types.is_datetime64_any_dtype(df["data"])
        for col in POSITION_COLUMNS:
            assert df[col].dtype == "int64", col
        assert df["managed_money_net"].dtype == "int64"
        for col in CHANGE_COLUMNS:
            assert df[col].dtype == "Int64", col

    def test_commodity_mapeada(self):
        df = parse_cot(_load_golden())

        assert set(df["commodity"]) == {"soja", "acucar"}
        soja = df[df["commodity"] == "soja"]
        assert soja["contrato"].iloc[0] == "SOYBEANS - CHICAGO BOARD OF TRADE"
        assert soja["codigo_cftc"].iloc[0] == "005602"

    def test_managed_money_net_calculado(self):
        df = parse_cot(_load_golden())

        esperado = df["managed_money_long"] - df["managed_money_short"]
        assert (df["managed_money_net"] == esperado).all()

    def test_ordenacao_por_data_e_commodity(self):
        df = parse_cot(_load_golden())

        assert df["data"].is_monotonic_increasing or (
            df.sort_values(["data", "commodity"]).reset_index(drop=True).equals(df)
        )

    def test_valores_soja_ultima_semana(self):
        df = parse_cot(_load_golden())

        soja = df[(df["commodity"] == "soja") & (df["data"] == "2026-06-02")]
        assert len(soja) == 1
        assert soja["open_interest"].iloc[0] == 1054882
        assert soja["managed_money_net"].iloc[0] == 155780


class TestParseCotValidation:
    def test_campo_ausente_raises(self):
        records = _load_golden()
        for r in records:
            del r["m_money_positions_long_all"]

        with pytest.raises(ParseError, match="Campos ausentes"):
            parse_cot(records)

    def test_posicao_nula_raises(self):
        records = _load_golden()
        records[0]["open_interest_all"] = ""

        with pytest.raises(ParseError, match="Posições nulas"):
            parse_cot(records)

    def test_posicao_negativa_raises(self):
        records = _load_golden()
        records[0]["open_interest_all"] = "-100"

        with pytest.raises(ParseError, match="Posições negativas"):
            parse_cot(records)

    def test_data_invalida_raises(self):
        records = _load_golden()
        records[0]["report_date_as_yyyy_mm_dd"] = "data-quebrada"

        with pytest.raises(ParseError, match="Datas inválidas"):
            parse_cot(records)

    def test_codigo_nao_mapeado_mantem_codigo(self):
        records = _load_golden()
        for r in records:
            r["cftc_contract_market_code"] = "999999"

        df = parse_cot(records)
        assert (df["commodity"] == "999999").all()

    def test_change_nulo_aceito(self):
        records = _load_golden()
        del records[0]["change_in_m_money_long_all"]

        df = parse_cot(records)
        assert df["change_managed_money_long"].isna().sum() == 1
