from agrobr.constants import URLS, Fonte

DOWNLOAD_URL: str = URLS[Fonte.LISTA_SUJA]["download"]

RENAME_MAP: dict[str, str] = {
    "EMPREGADOR": "empregador",
    "CPF/CNPJ": "cpf_cnpj",
    "ESTABELECIMENTO": "estabelecimento",
    "UF": "uf",
    "MUNICÍPIO": "municipio",
    "CNAE": "cnae",
    "DATA DA INCLUSÃO": "data_inclusao",
    "TRABALHADORES ENVOLVIDOS": "trabalhadores_resgatados",
}

COLUNAS_SAIDA = [
    "empregador",
    "cpf_cnpj",
    "estabelecimento",
    "uf",
    "municipio",
    "cnae",
    "data_inclusao",
    "trabalhadores_resgatados",
]
