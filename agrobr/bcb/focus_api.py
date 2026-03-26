from __future__ import annotations

import time
from typing import Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta, finalize_result

from . import focus_client

logger = structlog.get_logger()

PARSER_VERSION = 1

_COLUMN_MAP: dict[str, str] = {
    "Indicador": "indicador",
    "Data": "data",
    "DataReferencia": "data_referencia",
    "Media": "media",
    "Mediana": "mediana",
    "DesvioPadrao": "desvio_padrao",
    "Minimo": "minimo",
    "Maximo": "maximo",
    "numeroRespondentes": "numero_respondentes",
    "baseCalculo": "base_calculo",
}


@overload
async def focus(
    indicador: str = "PIB Agropecuário",
    *,
    top: int = 1000,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def focus(
    indicador: str = "PIB Agropecuário",
    *,
    top: int = 1000,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def focus(
    indicador: str = "PIB Agropecuário",
    *,
    top: int = 1000,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    t0 = time.monotonic()

    records, source_url = await focus_client.fetch_focus(indicador, top=top)

    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = _parse_focus(records)
    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta(
        "bcb_focus",
        source_url,
        "httpx",
        fetch_ms,
        parse_ms,
        df,
        PARSER_VERSION,
        attempted_sources=["bcb_focus"],
        selected_source="bcb_focus",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


def _parse_focus(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=list(_COLUMN_MAP.values()))

    df = pd.DataFrame(records)
    df = df.rename(columns=_COLUMN_MAP)
    df["data"] = pd.to_datetime(df["data"])
    return df[list(_COLUMN_MAP.values())]
