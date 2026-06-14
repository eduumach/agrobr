from __future__ import annotations

FORMULADOS_RENAME: dict[str, str] = {
    "NR_REGISTRO": "nr_registro",
    "MARCA_COMERCIAL": "marca_comercial",
    "INGREDIENTE_ATIVO": "ingrediente_ativo",
    "TITULAR_DE_REGISTRO": "titular",
    "CLASSE": "classe",
    "FORMULACAO": "formulacao",
    "CLASSE_TOXICOLOGICA": "classe_toxicologica",
    "CLASSIFICACAO_AMBIENTAL": "classe_ambiental",
    "CLASSE_AMBIENTAL": "classe_ambiental",
    "ORGANICOS": "organicos",
    "MODO_DE_ACAO": "modo_de_acao",
    "CULTURA": "cultura",
    "PRAGA_NOME_CIENTIFICO": "praga",
    "PRAGA_NOME_COMUM": "praga_nome_comum",
    "MODALIDADE_DE_EMPREGO": "modalidade_de_emprego",
}

TECNICOS_RENAME: dict[str, str] = {
    "NR_REGISTRO": "nr_registro",
    "NUMERO_REGISTRO": "nr_registro",
    "MARCA_COMERCIAL": "marca_comercial",
    "PRODUTO_TECNICO_MARCA_COMERCIAL": "marca_comercial",
    "INGREDIENTE_ATIVO": "ingrediente_ativo",
    "TITULAR_DE_REGISTRO": "titular",
    "TITULAR_REGISTRO": "titular",
    "CLASSE": "classe",
    "GRUPO_QUIMICI": "grupo_quimico",
    "NOME_CIENTIFICO": "nome_cientifico",
    "CLASSIFICACAO_TOXICOLOGICA": "classe_toxicologica",
    "CLASSIFICACAO_AMBIENTAL": "classe_ambiental",
}

FORMULADOS_PRODUCT_COLS: list[str] = [
    "nr_registro",
    "marca_comercial",
    "ingrediente_ativo",
    "titular",
    "classe",
    "formulacao",
    "classe_toxicologica",
    "classe_ambiental",
    "organicos",
    "modo_de_acao",
]

AUTORIZACOES_COLS: list[str] = [
    "nr_registro",
    "marca_comercial",
    "ingrediente_ativo",
    "titular",
    "classe",
    "cultura",
    "praga",
    "praga_nome_comum",
    "modalidade_de_emprego",
]

TECNICOS_COLS: list[str] = [
    "nr_registro",
    "marca_comercial",
    "ingrediente_ativo",
    "titular",
    "classe",
    "grupo_quimico",
    "nome_cientifico",
    "classe_toxicologica",
    "classe_ambiental",
]

FORMULADOS_COLS_DROP: list[str] = [
    "EMPRESA_PAIS_TIPO",
    "EMPRESA_<PAIS>_TIPO",
    "SITUACAO",
]

TECNICOS_COLS_DROP: list[str] = [
    "EMPRESA_PAIS_TIPO",
    "EMPRESA_<PAIS>_TIPO",
]
