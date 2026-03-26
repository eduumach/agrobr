from agrobr.embrapa_solos.models import (
    MAPA_COLUNAS_SAIDA,
    MAPA_COLUNAS_SAIDA_GEO,
    MAPA_PROPERTY_NAMES,
    MAPA_RENAME_MAP,
    PERFIS_COLUNAS_SAIDA,
    PERFIS_COLUNAS_SAIDA_GEO,
    PERFIS_NUMERIC_COLS,
    PERFIS_PROPERTY_NAMES,
    PERFIS_RENAME_MAP,
    WFS_VERSION,
)


def test_wfs_version_is_2():
    assert WFS_VERSION == "2.0.0"


def test_perfis_output_has_19_columns():
    assert len(PERFIS_COLUNAS_SAIDA) == 19


def test_perfis_geo_adds_geometry():
    assert PERFIS_COLUNAS_SAIDA_GEO == PERFIS_COLUNAS_SAIDA + ["geometry"]


def test_perfis_numeric_cols_subset_of_output():
    assert set(PERFIS_COLUNAS_SAIDA) >= PERFIS_NUMERIC_COLS


def test_perfis_rename_values_in_output():
    renamed = set(PERFIS_RENAME_MAP.values())
    output = set(PERFIS_COLUNAS_SAIDA)
    assert renamed <= output


def test_perfis_property_names_has_key_fields():
    assert "fid" in PERFIS_PROPERTY_NAMES
    assert "uf" in PERFIS_PROPERTY_NAMES
    assert "ph_h2o" in PERFIS_PROPERTY_NAMES


def test_mapa_output_has_15_columns():
    assert len(MAPA_COLUNAS_SAIDA) == 15


def test_mapa_geo_adds_geometry():
    assert MAPA_COLUNAS_SAIDA_GEO == MAPA_COLUNAS_SAIDA + ["geometry"]


def test_mapa_property_names_has_key_fields():
    assert "ogc_fid" in MAPA_PROPERTY_NAMES
    assert "classe_dom" in MAPA_PROPERTY_NAMES
    assert "area_km2" in MAPA_PROPERTY_NAMES


def test_mapa_rename_values_in_output():
    renamed = set(MAPA_RENAME_MAP.values())
    output = set(MAPA_COLUNAS_SAIDA)
    assert renamed <= output
