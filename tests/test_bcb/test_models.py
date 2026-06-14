from agrobr.bcb.models import (
    SICOR_ATIVIDADES,
    SICOR_FONTES_RECURSO,
    SICOR_MODALIDADES,
    SICOR_PRODUTOS,
    SICOR_PROGRAMAS,
    SICOR_TIPOS_SEGURO,
    UF_CODES,
    normalize_safra_sicor,
    resolve_atividade,
    resolve_fonte_recurso,
    resolve_modalidade,
    resolve_produto_sicor,
    resolve_programa,
    resolve_tipo_seguro,
)


class TestNormalizeSafraSicor:
    def test_full_format(self):
        assert normalize_safra_sicor("2023/2024") == "2023/2024"

    def test_short_format(self):
        assert normalize_safra_sicor("2023/24") == "2023/2024"

    def test_year_only(self):
        assert normalize_safra_sicor("2024") == "2023/2024"

    def test_strip(self):
        assert normalize_safra_sicor("  2023/24  ") == "2023/2024"

    def test_century_boundary(self):
        assert normalize_safra_sicor("2099/00") == "2099/2100"


class TestResolveProdutoSicor:
    def test_known_products(self):
        assert resolve_produto_sicor("soja") == "SOJA"
        assert resolve_produto_sicor("milho") == "MILHO"
        assert resolve_produto_sicor("algodao") == "ALGODAO HERBACEO"
        assert resolve_produto_sicor("cafe") == "CAFE"

    def test_unknown_product(self):
        assert resolve_produto_sicor("quinoa") == "QUINOA"

    def test_case_insensitive(self):
        assert resolve_produto_sicor("SOJA") == "SOJA"
        assert resolve_produto_sicor("Soja") == "SOJA"


class TestUfCodes:
    def test_main_states(self):
        assert UF_CODES["MT"] == "51"
        assert UF_CODES["SP"] == "35"
        assert UF_CODES["PR"] == "41"
        assert UF_CODES["GO"] == "52"

    def test_all_states(self):
        assert len(UF_CODES) == 27

    def test_sicor_produtos_completeness(self):
        assert len(SICOR_PRODUTOS) >= 10


class TestSicorProgramas:
    def test_known_entries(self):
        assert SICOR_PROGRAMAS["0001"] == "Pronaf"
        assert SICOR_PROGRAMAS["0050"] == "Pronamp"
        assert SICOR_PROGRAMAS["0999"] == "Sem programa especifico"

    def test_minimum_size(self):
        assert len(SICOR_PROGRAMAS) >= 10


class TestSicorFontesRecurso:
    def test_known_entries(self):
        assert SICOR_FONTES_RECURSO["0201"] == "Recursos obrigatorios (MCR 6.2)"
        assert SICOR_FONTES_RECURSO["0430"] == "LCA"
        assert SICOR_FONTES_RECURSO["0505"] == "Funcafe"

    def test_minimum_size(self):
        assert len(SICOR_FONTES_RECURSO) >= 8


class TestSicorTiposSeguro:
    def test_covers_known_codes(self):
        assert "1" in SICOR_TIPOS_SEGURO
        assert "2" in SICOR_TIPOS_SEGURO
        assert "3" in SICOR_TIPOS_SEGURO
        assert "9" in SICOR_TIPOS_SEGURO

    def test_values(self):
        assert SICOR_TIPOS_SEGURO["1"] == "Proagro"
        assert SICOR_TIPOS_SEGURO["3"] == "Seguro privado"


class TestSicorModalidades:
    def test_known_entries(self):
        assert SICOR_MODALIDADES["01"] == "Individual"
        assert SICOR_MODALIDADES["03"] == "Coletiva"


class TestSicorAtividades:
    def test_known_entries(self):
        assert SICOR_ATIVIDADES["1"] == "Agricola"
        assert SICOR_ATIVIDADES["2"] == "Pecuaria"


class TestResolvePrograma:
    def test_known(self):
        assert resolve_programa("0050") == "Pronamp"
        assert resolve_programa("0001") == "Pronaf"

    def test_unknown_fallback(self):
        result = resolve_programa("9999")
        assert result == "Desconhecido (9999)"


class TestResolveFonteRecurso:
    def test_known(self):
        assert resolve_fonte_recurso("0430") == "LCA"
        assert resolve_fonte_recurso("0303") == "Poupanca rural controlados"

    def test_unknown_fallback(self):
        result = resolve_fonte_recurso("0000")
        assert result == "Desconhecido (0000)"


class TestResolveTipoSeguro:
    def test_known(self):
        assert resolve_tipo_seguro("1") == "Proagro"
        assert resolve_tipo_seguro("9") == "Nao se aplica"

    def test_unknown_fallback(self):
        result = resolve_tipo_seguro("5")
        assert result == "Desconhecido (5)"


class TestResolveModalidade:
    def test_known(self):
        assert resolve_modalidade("01") == "Individual"

    def test_unknown_fallback(self):
        assert resolve_modalidade("99") == "Desconhecido (99)"


class TestResolveAtividade:
    def test_known(self):
        assert resolve_atividade("1") == "Agricola"
        assert resolve_atividade("2") == "Pecuaria"

    def test_unknown_fallback(self):
        assert resolve_atividade("3") == "Desconhecido (3)"
