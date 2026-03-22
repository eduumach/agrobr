from __future__ import annotations

from agrobr.constants import URLS, Fonte

WFS_BASE: str = URLS[Fonte.INCRA]["geoserver"]
WFS_VERSION = "1.0.0"
LAYER = "lim_quilombolas_a"
NAMESPACE = "CMR-PUBLICO"
GEOM_COLUMN = "geom"
MAX_FEATURES_GEO = 500
MAX_FEATURES_TABULAR = 500

PROPERTY_NAMES = [
    "cd_quilomb",
    "no_comunidade",
    "no_municipio",
    "sg_uf",
    "nu_area_ha",
    "nu_familia",
    "ds_fase",
    "st_titulad",
    "dt_publica",
    "dt_titulo",
]

PROPERTY_NAMES_GEO = [GEOM_COLUMN] + PROPERTY_NAMES

RENAME_MAP: dict[str, str] = {
    "cd_quilomb": "codigo",
    "no_comunidade": "nome",
    "no_municipio": "municipio",
    "sg_uf": "uf",
    "nu_area_ha": "area_ha",
    "nu_familia": "familias",
    "ds_fase": "fase",
    "st_titulad": "titulado",
    "dt_publica": "data_publicacao",
    "dt_titulo": "data_titulo",
}

COLUNAS_SAIDA = [
    "codigo",
    "nome",
    "municipio",
    "uf",
    "area_ha",
    "familias",
    "fase",
    "titulado",
    "data_publicacao",
    "data_titulo",
]

COLUNAS_SAIDA_GEO = COLUNAS_SAIDA + ["geometry"]
