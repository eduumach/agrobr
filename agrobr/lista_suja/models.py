from agrobr.constants import URLS, Fonte

DOWNLOAD_URL: str = URLS[Fonte.LISTA_SUJA]["download"]

RENAME_MAP: dict[str, str] = {
    "Empregador": "empregador",
    "CNPJ/CPF": "cpf_cnpj",
    "Estabelecimento": "estabelecimento",
    "UF": "uf",
    "CNAE": "cnae",
    "Trabalhadores\nenvolvidos": "trabalhadores_resgatados",
    "Inclusão no\nCadastro de\nEmpregadores": "data_inclusao",
    "Ano da\nação\nfiscal": "ano_acao_fiscal",
}

COLUNAS_SAIDA = [
    "empregador",
    "cpf_cnpj",
    "estabelecimento",
    "uf",
    "cnae",
    "data_inclusao",
    "trabalhadores_resgatados",
    "ano_acao_fiscal",
]

PDF_HEADER_ROW_MARKER = "ID"
