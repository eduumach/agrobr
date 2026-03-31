from __future__ import annotations

from agrobr.acervo_fundiario import models


class TestSigefModels:
    def test_layers_have_expected_keys(self):
        assert "particular" in models.SIGEF_LAYERS
        assert "publico" in models.SIGEF_LAYERS

    def test_tipos_match_layers(self):
        assert frozenset(models.SIGEF_LAYERS.keys()) == models.TIPOS_SIGEF

    def test_rename_map_keys_match_property_names(self):
        assert set(models.SIGEF_RENAME_MAP.keys()) == set(models.SIGEF_PROPERTY_NAMES)

    def test_colunas_saida_match_rename_values(self):
        assert set(models.SIGEF_COLUNAS_SAIDA) == set(models.SIGEF_RENAME_MAP.values())

    def test_colunas_saida_geo(self):
        assert models.SIGEF_COLUNAS_SAIDA_GEO == models.SIGEF_COLUNAS_SAIDA + ["geometry"]

    def test_required_cols_subset_of_property_names(self):
        assert set(models.SIGEF_PROPERTY_NAMES) >= models.SIGEF_REQUIRED_COLS


class TestSnciModels:
    def test_layers_have_expected_keys(self):
        assert "privado" in models.SNCI_LAYERS
        assert "publico" in models.SNCI_LAYERS

    def test_tipos_match_layers(self):
        assert frozenset(models.SNCI_LAYERS.keys()) == models.TIPOS_SNCI

    def test_rename_map_keys_match_property_names(self):
        assert set(models.SNCI_RENAME_MAP.keys()) == set(models.SNCI_PROPERTY_NAMES)

    def test_colunas_saida_match_rename_values(self):
        assert set(models.SNCI_COLUNAS_SAIDA) == set(models.SNCI_RENAME_MAP.values())

    def test_colunas_saida_geo(self):
        assert models.SNCI_COLUNAS_SAIDA_GEO == models.SNCI_COLUNAS_SAIDA + ["geometry"]

    def test_required_cols_subset_of_property_names(self):
        assert set(models.SNCI_PROPERTY_NAMES) >= models.SNCI_REQUIRED_COLS

    def test_numeric_cols_in_colunas_saida(self):
        renamed = {models.SNCI_RENAME_MAP.get(c, c) for c in models.SNCI_NUMERIC_COLS}
        assert renamed <= set(models.SNCI_COLUNAS_SAIDA)


class TestAssentamentosModels:
    def test_layer_is_string(self):
        assert isinstance(models.ASSENTAMENTOS_LAYER, str)

    def test_rename_map_keys_match_property_names(self):
        assert set(models.ASSENTAMENTOS_RENAME_MAP.keys()) == set(
            models.ASSENTAMENTOS_PROPERTY_NAMES
        )

    def test_colunas_saida_match_rename_values(self):
        assert set(models.ASSENTAMENTOS_COLUNAS_SAIDA) == set(
            models.ASSENTAMENTOS_RENAME_MAP.values()
        )

    def test_colunas_saida_geo(self):
        assert models.ASSENTAMENTOS_COLUNAS_SAIDA_GEO == models.ASSENTAMENTOS_COLUNAS_SAIDA + [
            "geometry"
        ]

    def test_required_cols_subset_of_property_names(self):
        assert set(models.ASSENTAMENTOS_PROPERTY_NAMES) >= models.ASSENTAMENTOS_REQUIRED_COLS

    def test_numeric_cols_in_colunas_saida(self):
        renamed = {
            models.ASSENTAMENTOS_RENAME_MAP.get(c, c) for c in models.ASSENTAMENTOS_NUMERIC_COLS
        }
        assert renamed <= set(models.ASSENTAMENTOS_COLUNAS_SAIDA)


class TestSharedModels:
    def test_wfs_base_is_url(self):
        assert models.WFS_BASE.startswith("https://")

    def test_wfs_version(self):
        assert models.WFS_VERSION == "1.0.0"

    def test_namespaces(self):
        assert models.NS_GML == "http://www.opengis.net/gml"
        assert "omsug" in models.NS_MS
