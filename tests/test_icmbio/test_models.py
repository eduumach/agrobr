from __future__ import annotations

from agrobr.icmbio.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    GEOM_COLUMN,
    GRUPOS_VALIDOS,
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
    def test_wfs_version_1_1_0(self):
        assert WFS_VERSION == "1.1.0"

    def test_layer(self):
        assert LAYER == "limiteucsfederais_a"

    def test_namespace(self):
        assert NAMESPACE == "ICMBio"

    def test_geom_column(self):
        assert GEOM_COLUMN == "the_geom"

    def test_wfs_base_url(self):
        assert "geoservicos.inde.gov.br" in WFS_BASE
        assert "ICMBio" in WFS_BASE


class TestPropertyNames:
    def test_property_names_has_cnuc(self):
        assert "cnuc" in PROPERTY_NAMES

    def test_property_names_has_nomeuc(self):
        assert "nomeuc" in PROPERTY_NAMES

    def test_property_names_has_grupouc(self):
        assert "grupouc" in PROPERTY_NAMES

    def test_property_names_has_areahaalb(self):
        assert "areahaalb" in PROPERTY_NAMES

    def test_property_names_geo_starts_with_geom(self):
        assert PROPERTY_NAMES_GEO[0] == GEOM_COLUMN

    def test_property_names_geo_contains_all_properties(self):
        for prop in PROPERTY_NAMES:
            assert prop in PROPERTY_NAMES_GEO


class TestColunaSaida:
    def test_colunas_saida_has_codigo(self):
        assert "codigo" in COLUNAS_SAIDA

    def test_colunas_saida_has_nome(self):
        assert "nome" in COLUNAS_SAIDA

    def test_colunas_saida_has_area_ha(self):
        assert "area_ha" in COLUNAS_SAIDA

    def test_colunas_saida_geo_has_geometry(self):
        assert "geometry" in COLUNAS_SAIDA_GEO

    def test_colunas_saida_geo_superset(self):
        for col in COLUNAS_SAIDA:
            assert col in COLUNAS_SAIDA_GEO


class TestRenameMap:
    def test_rename_map_keys_subset_of_property_names(self):
        for key in RENAME_MAP:
            assert key in PROPERTY_NAMES, f"RENAME_MAP key {key!r} not in PROPERTY_NAMES"

    def test_rename_map_values_match_colunas_saida(self):
        for val in RENAME_MAP.values():
            assert val in COLUNAS_SAIDA, f"RENAME_MAP value {val!r} not in COLUNAS_SAIDA"


class TestGruposValidos:
    def test_pi_in_grupos(self):
        assert "PI" in GRUPOS_VALIDOS

    def test_us_in_grupos(self):
        assert "US" in GRUPOS_VALIDOS

    def test_grupos_has_two(self):
        assert len(GRUPOS_VALIDOS) == 2


class TestMaxFeatures:
    def test_max_features_geo_covers_all_federal(self):
        assert MAX_FEATURES_GEO >= 344

    def test_max_features_tabular_covers_all_federal(self):
        assert MAX_FEATURES_TABULAR >= 344
