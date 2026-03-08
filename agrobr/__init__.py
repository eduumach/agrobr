"""agrobr - Dados agricolas brasileiros em uma linha de codigo."""

from __future__ import annotations

__version__ = "0.12.0"
__author__ = "Bruno"

from agrobr import (
    abiove,
    alt,
    anda,
    antaq,
    b3,
    bcb,
    cepea,
    comexstat,
    comtrade,
    conab,
    contracts,
    datasets,
    deral,
    desmatamento,
    ibge,
    imea,
    inmet,
    mapbiomas,
    nasa_power,
    noticias_agricolas,
    queimadas,
    usda,
    zarc,
)
from agrobr.datasets.deterministic import deterministic
from agrobr.models import MetaInfo

__all__ = [
    "abiove",
    "alt",
    "anda",
    "antaq",
    "b3",
    "bcb",
    "cepea",
    "comexstat",
    "comtrade",
    "conab",
    "contracts",
    "datasets",
    "deral",
    "desmatamento",
    "deterministic",
    "ibge",
    "imea",
    "inmet",
    "mapbiomas",
    "nasa_power",
    "noticias_agricolas",
    "queimadas",
    "usda",
    "zarc",
    "MetaInfo",
    "__version__",
]
