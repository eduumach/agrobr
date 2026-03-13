"""agrobr - Dados agricolas brasileiros em uma linha de codigo."""

from __future__ import annotations

__version__ = "1.0.0"
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
    defensivos,
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
from agrobr.config import configure
from agrobr.datasets.deterministic import deterministic
from agrobr.exceptions import (
    AgrobrError,
    ContractViolationError,
    ParseError,
    SourceUnavailableError,
)
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
    "configure",
    "contracts",
    "datasets",
    "defensivos",
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
    "AgrobrError",
    "ContractViolationError",
    "ParseError",
    "SourceUnavailableError",
    "MetaInfo",
    "__version__",
]
