from __future__ import annotations

from pydantic import BaseModel, field_validator


class _StripBase(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def strip_whitespace(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class ProdutoFormulado(_StripBase):
    nr_registro: str
    marca_comercial: str
    ingrediente_ativo: str | None = None
    titular: str | None = None
    classe: str | None = None
    formulacao: str | None = None
    classe_toxicologica: str | None = None
    classe_ambiental: str | None = None
    organicos: str | None = None
    modo_de_acao: str | None = None


class AutorizacaoUso(_StripBase):
    nr_registro: str
    marca_comercial: str
    ingrediente_ativo: str | None = None
    titular: str | None = None
    classe: str | None = None
    cultura: str | None = None
    praga: str | None = None
    praga_nome_comum: str | None = None
    modalidade_de_emprego: str | None = None


class ProdutoTecnico(_StripBase):
    nr_registro: str
    marca_comercial: str
    ingrediente_ativo: str | None = None
    titular: str | None = None
    classe: str | None = None
    grupo_quimico: str | None = None
    classe_toxicologica: str | None = None
    classe_ambiental: str | None = None


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
