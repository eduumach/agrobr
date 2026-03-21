from __future__ import annotations

from agrobr.constants import URLS, Fonte

WFS_BASE: str = URLS[Fonte.FUNAI]["geoserver"]
WFS_VERSION = "2.0.0"
LAYER = "tis_poligonais"
NAMESPACE = "Funai"
GEOM_COLUMN = "the_geom"
MAX_FEATURES_GEO = 1_000
MAX_FEATURES_TABULAR = 1_000

PROPERTY_NAMES = [
    "terrai_codigo",
    "terrai_nome",
    "etnia_nome",
    "municipio_nome",
    "uf_sigla",
    "superficie_perimetro_ha",
    "fase_ti",
    "modalidade_ti",
    "data_atualizacao",
]

PROPERTY_NAMES_GEO = [GEOM_COLUMN] + PROPERTY_NAMES

RENAME_MAP: dict[str, str] = {
    "terrai_codigo": "codigo",
    "terrai_nome": "nome",
    "etnia_nome": "etnia",
    "municipio_nome": "municipio",
    "uf_sigla": "uf",
    "superficie_perimetro_ha": "area_ha",
    "fase_ti": "fase",
    "modalidade_ti": "modalidade",
}

COLUNAS_SAIDA = [
    "codigo",
    "nome",
    "etnia",
    "municipio",
    "uf",
    "area_ha",
    "fase",
    "modalidade",
    "data_atualizacao",
]

COLUNAS_SAIDA_GEO = COLUNAS_SAIDA + ["geometry"]

FASES_VALIDAS = frozenset(
    {
        "Regularizada",
        "Homologada",
        "Declarada",
        "Delimitada",
        "Em Estudo",
        "Encaminhada RI",
    }
)
