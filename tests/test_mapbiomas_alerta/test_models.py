from agrobr.mapbiomas_alerta.models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    GRAPHQL_URL,
    RENAME_MAP,
)


class TestGraphqlUrl:
    def test_contains_graphql(self):
        assert "graphql" in GRAPHQL_URL or "mapbiomas" in GRAPHQL_URL

    def test_starts_with_https(self):
        assert GRAPHQL_URL.startswith("https://")


class TestRenameMap:
    def test_alert_code_key(self):
        assert "alertCode" in RENAME_MAP
        assert RENAME_MAP["alertCode"] == "alert_code"

    def test_area_ha_key(self):
        assert "areaHa" in RENAME_MAP
        assert RENAME_MAP["areaHa"] == "area_ha"

    def test_no_source_key(self):
        assert "source" not in RENAME_MAP

    def test_no_state_key(self):
        assert "state" not in RENAME_MAP


class TestColunasSaida:
    def test_alert_code_present(self):
        assert "alert_code" in COLUNAS_SAIDA

    def test_no_geometry(self):
        assert "geometry" not in COLUNAS_SAIDA

    def test_lat_lon_present(self):
        assert "lat" in COLUNAS_SAIDA
        assert "lon" in COLUNAS_SAIDA

    def test_fonte_present(self):
        assert "fonte" in COLUNAS_SAIDA

    def test_no_bioma(self):
        assert "bioma" not in COLUNAS_SAIDA

    def test_no_uf(self):
        assert "uf" not in COLUNAS_SAIDA

    def test_no_municipio(self):
        assert "municipio" not in COLUNAS_SAIDA


class TestColunasSaidaGeo:
    def test_geometry_present(self):
        assert "geometry" in COLUNAS_SAIDA_GEO

    def test_superset_of_tabular(self):
        assert set(COLUNAS_SAIDA).issubset(COLUNAS_SAIDA_GEO)
