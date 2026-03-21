from __future__ import annotations

from agrobr.incra.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
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


class TestConstants:
    def test_wfs_version_is_1_0_0(self):
        assert WFS_VERSION == "1.0.0"

    def test_layer(self):
        assert LAYER == "lim_quilombolas_a"

    def test_namespace_is_cmr_publico(self):
        assert NAMESPACE == "CMR-PUBLICO"

    def test_geom_column(self):
        assert GEOM_COLUMN == "the_geom"

    def test_wfs_base_url(self):
        assert "cmr.funai.gov.br" in WFS_BASE

    def test_max_features_geo_gte_426(self):
        assert MAX_FEATURES_GEO >= 426

    def test_max_features_tabular(self):
        assert MAX_FEATURES_TABULAR >= 1

    def test_property_names_has_required(self):
        assert "cd_quilomb" in PROPERTY_NAMES
        assert "no_comunidade" in PROPERTY_NAMES
        assert "sg_uf" in PROPERTY_NAMES
        assert "nu_area_ha" in PROPERTY_NAMES
        assert "nu_familia" in PROPERTY_NAMES
        assert "ds_fase" in PROPERTY_NAMES
        assert "st_titulad" in PROPERTY_NAMES
        assert "dt_publica" in PROPERTY_NAMES
        assert "dt_titulo" in PROPERTY_NAMES

    def test_property_names_geo_starts_with_geom(self):
        assert PROPERTY_NAMES_GEO[0] == GEOM_COLUMN
        for pn in PROPERTY_NAMES:
            assert pn in PROPERTY_NAMES_GEO

    def test_rename_map_keys_match_property_names(self):
        for key in RENAME_MAP:
            assert key in PROPERTY_NAMES

    def test_rename_map_values_match_colunas_saida(self):
        for val in RENAME_MAP.values():
            assert val in COLUNAS_SAIDA

    def test_colunas_saida_has_required(self):
        assert "codigo" in COLUNAS_SAIDA
        assert "nome" in COLUNAS_SAIDA
        assert "municipio" in COLUNAS_SAIDA
        assert "uf" in COLUNAS_SAIDA
        assert "area_ha" in COLUNAS_SAIDA
        assert "familias" in COLUNAS_SAIDA
        assert "fase" in COLUNAS_SAIDA
        assert "titulado" in COLUNAS_SAIDA
        assert "data_publicacao" in COLUNAS_SAIDA
        assert "data_titulo" in COLUNAS_SAIDA

    def test_colunas_saida_geo_has_geometry(self):
        assert "geometry" in COLUNAS_SAIDA_GEO

    def test_colunas_saida_geo_contains_all_tabular(self):
        for col in COLUNAS_SAIDA:
            assert col in COLUNAS_SAIDA_GEO
