from __future__ import annotations

from agrobr.constants import URLS, Fonte
from agrobr.utils.geo import LayerConfig

ANA_BASE: str = URLS[Fonte.ANA]["arcgis"]

LAYERS: dict[str, LayerConfig] = {
    "hidrografia": {
        "service_path": "Hidrografia/FeatureServer/0",
        "max_record_count": 1000,
        "fields": "OBJECTID,COCURSODAG,NORIOCOMP,NUCOMPam,NUAREAAM2,NUNIVOTTO,COBESSION",
        "rename_map": {
            "COCURSODAG": "codigo_curso",
            "NORIOCOMP": "nome_rio",
            "NUCOMPam": "comprimento_m",
            "NUAREAAM2": "area_m2",
            "NUNIVOTTO": "nivel_otto",
            "COBESSION": "codigo_bacia",
        },
        "colunas_saida": [
            "OBJECTID",
            "codigo_curso",
            "nome_rio",
            "comprimento_m",
            "area_m2",
            "nivel_otto",
            "codigo_bacia",
        ],
        "required_cols": {"COCURSODAG"},
    },
    "pivos_irrigacao": {
        "service_path": "Pivos_Mapeados/FeatureServer/0",
        "max_record_count": 1000,
        "fields": "OBJECTID,UF,MUNICIPIO,AREA_HA,ANO_MAPEA,LATITUDE,LONGITUDE",
        "rename_map": {
            "MUNICIPIO": "municipio",
            "AREA_HA": "area_ha",
            "ANO_MAPEA": "ano_mapeamento",
            "LATITUDE": "lat",
            "LONGITUDE": "lon",
        },
        "colunas_saida": [
            "OBJECTID",
            "UF",
            "municipio",
            "area_ha",
            "ano_mapeamento",
            "lat",
            "lon",
        ],
        "required_cols": {"UF"},
    },
    "demanda_irrigacao": {
        "service_path": "Demanda_de_Irrigacao_por_Ottobacia/FeatureServer/0",
        "max_record_count": 1000,
        "fields": "OBJECTID,COBESSION,NUNIVOTTO,NUDEMam3S,NUDEMAM3A",
        "rename_map": {
            "COBESSION": "codigo_bacia",
            "NUNIVOTTO": "nivel_otto",
            "NUDEMam3S": "demanda_m3_s",
            "NUDEMAM3A": "demanda_m3_ano",
        },
        "colunas_saida": [
            "OBJECTID",
            "codigo_bacia",
            "nivel_otto",
            "demanda_m3_s",
            "demanda_m3_ano",
        ],
        "required_cols": {"COBESSION"},
    },
    "disponibilidade_hidrica": {
        "service_path": "Disponibilidade_Hidrica_Superficial/FeatureServer/0",
        "max_record_count": 1000,
        "fields": "OBJECTID,COCURSODAG,NORIOCOMP,Q95_L_S,QMLT_L_S,COBESSION",
        "rename_map": {
            "COCURSODAG": "codigo_curso",
            "NORIOCOMP": "nome_rio",
            "Q95_L_S": "q95_l_s",
            "QMLT_L_S": "qmlt_l_s",
            "COBESSION": "codigo_bacia",
        },
        "colunas_saida": [
            "OBJECTID",
            "codigo_curso",
            "nome_rio",
            "q95_l_s",
            "qmlt_l_s",
            "codigo_bacia",
        ],
        "required_cols": {"COCURSODAG"},
    },
}
