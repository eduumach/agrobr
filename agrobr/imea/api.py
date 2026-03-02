from __future__ import annotations

import time
from typing import Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta
from agrobr.utils.warnings import warn_once

from . import client, parser
from .models import resolve_cadeia_id

logger = structlog.get_logger()


@overload
async def cotacoes(
    cadeia: str = "soja",
    *,
    safra: str | None = None,
    unidade: str | None = None,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def cotacoes(
    cadeia: str = "soja",
    *,
    safra: str | None = None,
    unidade: str | None = None,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def cotacoes(
    cadeia: str = "soja",
    *,
    safra: str | None = None,
    unidade: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once(
        "imea",
        "IMEA: termos de uso proíbem redistribuição de dados sem "
        "autorização escrita. Uso pessoal/educacional apenas. "
        "Ref: https://imea.com.br/imea-site/termo-de-uso.html",
    )

    cadeia_id = resolve_cadeia_id(cadeia)

    logger.info(
        "imea_cotacoes",
        cadeia=cadeia,
        cadeia_id=cadeia_id,
        safra=safra,
        unidade=unidade,
    )

    t0 = time.monotonic()
    records = await client.fetch_cotacoes(cadeia_id)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_cotacoes(records)

    if safra:
        df = parser.filter_by_safra(df, safra)

    if unidade:
        df = parser.filter_by_unidade(df, unidade)

    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        meta = build_source_meta(
            "imea",
            f"{client.BASE_URL}/v2/mobile/cadeias/{cadeia_id}/cotacoes",
            "httpx",
            fetch_ms,
            parse_ms,
            df,
            parser.PARSER_VERSION,
        )
        return df, meta

    return df
