from agrobr.lista_suja.models import COLUNAS_SAIDA, DOWNLOAD_URL, RENAME_MAP


class TestDownloadUrl:
    def test_url_is_valid(self):
        assert DOWNLOAD_URL.startswith("http")


class TestRenameMap:
    def test_min_size(self):
        assert len(RENAME_MAP) >= 5

    def test_empregador_key(self):
        assert "Empregador" in RENAME_MAP

    def test_values_in_colunas_saida(self):
        for value in RENAME_MAP.values():
            assert value in COLUNAS_SAIDA, f"RENAME_MAP value {value!r} not in COLUNAS_SAIDA"


class TestColunasSaida:
    def test_empregador(self):
        assert "empregador" in COLUNAS_SAIDA

    def test_uf(self):
        assert "uf" in COLUNAS_SAIDA

    def test_cpf_cnpj(self):
        assert "cpf_cnpj" in COLUNAS_SAIDA
