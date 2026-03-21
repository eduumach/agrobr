from agrobr.constants import URLS, Fonte

WFS_BASE: str = URLS[Fonte.IBAMA]["geoserver"]
WFS_VERSION = "2.0.0"
LAYER = "vw_brasil_adm_embargo_a"
NAMESPACE = "publica"
GEOM_COLUMN = "geom"

PAGE_SIZE = 10_000
MAX_FEATURES_GEO = 5_000

PROPERTY_NAMES = [
    "numero_tad",
    "data_tad",
    "sig_uf",
    "nom_municipio",
    "qtd_area_desmatada",
    "des_infracao",
    "legislacao",
    "status_tad",
    "sit_embarga_poligono",
    "respeita_embargo",
]

PROPERTY_NAMES_GEO = [GEOM_COLUMN] + PROPERTY_NAMES

RENAME_MAP: dict[str, str] = {
    "data_tad": "data_embargo",
    "sig_uf": "uf",
    "nom_municipio": "municipio",
    "qtd_area_desmatada": "area_desmatada_ha",
    "des_infracao": "infracao",
    "status_tad": "status",
    "sit_embarga_poligono": "situacao_poligono",
}

COLUNAS_SAIDA = [
    "numero_tad",
    "data_embargo",
    "uf",
    "municipio",
    "area_desmatada_ha",
    "infracao",
    "legislacao",
    "status",
    "situacao_poligono",
    "respeita_embargo",
]

COLUNAS_SAIDA_GEO = COLUNAS_SAIDA + ["geometry"]
