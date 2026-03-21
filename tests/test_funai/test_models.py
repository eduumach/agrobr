from agrobr.funai.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    FASES_VALIDAS,
    GEOM_COLUMN,
    LAYER,
    MAX_FEATURES_GEO,
    MAX_FEATURES_TABULAR,
    NAMESPACE,
    PROPERTY_NAMES,
    PROPERTY_NAMES_GEO,
    RENAME_MAP,
    WFS_BASE,
    WFS_VERSION,
)


class TestWfsConstants:
    def test_wfs_base_url(self):
        assert "geoserver.funai.gov.br" in WFS_BASE
        assert WFS_BASE.startswith("https://")

    def test_wfs_version(self):
        assert WFS_VERSION == "2.0.0"

    def test_layer(self):
        assert LAYER == "tis_poligonais"

    def test_namespace(self):
        assert NAMESPACE == "Funai"

    def test_geom_column(self):
        assert GEOM_COLUMN == "the_geom"


class TestPropertyNames:
    def test_property_names_has_required_fields(self):
        assert "terrai_codigo" in PROPERTY_NAMES
        assert "terrai_nome" in PROPERTY_NAMES
        assert "uf_sigla" in PROPERTY_NAMES
        assert "superficie_perimetro_ha" in PROPERTY_NAMES

    def test_property_names_geo_starts_with_geom(self):
        assert PROPERTY_NAMES_GEO[0] == GEOM_COLUMN

    def test_property_names_geo_contains_all_tabular(self):
        for prop in PROPERTY_NAMES:
            assert prop in PROPERTY_NAMES_GEO


class TestColunaSaida:
    def test_colunas_saida_contains_expected(self):
        expected = [
            "codigo",
            "nome",
            "etnia",
            "municipio",
            "uf",
            "area_ha",
            "fase",
            "modalidade",
            "data_atualizacao",
        ]
        assert expected == COLUNAS_SAIDA

    def test_colunas_saida_geo_extends_tabular(self):
        assert COLUNAS_SAIDA_GEO == COLUNAS_SAIDA + ["geometry"]

    def test_colunas_saida_geo_has_geometry(self):
        assert "geometry" in COLUNAS_SAIDA_GEO


class TestRenameMap:
    def test_rename_map_keys_subset_of_property_names(self):
        for key in RENAME_MAP:
            assert key in PROPERTY_NAMES, f"RENAME_MAP key {key!r} not in PROPERTY_NAMES"

    def test_rename_map_values_in_colunas_saida(self):
        for value in RENAME_MAP.values():
            assert value in COLUNAS_SAIDA, f"RENAME_MAP value {value!r} not in COLUNAS_SAIDA"


class TestFasesValidas:
    def test_fases_validas_has_expected_values(self):
        assert "Regularizada" in FASES_VALIDAS
        assert "Homologada" in FASES_VALIDAS
        assert "Declarada" in FASES_VALIDAS
        assert "Delimitada" in FASES_VALIDAS
        assert "Em Estudo" in FASES_VALIDAS
        assert "Encaminhada RI" in FASES_VALIDAS

    def test_fases_validas_is_frozenset(self):
        assert isinstance(FASES_VALIDAS, frozenset)

    def test_fases_validas_count(self):
        assert len(FASES_VALIDAS) == 6


class TestMaxFeatures:
    def test_max_features_geo(self):
        assert MAX_FEATURES_GEO >= 740

    def test_max_features_tabular(self):
        assert MAX_FEATURES_TABULAR >= 740
