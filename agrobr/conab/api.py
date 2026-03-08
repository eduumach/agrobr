from __future__ import annotations

import time
from typing import Any, Literal, overload

import pandas as pd
import structlog

from agrobr import constants
from agrobr.cache.keys import build_cache_key
from agrobr.cache.policies import calculate_expiry
from agrobr.conab import client
from agrobr.conab.parsers.v1 import ConabParserV1
from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta, finalize_result

logger = structlog.get_logger()


@overload
async def safras(
    produto: str,
    safra: str | None = None,
    uf: str | None = None,
    levantamento: int | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def safras(
    produto: str,
    safra: str | None = None,
    uf: str | None = None,
    levantamento: int | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def safras(
    produto: str,
    safra: str | None = None,
    uf: str | None = None,
    levantamento: int | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    logger.info(
        "conab_safras_request",
        produto=produto,
        safra=safra,
        uf=uf,
        levantamento=levantamento,
    )

    t0 = time.monotonic()
    xlsx, metadata = await client.fetch_safra_xlsx(safra=safra, levantamento=levantamento)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    source_url = metadata.get("url", "https://www.conab.gov.br/info-agro/safras/graos")

    parser = ConabParserV1()
    safra_list = parser.parse_safra_produto(
        xlsx=xlsx,
        produto=produto,
        safra_ref=safra or metadata["safra"],
        levantamento=metadata.get("levantamento"),
    )

    safra_list = [s for s in safra_list if s.uf is not None]

    if uf:
        safra_list = [s for s in safra_list if s.uf == uf.upper()]

    if not safra_list:
        logger.warning(
            "conab_safras_empty",
            produto=produto,
            safra=safra,
            uf=uf,
        )
        df = pd.DataFrame()
    else:
        df = pd.DataFrame([s.model_dump() for s in safra_list])

        for col in ("area_plantada", "produtividade", "producao"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "area_colhida" not in df.columns:
            df["area_colhida"] = df.get("area_plantada")

        contract_cols = [
            "fonte",
            "produto",
            "safra",
            "uf",
            "area_plantada",
            "area_colhida",
            "produtividade",
            "producao",
            "levantamento",
            "data_publicacao",
        ]
        df = df[[c for c in contract_cols if c in df.columns]]

        logger.info(
            "conab_safras_success",
            produto=produto,
            records=len(df),
        )

    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta("conab", source_url, "httpx", fetch_ms, parse_ms, df, parser.version)
    meta.cache_key = build_cache_key(
        "conab:safras",
        {"produto": produto, "safra": safra or "latest"},
        schema_version=meta.schema_version,
    )
    meta.cache_expires_at = calculate_expiry(constants.Fonte.CONAB)

    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def balanco(
    produto: str | None = None,
    safra: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = ...,
) -> pd.DataFrame: ...


@overload
async def balanco(
    produto: str | None = None,
    safra: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def balanco(
    produto: str | None = None,
    safra: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    logger.info(
        "conab_balanco_request",
        produto=produto,
        safra=safra,
    )

    t0 = time.monotonic()
    xlsx, metadata = await client.fetch_safra_xlsx(safra=safra)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    parser = ConabParserV1()
    suprimentos = parser.parse_suprimento(xlsx=xlsx, produto=produto)

    if not suprimentos:
        logger.warning(
            "conab_balanco_empty",
            produto=produto,
        )
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(suprimentos)

        if "suprimento_total" in df.columns:
            df = df.rename(columns={"suprimento_total": "suprimento"})

        for col in (
            "estoque_inicial",
            "producao",
            "importacao",
            "suprimento",
            "consumo",
            "exportacao",
            "estoque_final",
        ):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        logger.info(
            "conab_balanco_success",
            produto=produto,
            records=len(df),
        )

    parse_ms = int((time.monotonic() - t1) * 1000)
    source_url = metadata.get("url", "https://www.conab.gov.br/info-agro/safras/graos")

    meta = build_source_meta("conab", source_url, "httpx", fetch_ms, parse_ms, df, parser.version)
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def brasil_total(
    safra: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[False] = ...,
) -> pd.DataFrame: ...


@overload
async def brasil_total(
    safra: str | None = None,
    as_polars: bool = False,
    *,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def brasil_total(
    safra: str | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    logger.info(
        "conab_brasil_total_request",
        safra=safra,
    )

    t0 = time.monotonic()
    xlsx, metadata = await client.fetch_safra_xlsx(safra=safra)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    parser = ConabParserV1()
    totais = parser.parse_brasil_total(xlsx=xlsx, safra_ref=safra)

    if not totais:
        logger.warning("conab_brasil_total_empty", safra=safra)
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(totais)
        logger.info(
            "conab_brasil_total_success",
            records=len(df),
        )

    parse_ms = int((time.monotonic() - t1) * 1000)
    source_url = metadata.get("url", "https://www.conab.gov.br/info-agro/safras/graos")

    meta = build_source_meta("conab", source_url, "httpx", fetch_ms, parse_ms, df, parser.version)
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


async def levantamentos() -> list[dict[str, Any]]:
    return await client.list_levantamentos()


async def produtos() -> list[str]:
    return list(constants.CONAB_PRODUTOS.keys())


async def ufs() -> list[str]:
    return constants.CONAB_UFS.copy()
