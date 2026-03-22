from __future__ import annotations

import time
from typing import Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta, finalize_result
from agrobr.utils.validation import validate_uf
from agrobr.utils.warnings import warn_once

from . import client, parser

logger = structlog.get_logger()


@overload
async def empregadores(
    *,
    uf: str | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def empregadores(
    *,
    uf: str | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def empregadores(
    *,
    uf: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once(
        "lista_suja_pii",
        "Lista Suja contem CPF/CNPJ — dados publicos por Lei de Acesso a Informacao.",
    )
    uf = validate_uf(uf)
    logger.info("lista_suja_empregadores", uf=uf)

    t0 = time.monotonic()
    data, source_url = await client.fetch_empregadores()
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_empregadores(data)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if uf:
        df = df[df["uf"] == uf].reset_index(drop=True)

    meta = build_source_meta(
        "lista_suja",
        source_url,
        "httpx+xlsx",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["lista_suja_download"],
        selected_source="lista_suja_download",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)
