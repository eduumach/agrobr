from agrobr.ibama.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    GEOM_COLUMN,
    LAYER,
    MAX_FEATURES_GEO,
    NAMESPACE,
    PAGE_SIZE,
    PROPERTY_NAMES,
    PROPERTY_NAMES_GEO,
    RENAME_MAP,
    WFS_BASE,
    WFS_VERSION,
)


class TestWfsConstants:
    def test_wfs_base_url(self):
        assert "siscom.ibama.gov.br" in WFS_BASE
        assert WFS_BASE.startswith("https://")

    def test_wfs_version(self):
        assert WFS_VERSION == "2.0.0"

    def test_layer(self):
        assert LAYER == "vw_brasil_adm_embargo_a"

    def test_namespace(self):
        assert NAMESPACE == "publica"

    def test_geom_column(self):
        assert GEOM_COLUMN == "geom"


class TestPropertyNames:
    def test_has_required_fields(self):
        assert "numero_tad" in PROPERTY_NAMES
        assert "data_tad" in PROPERTY_NAMES
        assert "sig_uf" in PROPERTY_NAMES
        assert "qtd_area_desmatada" in PROPERTY_NAMES

    def test_geo_starts_with_geom(self):
        assert PROPERTY_NAMES_GEO[0] == GEOM_COLUMN

    def test_geo_superset_of_tabular(self):
        for prop in PROPERTY_NAMES:
            assert prop in PROPERTY_NAMES_GEO


class TestColunaSaida:
    def test_contains_expected(self):
        expected = [
            "numero_tad",
            "data_embargo",
            "uf",
            "municipio",
            "area_desmatada_ha",
            "infracao",
            "legislacao",
            "status",
            "situacao_poligono",
            "respeita_embargo",
        ]
        assert expected == COLUNAS_SAIDA

    def test_geo_extends_tabular(self):
        assert COLUNAS_SAIDA_GEO == COLUNAS_SAIDA + ["geometry"]

    def test_geo_has_geometry(self):
        assert "geometry" in COLUNAS_SAIDA_GEO


class TestRenameMap:
    def test_keys_subset_of_property_names(self):
        for key in RENAME_MAP:
            assert key in PROPERTY_NAMES, f"RENAME_MAP key {key!r} not in PROPERTY_NAMES"

    def test_values_in_colunas_saida(self):
        for value in RENAME_MAP.values():
            assert value in COLUNAS_SAIDA, f"RENAME_MAP value {value!r} not in COLUNAS_SAIDA"


class TestMaxFeatures:
    def test_page_size(self):
        assert PAGE_SIZE >= 10_000

    def test_geo(self):
        assert MAX_FEATURES_GEO >= 5_000


class TestPiiExclusion:
    def test_nom_pessoa_not_in_property_names(self):
        assert "nom_pessoa" not in PROPERTY_NAMES
        assert "nom_pessoa" not in PROPERTY_NAMES_GEO

    def test_cpf_cnpj_not_in_property_names(self):
        assert "cpf_cnpj_infrator" not in PROPERTY_NAMES
        assert "cpf_cnpj_infrator" not in PROPERTY_NAMES_GEO
