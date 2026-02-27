"""Modulo IBGE - Dados PAM, LSPA, PPM, Abate, Censo Agropecuario, Censo Legado, Serie Historica e Municipal 1985."""

from __future__ import annotations

from agrobr.ibge.api import (
    abate,
    censo_agro,
    censo_agro_historico,
    especies_abate,
    especies_ppm,
    lspa,
    pam,
    ppm,
    produtos_lspa,
    produtos_pam,
    temas_censo_agro,
    temas_censo_agro_historico,
    ufs,
)
from agrobr.ibge.censo_municipal_1985 import (
    censo_agro_municipal_1985,
    temas_censo_agro_municipal_1985,
)
from agrobr.ibge.legacy_api import censo_agro_legado, temas_censo_agro_legado

__all__ = [
    "abate",
    "censo_agro",
    "censo_agro_historico",
    "censo_agro_legado",
    "censo_agro_municipal_1985",
    "especies_abate",
    "especies_ppm",
    "lspa",
    "pam",
    "ppm",
    "produtos_lspa",
    "produtos_pam",
    "temas_censo_agro",
    "temas_censo_agro_historico",
    "temas_censo_agro_legado",
    "temas_censo_agro_municipal_1985",
    "ufs",
]
