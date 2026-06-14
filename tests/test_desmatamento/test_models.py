from __future__ import annotations

from agrobr.desmatamento.models import (
    BIOMAS_VALIDOS,
    COLUNAS_SAIDA_DETER,
    COLUNAS_SAIDA_DETER_GEO,
    COLUNAS_SAIDA_PRODES,
    COLUNAS_SAIDA_PRODES_GEO,
    DETER_COLUNAS_WFS_GEO_AMZ,
    DETER_COLUNAS_WFS_GEO_CERRADO,
    DETER_LAYERS,
    DETER_WORKSPACES,
    MAX_FEATURES_GEO,
    PRODES_GEOM_COLUMN,
    PRODES_LAYERS,
    PRODES_WORKSPACES,
    UF_ESTADO,
    estado_para_uf,
    normalizar_bioma,
)


class TestNormalizarBioma:
    def test_amazonia_lowercase(self):
        assert normalizar_bioma("amazonia") == "Amazônia"

    def test_amazonia_accented(self):
        assert normalizar_bioma("amazônia") == "Amazônia"

    def test_cerrado(self):
        assert normalizar_bioma("cerrado") == "Cerrado"

    def test_mata_atlantica(self):
        assert normalizar_bioma("mata atlantica") == "Mata Atlântica"

    def test_mata_atlantica_accented(self):
        assert normalizar_bioma("mata atlântica") == "Mata Atlântica"

    def test_caatinga(self):
        assert normalizar_bioma("caatinga") == "Caatinga"

    def test_pampa(self):
        assert normalizar_bioma("pampa") == "Pampa"

    def test_pantanal(self):
        assert normalizar_bioma("pantanal") == "Pantanal"

    def test_unknown_passthrough(self):
        assert normalizar_bioma("desconhecido") == "desconhecido"

    def test_with_spaces(self):
        assert normalizar_bioma("  cerrado  ") == "Cerrado"


class TestEstadoParaUf:
    def test_mato_grosso(self):
        assert estado_para_uf("MATO GROSSO") == "MT"

    def test_sao_paulo(self):
        assert estado_para_uf("SÃO PAULO") == "SP"

    def test_lowercase(self):
        assert estado_para_uf("mato grosso") == "MT"

    def test_amazonas(self):
        assert estado_para_uf("AMAZONAS") == "AM"

    def test_all_27_ufs(self):
        assert len(UF_ESTADO) == 27

    def test_unknown_passthrough(self):
        assert estado_para_uf("UNKNOWN") == "UNKNOWN"

    def test_rondonia(self):
        assert estado_para_uf("RONDÔNIA") == "RO"

    def test_maranhao(self):
        assert estado_para_uf("MARANHÃO") == "MA"


class TestConstants:
    def test_biomas_validos_has_6(self):
        assert len(BIOMAS_VALIDOS) == 6

    def test_prodes_workspaces_non_empty(self):
        assert len(PRODES_WORKSPACES) == 6
        assert "Cerrado" in PRODES_WORKSPACES
        assert PRODES_WORKSPACES["Amazônia"] == "prodes-amazon-nb"

    def test_prodes_layers_six_biomes(self):
        assert len(PRODES_LAYERS) == 6
        assert PRODES_LAYERS["Amazônia"] == "yearly_deforestation_biome"
        assert PRODES_LAYERS["Cerrado"] == "yearly_deforestation"
        assert PRODES_LAYERS["Caatinga"] == "yearly_deforestation"
        assert PRODES_LAYERS["Mata Atlântica"] == "yearly_deforestation"
        assert PRODES_LAYERS["Pantanal"] == "yearly_deforestation"
        assert PRODES_LAYERS["Pampa"] == "yearly_deforestation"

    def test_prodes_geom_column(self):
        assert PRODES_GEOM_COLUMN == "geom"

    def test_prodes_geo_output_columns_has_geometry(self):
        assert "geometry" in COLUNAS_SAIDA_PRODES_GEO
        for col in COLUNAS_SAIDA_PRODES:
            assert col in COLUNAS_SAIDA_PRODES_GEO

    def test_deter_workspaces_two_biomes(self):
        assert len(DETER_WORKSPACES) == 2
        assert "Amazônia" in DETER_WORKSPACES
        assert "Cerrado" in DETER_WORKSPACES

    def test_deter_layers_two_biomes(self):
        assert len(DETER_LAYERS) == 2
        assert "Amazônia" in DETER_LAYERS
        assert "Cerrado" in DETER_LAYERS

    def test_colunas_saida_prodes(self):
        assert "ano" in COLUNAS_SAIDA_PRODES
        assert "uf" in COLUNAS_SAIDA_PRODES
        assert "area_km2" in COLUNAS_SAIDA_PRODES
        assert "bioma" in COLUNAS_SAIDA_PRODES

    def test_colunas_saida_deter(self):
        assert "data" in COLUNAS_SAIDA_DETER
        assert "classe" in COLUNAS_SAIDA_DETER
        assert "uf" in COLUNAS_SAIDA_DETER
        assert "area_km2" in COLUNAS_SAIDA_DETER
        assert "municipio" in COLUNAS_SAIDA_DETER
        assert "bioma" in COLUNAS_SAIDA_DETER

    def test_geo_columns_amz_includes_geom(self):
        assert "geom" in DETER_COLUNAS_WFS_GEO_AMZ

    def test_geo_columns_cerrado_includes_st_multi(self):
        assert "st_multi" in DETER_COLUNAS_WFS_GEO_CERRADO

    def test_geo_output_columns_has_geometry(self):
        assert "geometry" in COLUNAS_SAIDA_DETER_GEO

    def test_max_features_geo(self):
        assert MAX_FEATURES_GEO == 10_000
