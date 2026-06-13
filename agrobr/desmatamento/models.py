from __future__ import annotations

from agrobr.normalize.regions import BIOMAS as BIOMAS  # noqa: F401
from agrobr.normalize.regions import BIOMAS_VALIDOS as BIOMAS_VALIDOS  # noqa: F401
from agrobr.normalize.regions import normalizar_bioma as normalizar_bioma  # noqa: F401

UF_ESTADO: dict[str, str] = {
    "ACRE": "AC",
    "ALAGOAS": "AL",
    "AMAPÁ": "AP",
    "AMAZONAS": "AM",
    "BAHIA": "BA",
    "CEARÁ": "CE",
    "DISTRITO FEDERAL": "DF",
    "ESPÍRITO SANTO": "ES",
    "GOIÁS": "GO",
    "MARANHÃO": "MA",
    "MATO GROSSO": "MT",
    "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG",
    "PARÁ": "PA",
    "PARAÍBA": "PB",
    "PARANÁ": "PR",
    "PERNAMBUCO": "PE",
    "PIAUÍ": "PI",
    "RIO DE JANEIRO": "RJ",
    "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS",
    "RONDÔNIA": "RO",
    "RORAIMA": "RR",
    "SANTA CATARINA": "SC",
    "SÃO PAULO": "SP",
    "SERGIPE": "SE",
    "TOCANTINS": "TO",
}

PRODES_WORKSPACES: dict[str, str] = {
    "Amazônia": "prodes-amazon-nb",
    "Cerrado": "prodes-cerrado-nb",
    "Caatinga": "prodes-caatinga-nb",
    "Mata Atlântica": "prodes-mata-atlantica-nb",
    "Pantanal": "prodes-pantanal-nb",
    "Pampa": "prodes-pampa-nb",
}

PRODES_LAYERS: dict[str, str] = {
    "Amazônia": "yearly_deforestation_biome",
    "Cerrado": "yearly_deforestation",
    "Caatinga": "yearly_deforestation",
    "Mata Atlântica": "yearly_deforestation",
    "Pantanal": "yearly_deforestation",
    "Pampa": "yearly_deforestation",
}

PRODES_GEOM_COLUMN = "geom"

DETER_WORKSPACES: dict[str, str] = {
    "Amazônia": "deter-amz",
    "Cerrado": "deter-cerrado-nb",
}

DETER_LAYERS: dict[str, str] = {
    "Amazônia": "deter_amz",
    "Cerrado": "deter_cerrado",
}

PRODES_COLUNAS_WFS = [
    "state",
    "main_class",
    "class_name",
    "year",
    "area_km",
    "source",
    "satellite",
    "sensor",
    "path_row",
    "publish_year",
]

DETER_COLUNAS_WFS_AMZ = [
    "classname",
    "quadrant",
    "path_row",
    "view_date",
    "sensor",
    "satellite",
    "areauckm",
    "areamunkm",
    "municipality",
    "mun_geocod",
    "uf",
    "publish_month",
]

DETER_COLUNAS_WFS_CERRADO = [
    "classname",
    "quadrant",
    "path_row",
    "view_date",
    "sensor",
    "satellite",
    "areatotalkm",
    "areauckm",
    "areamunkm",
    "municipality",
    "uf",
    "publish_month",
]

PRODES_COLUNAS_WFS_GEO = [PRODES_GEOM_COLUMN] + PRODES_COLUNAS_WFS

COLUNAS_SAIDA_PRODES = [
    "ano",
    "uf",
    "classe",
    "area_km2",
    "satelite",
    "sensor",
    "bioma",
]

COLUNAS_SAIDA_PRODES_GEO = COLUNAS_SAIDA_PRODES + ["geometry"]

COLUNAS_SAIDA_DETER = [
    "data",
    "classe",
    "uf",
    "municipio",
    "municipio_id",
    "area_km2",
    "satelite",
    "sensor",
    "bioma",
]

MAX_FEATURES_GEO = 10_000

DETER_COLUNAS_WFS_GEO_AMZ = ["geom"] + DETER_COLUNAS_WFS_AMZ
DETER_COLUNAS_WFS_GEO_CERRADO = ["st_multi"] + DETER_COLUNAS_WFS_CERRADO

COLUNAS_SAIDA_DETER_GEO = COLUNAS_SAIDA_DETER + ["geometry"]


def estado_para_uf(estado: str) -> str:
    return UF_ESTADO.get(estado.strip().upper(), estado.strip())
