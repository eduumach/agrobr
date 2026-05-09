from __future__ import annotations

from agrobr.acervo_fundiario import models
from agrobr.normalize.regions import UFS_VALIDAS


class TestUFsDisponiveis:
    def test_sigef_subset_of_ufs_validas(self):
        assert models.SIGEF_UFS_DISPONIVEIS.issubset(UFS_VALIDAS)

    def test_snci_subset_of_ufs_validas(self):
        assert models.SNCI_UFS_DISPONIVEIS.issubset(UFS_VALIDAS)

    def test_sigef_15_ufs(self):
        assert len(models.SIGEF_UFS_DISPONIVEIS) == 15

    def test_snci_10_ufs(self):
        assert len(models.SNCI_UFS_DISPONIVEIS) == 10


class TestFilenamePatterns:
    def test_three_themes(self):
        assert set(models.FILENAME_PATTERNS.keys()) == {"sigef", "snci", "assentamentos"}

    def test_sigef_has_uf_placeholder(self):
        assert "{uf}" in models.FILENAME_PATTERNS["sigef"]

    def test_snci_has_uf_placeholder(self):
        assert "{uf}" in models.FILENAME_PATTERNS["snci"]

    def test_assentamentos_brasil_unico(self):
        assert "{uf}" not in models.FILENAME_PATTERNS["assentamentos"]

    def test_sigef_format(self):
        assert models.FILENAME_PATTERNS["sigef"].format(uf="GO") == "Sigef Brasil_GO.zip"

    def test_snci_format(self):
        assert (
            models.FILENAME_PATTERNS["snci"].format(uf="GO")
            == "Imóvel certificado SNCI Brasil_GO.zip"
        )


class TestRenameMaps:
    def test_sigef_truncated_keys(self):
        assert all(len(k) <= 10 for k in models.SIGEF_RENAME_MAP)

    def test_snci_truncated_keys(self):
        assert all(len(k) <= 10 for k in models.SNCI_RENAME_MAP)

    def test_assentamentos_truncated_keys(self):
        assert all(len(k) <= 10 for k in models.ASSENTAMENTOS_RENAME_MAP)


class TestColunasSaida:
    def test_sigef_geo_extends_with_geometry(self):
        assert [*models.SIGEF_COLUNAS_SAIDA, "geometry"] == models.SIGEF_COLUNAS_SAIDA_GEO

    def test_snci_geo_extends_with_geometry(self):
        assert [*models.SNCI_COLUNAS_SAIDA, "geometry"] == models.SNCI_COLUNAS_SAIDA_GEO

    def test_assentamentos_geo_extends_with_geometry(self):
        assert [
            *models.ASSENTAMENTOS_COLUNAS_SAIDA,
            "geometry",
        ] == models.ASSENTAMENTOS_COLUNAS_SAIDA_GEO

    def test_sigef_includes_uf(self):
        assert "uf" in models.SIGEF_COLUNAS_SAIDA

    def test_snci_includes_uf(self):
        assert "uf" in models.SNCI_COLUNAS_SAIDA

    def test_assentamentos_includes_uf(self):
        assert "uf" in models.ASSENTAMENTOS_COLUNAS_SAIDA


class TestRequiredCols:
    def test_sigef_required_uses_truncated_names(self):
        assert "parcela_co" in models.SIGEF_REQUIRED_COLS
        assert "uf_id" in models.SIGEF_REQUIRED_COLS

    def test_snci_required_uses_truncated_names(self):
        assert "num_proces" in models.SNCI_REQUIRED_COLS
        assert "uf_municip" in models.SNCI_REQUIRED_COLS

    def test_assentamentos_required_uses_truncated_names(self):
        assert "cd_sipra" in models.ASSENTAMENTOS_REQUIRED_COLS
        assert "uf" in models.ASSENTAMENTOS_REQUIRED_COLS


class TestDateCols:
    def test_sigef_date_cols_in_saida(self):
        assert all(c in models.SIGEF_COLUNAS_SAIDA for c in models.SIGEF_DATE_COLS)

    def test_snci_date_cols_in_saida(self):
        assert all(c in models.SNCI_COLUNAS_SAIDA for c in models.SNCI_DATE_COLS)

    def test_assentamentos_date_cols_in_saida(self):
        assert all(c in models.ASSENTAMENTOS_COLUNAS_SAIDA for c in models.ASSENTAMENTOS_DATE_COLS)


class TestConstants:
    def test_dbf_encoding_latin1(self):
        assert models.DBF_ENCODING == "latin1"

    def test_base_url_certificacao(self):
        assert "certificacao.incra.gov.br" in models.BASE_URL
        assert models.BASE_URL.endswith("/")
