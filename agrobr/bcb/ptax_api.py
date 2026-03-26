from __future__ import annotations

import time
from typing import Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta, finalize_result

from . import ptax_client

logger = structlog.get_logger()

PARSER_VERSION = 1


@overload
async def ptax(
    *,
    data: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def ptax(
    *,
    data: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def ptax(
    *,
    data: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    t0 = time.monotonic()

    records, url = await ptax_client.fetch_ptax(
        data=data,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    fetch_ms = int((time.monotonic() - t0) * 1000)
    t1 = time.monotonic()

    df = pd.DataFrame(records)

    if not df.empty:
        df = df.rename(
            columns={
                "cotacaoCompra": "cotacao_compra",
                "cotacaoVenda": "cotacao_venda",
                "dataHoraCotacao": "data_hora",
            }
        )
        df["data_hora"] = pd.to_datetime(df["data_hora"])
        df["data"] = df["data_hora"].dt.date

    parse_ms = int((time.monotonic() - t1) * 1000)

    logger.info("bcb_ptax_parsed", records=len(df))

    meta = build_source_meta(
        "bcb_ptax",
        url,
        "httpx",
        fetch_ms,
        parse_ms,
        df,
        PARSER_VERSION,
        attempted_sources=["bcb_ptax"],
        selected_source="bcb_ptax",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)
