"""Modulo IBGE - Dados PAM, LSPA, PPM, Abate, Censo Agropecuario e Censo Legado."""

from __future__ import annotations

from agrobr.ibge.api import (
    abate,
    censo_agro,
    especies_abate,
    especies_ppm,
    lspa,
    pam,
    ppm,
    produtos_lspa,
    produtos_pam,
    temas_censo_agro,
    ufs,
)
from agrobr.ibge.legacy_api import censo_agro_legado, temas_censo_agro_legado

__all__ = [
    "abate",
    "censo_agro",
    "censo_agro_legado",
    "especies_abate",
    "especies_ppm",
    "lspa",
    "pam",
    "ppm",
    "produtos_lspa",
    "produtos_pam",
    "temas_censo_agro",
    "temas_censo_agro_legado",
    "ufs",
]
