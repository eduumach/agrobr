from __future__ import annotations

from agrobr.constants import URLS, Fonte
from agrobr.normalize.regions import UFS_VALIDAS as UFS_VALIDAS

WFS_BASE = URLS[Fonte.SICAR]["geoserver"]
WFS_VERSION = "2.0.0"

PAGE_SIZE = 10_000
MAX_FEATURES_WARNING = 100_000


def layer_name(uf: str) -> str:
    return f"sicar_imoveis_{uf.lower()}"


PROPERTY_NAMES = [
    "cod_imovel",
    "status_imovel",
    "dat_criacao",
    "area",
    "condicao",
    "uf",
    "municipio",
    "cod_municipio_ibge",
    "m_fiscal",
    "tipo_imovel",
]

RENAME_MAP = {
    "status_imovel": "status",
    "dat_criacao": "data_criacao",
    "area": "area_ha",
    "m_fiscal": "modulos_fiscais",
    "tipo_imovel": "tipo",
}

COLUNAS_IMOVEIS = [
    "cod_imovel",
    "status",
    "data_criacao",
    "data_atualizacao",
    "area_ha",
    "condicao",
    "uf",
    "municipio",
    "cod_municipio_ibge",
    "modulos_fiscais",
    "tipo",
]

STATUS_VALIDOS = frozenset({"AT", "PE", "SU", "CA"})

TIPO_VALIDOS = frozenset({"IRU", "AST", "PCT"})

MAX_FEATURES_GEO = 5_000

SICAR_GEOM_COLUMN = "geo_area_imovel"

PROPERTY_NAMES_GEO = [SICAR_GEOM_COLUMN] + PROPERTY_NAMES

COLUNAS_IMOVEIS_GEO = COLUNAS_IMOVEIS + ["geometry"]
