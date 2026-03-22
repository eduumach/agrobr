from __future__ import annotations

from agrobr.constants import URLS, Fonte
from agrobr.utils.geo import LayerConfig

SFB_BASE: str = URLS[Fonte.SFB]["arcgis"]

LAYERS: dict[str, LayerConfig] = {
    "cnfp": {
        "service_path": "Hosted/CNFP_v19_03_retificado_17072025/FeatureServer/9",
        "max_record_count": 2000,
        "fields": "OBJECTID,NM_FLORPUB,UF,BIOMA,CATEGORIA,TIPO,AREA_HA,ANO_CRIACAO",
        "rename_map": {
            "NM_FLORPUB": "nome",
            "AREA_HA": "area_ha",
            "ANO_CRIACAO": "ano_criacao",
            "CATEGORIA": "categoria",
            "TIPO": "tipo",
            "BIOMA": "bioma",
        },
        "colunas_saida": [
            "OBJECTID",
            "nome",
            "UF",
            "bioma",
            "categoria",
            "tipo",
            "area_ha",
            "ano_criacao",
        ],
        "required_cols": {"NM_FLORPUB", "UF"},
    },
    "concessoes": {
        "service_path": "Hosted/unidades_concessoes_florestais/FeatureServer/0",
        "max_record_count": 2000,
        "fields": "OBJECTID,NOME,UF,AREA_HA,STATUS,ANO_CONTRATO",
        "rename_map": {
            "NOME": "nome",
            "AREA_HA": "area_ha",
            "STATUS": "status",
            "ANO_CONTRATO": "ano_contrato",
        },
        "colunas_saida": [
            "OBJECTID",
            "nome",
            "UF",
            "area_ha",
            "status",
            "ano_contrato",
        ],
        "required_cols": {"NOME"},
    },
    "ifn_conglomerados": {
        "service_path": "DadosAbertos_IFN/Conglomerado/FeatureServer/0",
        "max_record_count": 2000,
        "fields": "OBJECTID,UF,BIOMA,NUM_CONGLOMERADO,LATITUDE,LONGITUDE,SITUACAO",
        "rename_map": {
            "NUM_CONGLOMERADO": "numero",
            "BIOMA": "bioma",
            "LATITUDE": "lat",
            "LONGITUDE": "lon",
            "SITUACAO": "situacao",
        },
        "colunas_saida": [
            "OBJECTID",
            "UF",
            "bioma",
            "numero",
            "lat",
            "lon",
            "situacao",
        ],
        "required_cols": {"UF"},
    },
}
