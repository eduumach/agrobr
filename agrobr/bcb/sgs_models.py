from __future__ import annotations

SGS_SERIES: dict[str, int] = {
    "selic": 432,
    "ipca": 433,
    "ipca_alimentacao": 1635,
    "ipa_agropecuario": 7460,
    "pib_agropecuaria": 22083,
    "credito_rural_concessoes_pf": 20701,
    "credito_rural_saldo_pf": 20609,
    "dolar_ptax_venda": 1,
    "dolar_ptax_compra": 10813,
    "cambio_mensal_compra": 3697,
    "cambio_mensal_venda": 3698,
    "igpm": 189,
    "igpdi": 190,
    "inpc": 188,
    "cdi": 4392,
    "tjlp": 256,
    "tr": 226,
}

COLUNAS_SAIDA: list[str] = ["data", "valor", "codigo", "nome_serie"]

PARSER_VERSION: int = 1
