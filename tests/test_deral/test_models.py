"""Testes para os modelos DERAL."""

from agrobr.deral.models import DERAL_PRODUTOS, normalize_condicao, normalize_produto


class TestNormalizeProduto:
    def test_soja(self):
        assert normalize_produto("soja") == "soja"
        assert normalize_produto("Soja") == "soja"

    def test_milho(self):
        assert normalize_produto("milho") == "milho"

    def test_milho_safras(self):
        assert normalize_produto("milho 1ª safra") == "milho_1"
        assert normalize_produto("milho 2ª safra") == "milho_2"
        assert normalize_produto("milho safrinha") == "milho_2"
        assert normalize_produto("milho verão") == "milho_1"

    def test_trigo(self):
        assert normalize_produto("trigo") == "trigo"
        assert normalize_produto("Trigo") == "trigo"

    def test_feijao(self):
        assert normalize_produto("feijão") == "feijao"
        assert normalize_produto("feijao") == "feijao"

    def test_cana(self):
        assert normalize_produto("cana-de-açúcar") == "cana"
        assert normalize_produto("cana") == "cana"

    def test_cafe(self):
        assert normalize_produto("café") == "cafe"
        assert normalize_produto("cafe") == "cafe"

    def test_unknown_passthrough(self):
        assert normalize_produto("sorgo") == "sorgo"

    def test_whitespace_stripped(self):
        assert normalize_produto("  soja  ") == "soja"


class TestNormalizeCondicao:
    def test_boa(self):
        assert normalize_condicao("boa") == "boa"
        assert normalize_condicao("Boa") == "boa"
        assert normalize_condicao("bom") == "boa"

    def test_media(self):
        assert normalize_condicao("média") == "media"
        assert normalize_condicao("media") == "media"
        assert normalize_condicao("regular") == "media"

    def test_ruim(self):
        assert normalize_condicao("ruim") == "ruim"
        assert normalize_condicao("Ruim") == "ruim"
        assert normalize_condicao("má") == "ruim"

    def test_unknown_passthrough(self):
        assert normalize_condicao("excelente") == "excelente"


class TestDeralProdutos:
    def test_main_products(self):
        assert "soja" in DERAL_PRODUTOS
        assert "milho" in DERAL_PRODUTOS
        assert "trigo" in DERAL_PRODUTOS
        assert "cafe" in DERAL_PRODUTOS

    def test_count(self):
        assert len(DERAL_PRODUTOS) >= 10
