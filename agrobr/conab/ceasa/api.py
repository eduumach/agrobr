from __future__ import annotations

import asyncio
import time
from typing import Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta, finalize_result
from agrobr.utils.warnings import warn_once

from . import client, parser
from .models import CATEGORIAS, CEASA_UF_MAP, PRODUTOS_PROHORT

logger = structlog.get_logger()


@overload
async def precos(
    *,
    produto: str | None = None,
    ceasa: str | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def precos(
    *,
    produto: str | None = None,
    ceasa: str | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def precos(
    *,
    produto: str | None = None,
    ceasa: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once(
        "conab_ceasa",
        "agrobr.conab.ceasa: dados CONAB/PROHORT via Pentaho CDA. "
        "Credenciais publicas embutidas no frontend, mas API nao e "
        "oficialmente documentada. Classificacao: zona_cinza. "
        "Veja docs/licenses.md.",
    )

    logger.info("conab_ceasa_precos", produto=produto, ceasa=ceasa)

    t0 = time.monotonic()
    (precos_json, source_url), (ceasas_json, _) = await asyncio.gather(
        client.fetch_precos(),
        client.fetch_ceasas(),
    )
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_precos(precos_json, ceasas_json)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if produto is not None:
        produto_upper = produto.strip().upper()
        df = df[df["produto"].str.upper() == produto_upper].reset_index(drop=True)

    if ceasa is not None:
        ceasa_upper = ceasa.strip().upper()
        df = df[df["ceasa"].str.upper().str.contains(ceasa_upper, regex=False)].reset_index(
            drop=True
        )

    meta = build_source_meta(
        "conab_ceasa",
        source_url,
        "httpx+json",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["conab_prohort"],
        selected_source="conab_prohort",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


def produtos() -> list[str]:
    return sorted(PRODUTOS_PROHORT)


def lista_ceasas() -> list[dict[str, str]]:
    result = []
    for nome, uf in sorted(CEASA_UF_MAP.items()):
        result.append({"nome": nome, "uf": uf})
    return result


def categorias() -> dict[str, list[str]]:
    return {k: list(v) for k, v in CATEGORIAS.items()}
