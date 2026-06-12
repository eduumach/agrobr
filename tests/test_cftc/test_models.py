from __future__ import annotations

import pytest

from agrobr.cftc.models import (
    CFTC_CONTRACTS,
    CHANGE_COLUMNS,
    COLUMN_MAP,
    COLUNAS_SAIDA,
    POSITION_COLUMNS,
    resolve_contract_codes,
)
from agrobr.normalize.crops import CANONICAL_CROPS


class TestCftcContracts:
    def test_doze_contratos_mapeados(self):
        assert len(CFTC_CONTRACTS) == 12

    def test_commodities_sao_canonicas(self):
        for code, commodity in CFTC_CONTRACTS.items():
            assert commodity in CANONICAL_CROPS, f"{code} -> {commodity}"

    def test_codigos_sao_strings_de_seis_chars(self):
        assert all(len(code) == 6 for code in CFTC_CONTRACTS)


class TestColumnMapConsistency:
    def test_colunas_saida_cobertas(self):
        derivadas = {"commodity", "managed_money_net"}
        mapeadas = set(COLUMN_MAP.values())
        for col in COLUNAS_SAIDA:
            assert col in mapeadas or col in derivadas

    def test_position_e_change_em_colunas_saida(self):
        for col in POSITION_COLUMNS + CHANGE_COLUMNS:
            assert col in COLUNAS_SAIDA

    def test_typo_swap_short_da_fonte_preservado(self):
        assert "swap__positions_short_all" in COLUMN_MAP
        assert COLUMN_MAP["swap__positions_short_all"] == "swap_short"


class TestResolveContractCodes:
    def test_none_retorna_todos(self):
        assert resolve_contract_codes(None) == list(CFTC_CONTRACTS)

    def test_canonico_pt(self):
        assert resolve_contract_codes("soja") == ["005602"]

    def test_alias_ingles(self):
        assert resolve_contract_codes("soybeans") == ["005602"]
        assert resolve_contract_codes("corn") == ["002602"]

    def test_codigo_direto(self):
        assert resolve_contract_codes("080732") == ["080732"]

    def test_case_insensitive(self):
        assert resolve_contract_codes("SOJA") == ["005602"]

    def test_acento(self):
        assert resolve_contract_codes("açúcar") == ["080732"]

    def test_boi_gordo_resolve_para_boi(self):
        assert resolve_contract_codes("boi gordo") == ["057642"]

    def test_commodity_sem_contrato_raises(self):
        with pytest.raises(ValueError, match="sem contrato CFTC"):
            resolve_contract_codes("mandioca")

    def test_commodity_invalida_raises(self):
        with pytest.raises(ValueError, match="sem contrato CFTC"):
            resolve_contract_codes("commodity_inexistente")
