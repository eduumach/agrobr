"""Testes para agrobr.alt.anp_diesel.models."""

from __future__ import annotations

import pytest

from agrobr.alt.anp_diesel.models import (
    AGREGACOES_VALIDAS,
    NIVEIS_VALIDOS,
    NIVEL_BRASIL,
    NIVEL_MUNICIPIO,
    NIVEL_UF,
    PRECOS_BRASIL_URL,
    PRECOS_ESTADOS_URL,
    PRECOS_MUNICIPIOS_URLS,
    PRODUTOS_DIESEL,
    SHLP_BASE,
    UFS_VALIDAS,
    VENDAS_DIESEL_CSV_URL,
    _resolve_periodo_municipio,
)


class TestConstantes:
    def test_shlp_base_url_valida(self):
        assert SHLP_BASE.startswith("https://www.gov.br/anp")
        assert "shlp" in SHLP_BASE

    def test_vendas_diesel_csv_url_valida(self):
        assert VENDAS_DIESEL_CSV_URL.endswith(".csv")
        assert "vendas-oleo-diesel" in VENDAS_DIESEL_CSV_URL

    def test_precos_municipios_urls_nao_vazio(self):
        assert len(PRECOS_MUNICIPIOS_URLS) >= 3

    def test_precos_municipios_urls_formato(self):
        for periodo, url in PRECOS_MUNICIPIOS_URLS.items():
            assert url.startswith("https://")
            assert ".xlsx" in url or ".xls" in url
            parts = periodo.split("-")
            assert len(parts) in (1, 2)
            for p in parts:
                assert p.isdigit()
                assert int(p) >= 2013

    def test_precos_estados_url_xlsx(self):
        assert PRECOS_ESTADOS_URL.endswith(".xlsx")

    def test_precos_brasil_url_xlsx(self):
        assert PRECOS_BRASIL_URL.endswith(".xlsx")

    def test_produtos_diesel_contem_s10(self):
        assert "DIESEL S10" in PRODUTOS_DIESEL
        assert "DIESEL" in PRODUTOS_DIESEL

    def test_produtos_diesel_frozen(self):
        with pytest.raises(AttributeError):
            PRODUTOS_DIESEL.add("GASOLINA")

    def test_niveis_validos(self):
        assert NIVEL_MUNICIPIO in NIVEIS_VALIDOS
        assert NIVEL_UF in NIVEIS_VALIDOS
        assert NIVEL_BRASIL in NIVEIS_VALIDOS

    def test_agregacoes_validas(self):
        assert "semanal" in AGREGACOES_VALIDAS
        assert "mensal" in AGREGACOES_VALIDAS

    def test_ufs_27_estados(self):
        assert len(UFS_VALIDAS) == 27
        assert "SP" in UFS_VALIDAS
        assert "MT" in UFS_VALIDAS
        assert "DF" in UFS_VALIDAS


class TestResolvePeriodoMunicipio:
    def test_ano_2022(self):
        assert _resolve_periodo_municipio(2022) == "2022-2023"

    def test_ano_2023(self):
        assert _resolve_periodo_municipio(2023) == "2022-2023"

    def test_ano_2024(self):
        assert _resolve_periodo_municipio(2024) == "2024-2025"

    def test_ano_2025(self):
        assert _resolve_periodo_municipio(2025) == "2024-2025"

    def test_ano_2026(self):
        assert _resolve_periodo_municipio(2026) == "2026"

    def test_ano_antigo_retorna_none(self):
        assert _resolve_periodo_municipio(2010) is None

    def test_ano_futuro_retorna_none(self):
        assert _resolve_periodo_municipio(2030) is None
