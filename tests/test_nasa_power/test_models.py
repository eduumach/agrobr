"""Testes para os modelos NASA POWER."""

from agrobr.nasa_power.models import COLUNAS_MAP, PARAMS_AG, UF_COORDS


class TestUFCoords:
    def test_all_27_ufs(self):
        assert len(UF_COORDS) == 27

    def test_main_agricultural_ufs_present(self):
        for uf in ["MT", "SP", "PR", "GO", "MS", "BA", "MG", "RS"]:
            assert uf in UF_COORDS, f"UF {uf} ausente"

    def test_coords_valid_ranges(self):
        for uf, (lat, lon) in UF_COORDS.items():
            assert -34.0 <= lat <= 6.0, f"{uf}: latitude {lat} fora do Brasil"
            assert -74.0 <= lon <= -35.0, f"{uf}: longitude {lon} fora do Brasil"


class TestParamsAG:
    def test_has_7_params(self):
        assert len(PARAMS_AG) == 7

    def test_expected_params(self):
        expected = {"T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M"}
        assert set(PARAMS_AG) == expected


class TestColunasMap:
    def test_maps_all_params(self):
        for param in PARAMS_AG:
            assert param in COLUNAS_MAP, f"Parametro {param} sem mapeamento"

    def test_output_names(self):
        expected = {
            "temp_media",
            "temp_max",
            "temp_min",
            "precip_mm",
            "umidade_rel",
            "radiacao_mj",
            "vento_ms",
        }
        assert set(COLUNAS_MAP.values()) == expected
