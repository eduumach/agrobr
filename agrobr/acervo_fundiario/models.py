from __future__ import annotations

from agrobr.constants import URLS, Fonte

WFS_BASE: str = URLS[Fonte.ACERVO_FUNDIARIO]["wfs"]
WFS_VERSION = "1.0.0"

NS_GML = "http://www.opengis.net/gml"
NS_MS = "http://www.omsug.ca/osgis2004"


# ---------------------------------------------------------------------------
# SIGEF — parcelas certificadas pos-2013
# ---------------------------------------------------------------------------

SIGEF_LAYERS: dict[str, str] = {
    "particular": "certificada_sigef_particular",
    "publico": "certificada_sigef_publico",
}

TIPOS_SIGEF = frozenset({"particular", "publico"})

SIGEF_PROPERTY_NAMES = [
    "parcela_codigo",
    "rt",
    "art",
    "situacao_informada",
    "codigo_imovel",
    "data_submissao",
    "data_aprovacao",
    "status",
    "nome_area",
    "registro_matricula",
    "registro_data",
    "codigo_municipio",
]

SIGEF_RENAME_MAP: dict[str, str] = {
    "parcela_codigo": "codigo_parcela",
    "rt": "rt",
    "art": "art",
    "situacao_informada": "situacao",
    "codigo_imovel": "codigo_imovel",
    "data_submissao": "data_submissao",
    "data_aprovacao": "data_aprovacao",
    "status": "status",
    "nome_area": "nome_area",
    "registro_matricula": "registro_matricula",
    "registro_data": "registro_data",
    "codigo_municipio": "cod_municipio",
}

SIGEF_COLUNAS_SAIDA = [
    "codigo_parcela",
    "rt",
    "art",
    "situacao",
    "codigo_imovel",
    "data_submissao",
    "data_aprovacao",
    "status",
    "nome_area",
    "registro_matricula",
    "registro_data",
    "cod_municipio",
]

SIGEF_COLUNAS_SAIDA_GEO = SIGEF_COLUNAS_SAIDA + ["geometry"]

SIGEF_DATE_COLS = ["data_submissao", "data_aprovacao"]

SIGEF_REQUIRED_COLS = frozenset({"parcela_codigo", "codigo_imovel", "status"})

MAX_FEATURES_SIGEF = 50_000


# ---------------------------------------------------------------------------
# SNCI — parcelas certificadas pre-2013
# ---------------------------------------------------------------------------

SNCI_LAYERS: dict[str, str] = {
    "privado": "imoveiscertificados_privado",
    "publico": "imoveiscertificados_publico",
}

TIPOS_SNCI = frozenset({"privado", "publico"})

SNCI_PROPERTY_NAMES = [
    "id1",
    "num_processo",
    "sr",
    "num_certificacao",
    "data_certificacao",
    "qtd_area_peca_tecnica",
    "cod_profissional_credenciado",
    "cod_imovel_rural",
    "nome_imovel",
]

SNCI_RENAME_MAP: dict[str, str] = {
    "id1": "id",
    "num_processo": "num_processo",
    "sr": "sr",
    "num_certificacao": "num_certificacao",
    "data_certificacao": "data_certificacao",
    "qtd_area_peca_tecnica": "area_peca_tecnica",
    "cod_profissional_credenciado": "cod_profissional",
    "cod_imovel_rural": "cod_imovel_rural",
    "nome_imovel": "nome_imovel",
}

SNCI_COLUNAS_SAIDA = [
    "id",
    "num_processo",
    "sr",
    "num_certificacao",
    "data_certificacao",
    "area_peca_tecnica",
    "cod_profissional",
    "cod_imovel_rural",
    "nome_imovel",
]

SNCI_COLUNAS_SAIDA_GEO = SNCI_COLUNAS_SAIDA + ["geometry"]

SNCI_NUMERIC_COLS = frozenset({"area_peca_tecnica"})

SNCI_DATE_COLS = ["data_certificacao"]

SNCI_REQUIRED_COLS = frozenset({"id1", "cod_imovel_rural"})

MAX_FEATURES_SNCI = 50_000


# ---------------------------------------------------------------------------
# Assentamentos — projetos de reforma agraria
# ---------------------------------------------------------------------------

ASSENTAMENTOS_LAYER = "assentamentos"

ASSENTAMENTOS_PROPERTY_NAMES = [
    "gid",
    "cd_sipra",
    "nome_projeto",
    "municipio",
    "area_hectare_declarada",
    "capacidade",
    "num_familias",
    "fase",
    "data_de_criacao",
    "forma_obtencao",
    "data_obtencao",
    "area_calc_ha",
    "sr",
    "descricao_fase",
]

ASSENTAMENTOS_RENAME_MAP: dict[str, str] = {
    "gid": "gid",
    "cd_sipra": "codigo_sipra",
    "nome_projeto": "nome_projeto",
    "municipio": "municipio",
    "area_hectare_declarada": "area_ha",
    "capacidade": "capacidade",
    "num_familias": "num_familias",
    "fase": "fase",
    "data_de_criacao": "data_criacao",
    "forma_obtencao": "forma_obtencao",
    "data_obtencao": "data_obtencao",
    "area_calc_ha": "area_calc_ha",
    "sr": "sr",
    "descricao_fase": "descricao_fase",
}

ASSENTAMENTOS_COLUNAS_SAIDA = [
    "gid",
    "codigo_sipra",
    "nome_projeto",
    "municipio",
    "area_ha",
    "capacidade",
    "num_familias",
    "fase",
    "data_criacao",
    "forma_obtencao",
    "data_obtencao",
    "area_calc_ha",
    "sr",
    "descricao_fase",
]

ASSENTAMENTOS_COLUNAS_SAIDA_GEO = ASSENTAMENTOS_COLUNAS_SAIDA + ["geometry"]

ASSENTAMENTOS_NUMERIC_COLS = frozenset({"area_ha", "capacidade", "num_familias", "area_calc_ha"})

ASSENTAMENTOS_DATE_COLS = ["data_criacao", "data_obtencao"]

ASSENTAMENTOS_REQUIRED_COLS = frozenset({"cd_sipra", "nome_projeto", "municipio"})

MAX_FEATURES_ASSENTAMENTOS = 10_000
