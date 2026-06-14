from __future__ import annotations

from agrobr.constants import URLS, Fonte
from agrobr.normalize.regions import UFS_VALIDAS as UFS_VALIDAS

SHLP_BASE = URLS[Fonte.ANP_DIESEL]["shlp"]
VENDAS_DIESEL_CSV_URL = URLS[Fonte.ANP_DIESEL]["vendas_diesel_csv"]

PRECOS_MUNICIPIOS_URLS: dict[str, str] = {
    "2022-2023": f"{SHLP_BASE}/semanal/semanal-municipios-2022_a_2023.xlsx",
    "2024-2025": f"{SHLP_BASE}/semanal/semanal-municipio-2024-2025.xlsx",
    "2026": f"{SHLP_BASE}/semanal/semanal-municipios-2026.xlsx",
}

PRECOS_ESTADOS_URL = f"{SHLP_BASE}/semanal/semanal-estados-desde-2013.xlsx"

PRECOS_BRASIL_URL = f"{SHLP_BASE}/semanal/semanal-brasil-desde-2013.xlsx"

PRODUTOS_DIESEL = frozenset(
    {
        "DIESEL",
        "DIESEL S10",
        "OLEO DIESEL",
        "OLEO DIESEL S10",
    }
)

NIVEL_MUNICIPIO = "municipio"
NIVEL_UF = "uf"
NIVEL_BRASIL = "brasil"
NIVEIS_VALIDOS = frozenset({NIVEL_MUNICIPIO, NIVEL_UF, NIVEL_BRASIL})

AGREGACAO_SEMANAL = "semanal"
AGREGACAO_MENSAL = "mensal"
AGREGACOES_VALIDAS = frozenset({AGREGACAO_SEMANAL, AGREGACAO_MENSAL})


def _resolve_periodo_municipio(ano: int) -> str | None:
    for periodo, _url in PRECOS_MUNICIPIOS_URLS.items():
        partes = periodo.split("-")
        if len(partes) == 2:
            inicio, fim = int(partes[0]), int(partes[1])
            if inicio <= ano <= fim:
                return periodo
        elif len(partes) == 1:
            if ano == int(partes[0]):
                return periodo
    return None
