from __future__ import annotations

from agrobr.constants import URLS, Fonte

WFS_BASE: str = URLS[Fonte.EMBRAPA_SOLOS]["geoserver"]
WFS_VERSION = "2.0.0"

PERFIS_NAMESPACE = "geonode"
PERFIS_LAYER = "perfis_pronasolos_2020"
PERFIS_PAGE_SIZE = 5_000
PERFIS_MAX_FEATURES_GEO = 5_000

PERFIS_PROPERTY_NAMES: list[str] = [
    "fid",
    "nivel_leva",
    "uso_atual",
    "gcs_latitu",
    "gcs_longit",
    "municipio",
    "uf",
    "simbolo_ho",
    "profundida",
    "areia_tota",
    "silte",
    "argila",
    "ph_h2o",
    "carbono_or",
    "valor_t",
    "valor_v",
    "aluminio_t",
    "fosforo_as",
    "classe_tex",
]

PERFIS_GEOM_COLUMN = "geom"
PERFIS_PROPERTY_NAMES_GEO: list[str] = [PERFIS_GEOM_COLUMN] + PERFIS_PROPERTY_NAMES

PERFIS_RENAME_MAP: dict[str, str] = {
    "gcs_latitu": "latitude",
    "gcs_longit": "longitude",
    "simbolo_ho": "horizonte",
    "profundida": "profundidade",
    "areia_tota": "areia_total",
    "carbono_or": "carbono_organico",
    "valor_t": "ctc",
    "valor_v": "saturacao_bases",
    "aluminio_t": "aluminio",
    "fosforo_as": "fosforo",
    "classe_tex": "classe_textural",
    "nivel_leva": "nivel_levantamento",
}

PERFIS_COLUNAS_SAIDA: list[str] = [
    "fid",
    "uf",
    "municipio",
    "latitude",
    "longitude",
    "horizonte",
    "profundidade",
    "areia_total",
    "silte",
    "argila",
    "ph_h2o",
    "carbono_organico",
    "ctc",
    "saturacao_bases",
    "aluminio",
    "fosforo",
    "classe_textural",
    "nivel_levantamento",
    "uso_atual",
]

PERFIS_COLUNAS_SAIDA_GEO: list[str] = PERFIS_COLUNAS_SAIDA + ["geometry"]

PERFIS_NUMERIC_COLS: frozenset[str] = frozenset(
    {
        "latitude",
        "longitude",
        "areia_total",
        "silte",
        "argila",
        "ph_h2o",
        "carbono_organico",
        "ctc",
        "saturacao_bases",
        "aluminio",
        "fosforo",
    }
)

_REQUIRED_PERFIS: set[str] = {"fid", "uf", "gcs_latitu", "gcs_longit"}

MAPA_NAMESPACE = "geonode"
MAPA_LAYER = "brasil_solos_5m_20201104"
MAPA_PAGE_SIZE = 500
MAPA_MAX_FEATURES_GEO = 3_000

MAPA_PROPERTY_NAMES: list[str] = [
    "ogc_fid",
    "simbolos",
    "comp1",
    "comp2",
    "comp3",
    "leg_desc",
    "area_km2",
    "ordem1",
    "subordem1",
    "gdegrupo1",
    "ordem2",
    "subordem2",
    "gdegrupo2",
    "leg_sinot",
    "classe_dom",
]

MAPA_GEOM_COLUMN = "geometry"
MAPA_PROPERTY_NAMES_GEO: list[str] = [MAPA_GEOM_COLUMN] + MAPA_PROPERTY_NAMES

MAPA_RENAME_MAP: dict[str, str] = {
    "ogc_fid": "fid",
    "leg_desc": "legenda",
    "leg_sinot": "legenda_sinotica",
}

MAPA_COLUNAS_SAIDA: list[str] = [
    "fid",
    "simbolos",
    "comp1",
    "comp2",
    "comp3",
    "legenda",
    "area_km2",
    "ordem1",
    "subordem1",
    "gdegrupo1",
    "ordem2",
    "subordem2",
    "gdegrupo2",
    "legenda_sinotica",
    "classe_dom",
]

MAPA_COLUNAS_SAIDA_GEO: list[str] = MAPA_COLUNAS_SAIDA + ["geometry"]

_REQUIRED_MAPA: set[str] = {"ogc_fid", "classe_dom"}
