from __future__ import annotations

from agrobr.constants import URLS, Fonte

WFS_BASE: str = URLS[Fonte.ICMBIO]["geoserver"]
WFS_VERSION = "1.1.0"
LAYER = "limiteucsfederais_a"
NAMESPACE = "ICMBio"
GEOM_COLUMN = "the_geom"
MAX_FEATURES_GEO = 500
MAX_FEATURES_TABULAR = 500

PROPERTY_NAMES = [
    "cnuc",
    "nomeuc",
    "siglacateg",
    "grupouc",
    "areahaalb",
    "ufabrang",
    "biomas",
    "criacaoano",
    "criacaoato",
]

PROPERTY_NAMES_GEO = [GEOM_COLUMN] + PROPERTY_NAMES

RENAME_MAP: dict[str, str] = {
    "cnuc": "codigo",
    "nomeuc": "nome",
    "siglacateg": "categoria",
    "grupouc": "grupo",
    "areahaalb": "area_ha",
    "ufabrang": "uf",
    "biomas": "bioma",
    "criacaoano": "ano_criacao",
    "criacaoato": "ato_criacao",
}

COLUNAS_SAIDA = [
    "codigo",
    "nome",
    "categoria",
    "grupo",
    "uf",
    "bioma",
    "area_ha",
    "ano_criacao",
    "ato_criacao",
]

COLUNAS_SAIDA_GEO = COLUNAS_SAIDA + ["geometry"]

GRUPOS_VALIDOS = frozenset({"PI", "US"})
