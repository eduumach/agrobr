from __future__ import annotations

import time
from datetime import datetime
from typing import Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta

from . import client
from .models import resolve_ncm
from .parser import PARSER_VERSION, agregar_mensal, parse_exportacao

logger = structlog.get_logger()


@overload
async def exportacao(
    produto: str,
    ano: int | None = None,
    uf: str | None = None,
    agregacao: str = "mensal",
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def exportacao(
    produto: str,
    ano: int | None = None,
    uf: str | None = None,
    agregacao: str = "mensal",
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def exportacao(
    produto: str,
    ano: int | None = None,
    uf: str | None = None,
    agregacao: str = "mensal",
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    if ano is None:
        ano = datetime.now().year

    ncm = resolve_ncm(produto)

    t0 = time.monotonic()

    logger.info(
        "comexstat_exportacao_request",
        produto=produto,
        ncm=ncm,
        ano=ano,
        uf=uf,
    )

    csv_text = await client.fetch_exportacao_csv(ano)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parse_exportacao(csv_text, ncm=ncm, uf=uf)

    if agregacao == "mensal":
        df = agregar_mensal(df)

    parse_ms = int((time.monotonic() - t1) * 1000)

    logger.info(
        "comexstat_exportacao_ok",
        produto=produto,
        ncm=ncm,
        ano=ano,
        records=len(df),
    )

    if return_meta:
        meta = build_source_meta(
            "comexstat",
            f"{client.BULK_CSV_BASE}/EXP_{ano}.csv",
            "httpx",
            fetch_ms,
            parse_ms,
            df,
            PARSER_VERSION,
        )
        return df, meta

    return df
