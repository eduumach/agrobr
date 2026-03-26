from __future__ import annotations

REGISTRADAS_RENAME: dict[str, str] = {
    "CULTIVAR": "cultivar",
    "NOME COMUM": "nome_comum",
    "NOME CIENTÍFICO": "nome_cientifico",
    "GRUPO DA ESPÉCIE": "grupo",
    "SITUAÇÃO": "situacao",
    "Nº FORMULÁRIO": "nr_formulario",
    "Nº REGISTRO": "nr_registro",
    "DATA DO REGISTRO": "data_registro",
    "DATA DE VALIDADE DO REGISTRO": "data_validade",
    "MANTENEDOR (REQUERENTE) (NOME)": "mantenedor",
}

PROTEGIDAS_RENAME: dict[str, str] = {
    "CULTIVAR": "cultivar",
    "NOME CIENTÍFICO": "nome_cientifico",
    "NOME COMUM": "nome_comum",
    "Nº PROCESSO": "nr_processo",
    "SITUAÇÃO": "situacao",
    "Nº CERTIFICADO": "nr_certificado",
    "INÍCIO DA PROTEÇÃO": "inicio_protecao",
    "TÉRMINO DA PROTEÇÃO": "termino_protecao",
    "TITULAR (NOME)": "titular",
    "REPRESENANTE LEGAL (NOME) ": "representante_legal",
    "MELHORISTAS": "melhoristas",
}

REGISTRADAS_COLS: list[str] = [
    "cultivar",
    "nome_comum",
    "nome_cientifico",
    "grupo",
    "situacao",
    "nr_formulario",
    "nr_registro",
    "data_registro",
    "data_validade",
    "mantenedor",
]

PROTEGIDAS_COLS: list[str] = [
    "cultivar",
    "nome_cientifico",
    "nome_comum",
    "nr_processo",
    "situacao",
    "nr_certificado",
    "inicio_protecao",
    "termino_protecao",
    "titular",
    "representante_legal",
    "melhoristas",
]

DATE_COLS_REG: list[str] = ["data_registro", "data_validade"]
DATE_COLS_PROT: list[str] = ["inicio_protecao", "termino_protecao"]

_REQUIRED_REG: frozenset[str] = frozenset({"CULTIVAR", "Nº REGISTRO", "DATA DO REGISTRO"})
_REQUIRED_PROT: frozenset[str] = frozenset({"CULTIVAR", "Nº CERTIFICADO", "SITUAÇÃO"})
