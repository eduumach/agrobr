from __future__ import annotations

from agrobr.constants import URLS, Fonte

SIDRA_BASE = URLS[Fonte.IBGE]["base"]

NIVEL_MAP: dict[str, str] = {
    "brasil": "1",
    "uf": "3",
    "municipio": "6",
}

NIVEL_MAP_HISTORICO: dict[str, str] = {
    "brasil": "1",
    "regiao": "2",
    "uf": "3",
}
