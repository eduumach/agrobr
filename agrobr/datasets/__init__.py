"""Camada semântica de datasets do agrobr."""

from agrobr.datasets.abate_trimestral import abate_trimestral
from agrobr.datasets.balanco import balanco
from agrobr.datasets.cadastro_rural import cadastro_rural
from agrobr.datasets.censo_agropecuario import censo_agropecuario
from agrobr.datasets.censo_agropecuario_historico import censo_agropecuario_historico
from agrobr.datasets.censo_agropecuario_legado import censo_agropecuario_legado
from agrobr.datasets.censo_agropecuario_municipal_1985 import censo_agropecuario_municipal_1985
from agrobr.datasets.credito_rural import credito_rural
from agrobr.datasets.custo_producao import custo_producao
from agrobr.datasets.deterministic import deterministic, get_snapshot, is_deterministic
from agrobr.datasets.estimativa_safra import estimativa_safra
from agrobr.datasets.exportacao import exportacao
from agrobr.datasets.extrativismo_vegetal import extrativismo_vegetal
from agrobr.datasets.fertilizante import fertilizante
from agrobr.datasets.importacao import importacao
from agrobr.datasets.leite_industrial import leite_industrial
from agrobr.datasets.pecuaria_municipal import pecuaria_municipal
from agrobr.datasets.pib_agro import pib_agro
from agrobr.datasets.preco_diario import preco_diario
from agrobr.datasets.producao_anual import producao_anual
from agrobr.datasets.progresso_safra import progresso_safra
from agrobr.datasets.registry import (
    describe,
    describe_all,
    get_dataset,
    info,
    list_datasets,
    list_products,
)
from agrobr.datasets.silvicultura import silvicultura as silvicultura_dataset

__all__ = [
    "abate_trimestral",
    "balanco",
    "cadastro_rural",
    "censo_agropecuario",
    "censo_agropecuario_historico",
    "censo_agropecuario_legado",
    "censo_agropecuario_municipal_1985",
    "credito_rural",
    "custo_producao",
    "describe",
    "describe_all",
    "deterministic",
    "estimativa_safra",
    "exportacao",
    "extrativismo_vegetal",
    "fertilizante",
    "get_dataset",
    "get_snapshot",
    "importacao",
    "info",
    "is_deterministic",
    "leite_industrial",
    "list_datasets",
    "list_products",
    "pecuaria_municipal",
    "pib_agro",
    "preco_diario",
    "producao_anual",
    "progresso_safra",
    "silvicultura_dataset",
]
