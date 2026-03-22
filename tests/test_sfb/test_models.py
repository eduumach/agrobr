from agrobr.sfb.models import LAYERS, SFB_BASE


class TestLayers:
    def test_layer_count(self):
        assert len(LAYERS) == 3

    def test_layer_keys(self):
        expected = {"cnfp", "concessoes", "ifn_conglomerados"}
        assert set(LAYERS.keys()) == expected

    def test_each_layer_has_required_config(self):
        required_keys = {
            "service_path",
            "max_record_count",
            "fields",
            "rename_map",
            "colunas_saida",
            "required_cols",
        }
        for key, config in LAYERS.items():
            for rk in required_keys:
                assert rk in config, f"Layer {key!r} missing config key {rk!r}"


class TestSfbBase:
    def test_base_url_https(self):
        assert SFB_BASE.startswith("https://")

    def test_base_url_domain(self):
        assert "florestal" in SFB_BASE or "sfb" in SFB_BASE or "arcgis" in SFB_BASE
