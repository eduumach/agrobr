from __future__ import annotations

from agrobr.constants import URLS, Fonte
from agrobr.utils.geo import LayerConfig

SFB_BASE: str = URLS[Fonte.SFB]["arcgis"]

LAYERS: dict[str, LayerConfig] = {
    "cnfp": {
        "service_path": "Hosted/CNFP_v19_03_retificado_17072025/FeatureServer/9",
        "max_record_count": 2000,
        "fields": "fid,nome,uf,bioma,categoria,tipo,governo,classe,area_ha,anocriacao,municipio",
        "rename_map": {
            "anocriacao": "ano_criacao",
        },
        "colunas_saida": [
            "fid",
            "nome",
            "uf",
            "bioma",
            "categoria",
            "tipo",
            "governo",
            "classe",
            "area_ha",
            "ano_criacao",
            "municipio",
        ],
        "required_cols": {"nome", "uf"},
    },
    "concessoes": {
        "service_path": "Hosted/unidades_concessoes_florestais/FeatureServer/0",
        "max_record_count": 2000,
        "fields": "fid,nome_uc,uf,bioma,hectares,criacao,grupo,cat_nome",
        "rename_map": {
            "nome_uc": "nome",
            "hectares": "area_ha",
            "criacao": "ano_criacao",
            "cat_nome": "categoria",
        },
        "colunas_saida": [
            "fid",
            "nome",
            "uf",
            "bioma",
            "area_ha",
            "ano_criacao",
            "grupo",
            "categoria",
        ],
        "required_cols": {"nome_uc"},
    },
    "ifn_conglomerados": {
        "service_path": "DadosAbertos-IFN/Conglomerado/FeatureServer/0",
        "max_record_count": 2000,
        "fields": "co_pontos_lote,co_lote,no_lote,no_conglomerado,no_uf,no_municipio,no_bioma",
        "rename_map": {
            "co_pontos_lote": "id",
            "co_lote": "codigo_lote",
            "no_lote": "lote",
            "no_conglomerado": "conglomerado",
            "no_uf": "uf",
            "no_municipio": "municipio",
            "no_bioma": "bioma",
        },
        "colunas_saida": [
            "id",
            "codigo_lote",
            "lote",
            "conglomerado",
            "uf",
            "municipio",
            "bioma",
        ],
        "required_cols": {"no_uf"},
    },
}
