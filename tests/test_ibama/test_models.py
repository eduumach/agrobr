from __future__ import annotations

from agrobr.ibama.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    CSV_COLUMN_MAP,
    GEOM_COLUMN_CSV,
    MIN_CSV_BYTES,
    ZIP_URL,
)


class TestModels:
    def test_zip_url_aponta_dados_abertos(self):
        assert ZIP_URL.startswith("https://dadosabertos.ibama.gov.br/")
        assert ZIP_URL.endswith(".zip")

    def test_colunas_saida_derivam_do_map(self):
        assert list(CSV_COLUMN_MAP.values()) == COLUNAS_SAIDA
        assert [*COLUNAS_SAIDA, "geometry"] == COLUNAS_SAIDA_GEO

    def test_geom_nao_esta_no_map_tabular(self):
        assert GEOM_COLUMN_CSV not in CSV_COLUMN_MAP

    def test_colunas_chave_presentes(self):
        for col in ("seq_tad", "numero_tad", "data_embargo", "uf", "area_embargada_ha"):
            assert col in COLUNAS_SAIDA

    def test_min_csv_bytes_protege_truncamento(self):
        assert MIN_CSV_BYTES >= 1_000_000
