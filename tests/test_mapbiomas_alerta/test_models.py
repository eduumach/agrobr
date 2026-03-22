from agrobr.mapbiomas_alerta.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    GRAPHQL_URL,
    RENAME_MAP,
    SOURCES_VALIDOS,
)


class TestGraphqlUrl:
    def test_contains_graphql(self):
        assert "graphql" in GRAPHQL_URL or "mapbiomas" in GRAPHQL_URL

    def test_starts_with_https(self):
        assert GRAPHQL_URL.startswith("https://")


class TestSourcesValidos:
    def test_deter_present(self):
        assert "DETER" in SOURCES_VALIDOS

    def test_sad_present(self):
        assert "SAD" in SOURCES_VALIDOS

    def test_glad_present(self):
        assert "GLAD" in SOURCES_VALIDOS

    def test_minimum_count(self):
        assert len(SOURCES_VALIDOS) >= 4


class TestRenameMap:
    def test_alert_code_key(self):
        assert "alertCode" in RENAME_MAP
        assert RENAME_MAP["alertCode"] == "alert_code"

    def test_area_ha_key(self):
        assert "areaHa" in RENAME_MAP
        assert RENAME_MAP["areaHa"] == "area_ha"

    def test_state_maps_to_uf(self):
        assert "state" in RENAME_MAP
        assert RENAME_MAP["state"] == "uf"


class TestColunasSaida:
    def test_alert_code_present(self):
        assert "alert_code" in COLUNAS_SAIDA

    def test_no_geometry(self):
        assert "geometry" not in COLUNAS_SAIDA

    def test_lat_lon_present(self):
        assert "lat" in COLUNAS_SAIDA
        assert "lon" in COLUNAS_SAIDA


class TestColunasSaidaGeo:
    def test_geometry_present(self):
        assert "geometry" in COLUNAS_SAIDA_GEO

    def test_superset_of_tabular(self):
        assert set(COLUNAS_SAIDA).issubset(COLUNAS_SAIDA_GEO)
