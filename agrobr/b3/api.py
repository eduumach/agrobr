from __future__ import annotations

import asyncio
import time
from datetime import date, datetime, timedelta
from typing import Any, Literal, overload

import httpx
import pandas as pd
import structlog

from agrobr.exceptions import ParseError, SourceUnavailableError
from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta
from agrobr.utils.warnings import warn_once

from . import client, parser
from .models import (
    B3_CONTRATOS_AGRO,
    COLUNAS_OI_SAIDA,
    COLUNAS_SAIDA,
    TICKERS_AGRO,
    TICKERS_AGRO_OI,
)

logger = structlog.get_logger()


@overload
async def ajustes(
    *,
    data: str | date,
    contrato: str | None = None,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def ajustes(
    *,
    data: str | date,
    contrato: str | None = None,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def ajustes(
    *,
    data: str | date,
    contrato: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once(
        "b3_ajustes",
        "agrobr.b3: dados da B3 (empresa privada). Ajustes diarios publicados "
        "sem autenticacao, mas termos de uso para acesso programatico nao sao "
        "claros. Classificacao: zona_cinza. Veja docs/licenses.md.",
    )

    logger.info("b3_ajustes", data=str(data), contrato=contrato)

    data_str = data.strftime("%d/%m/%Y") if isinstance(data, date) else data

    t0 = time.monotonic()
    html, source_url = await client.fetch_ajustes(data_str)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_ajustes_html(html)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if contrato is not None:
        ticker = B3_CONTRATOS_AGRO.get(contrato, contrato.upper())
        if ticker in TICKERS_AGRO:
            df = df[df["ticker"] == ticker].reset_index(drop=True)
        else:
            df = df[df["ticker"] == contrato.upper()].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "b3",
            source_url,
            "httpx+html",
            fetch_ms,
            parse_ms,
            df,
            parser.PARSER_VERSION,
        )
        return df, meta

    return df


@overload
async def historico(
    *,
    contrato: str,
    inicio: str | date,
    fim: str | date,
    vencimento: str | None = None,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def historico(
    *,
    contrato: str,
    inicio: str | date,
    fim: str | date,
    vencimento: str | None = None,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def historico(
    *,
    contrato: str,
    inicio: str | date,
    fim: str | date,
    vencimento: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    logger.info("b3_historico", contrato=contrato, inicio=str(inicio), fim=str(fim))

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date() if isinstance(inicio, str) else inicio
    fim_dt = datetime.strptime(fim, "%Y-%m-%d").date() if isinstance(fim, str) else fim

    t0 = time.monotonic()
    frames: list[pd.DataFrame] = []
    current = inicio_dt

    while current <= fim_dt:
        if current.weekday() < 5:
            try:
                df_dia = await ajustes(data=current, contrato=contrato)
                if not df_dia.empty:
                    frames.append(df_dia)
                else:
                    logger.debug("b3_historico_empty", data=str(current), contrato=contrato)
            except (httpx.HTTPError, SourceUnavailableError, ParseError) as exc:
                logger.warning(
                    "b3_historico_skip",
                    data=str(current),
                    contrato=contrato,
                    error=str(exc)[:200],
                )
            await asyncio.sleep(1.0)
        current += timedelta(days=1)

    fetch_ms = int((time.monotonic() - t0) * 1000)

    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLUNAS_SAIDA)

    if vencimento is not None:
        vct_upper = vencimento.strip().upper()
        df = df[df["vencimento_codigo"] == vct_upper].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "b3",
            client.BASE_URL,
            "httpx+html",
            fetch_ms,
            0,
            df,
            parser.PARSER_VERSION,
        )
        return df, meta

    return df


def contratos() -> list[str]:
    return sorted(B3_CONTRATOS_AGRO.keys())


@overload
async def posicoes_abertas(
    *,
    data: str | date,
    contrato: str | None = None,
    tipo: Literal["futuro", "opcao"] | None = None,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def posicoes_abertas(
    *,
    data: str | date,
    contrato: str | None = None,
    tipo: Literal["futuro", "opcao"] | None = None,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def posicoes_abertas(
    *,
    data: str | date,
    contrato: str | None = None,
    tipo: Literal["futuro", "opcao"] | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once(
        "b3_posicoes",
        "agrobr.b3: dados da B3 (empresa privada). Posicoes em aberto publicadas "
        "sem autenticacao, mas termos de uso para acesso programatico nao sao "
        "claros. Classificacao: zona_cinza. Veja docs/licenses.md.",
    )

    logger.info("b3_posicoes_abertas", data=str(data), contrato=contrato, tipo=tipo)

    data_str = data.strftime("%Y-%m-%d") if isinstance(data, date) else data

    t0 = time.monotonic()
    csv_bytes, source_url = await client.fetch_posicoes_abertas(data_str)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_posicoes_abertas(csv_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if contrato is not None:
        ticker = B3_CONTRATOS_AGRO.get(contrato, contrato.upper())
        if ticker in TICKERS_AGRO_OI:
            df = df[df["ticker"] == ticker].reset_index(drop=True)
        else:
            df = df[df["ticker"] == contrato.upper()].reset_index(drop=True)

    if tipo is not None:
        df = df[df["tipo"] == tipo].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "b3",
            source_url,
            "httpx+csv",
            fetch_ms,
            parse_ms,
            df,
            parser.PARSER_VERSION_OI,
        )
        return df, meta

    return df


@overload
async def oi_historico(
    *,
    contrato: str,
    inicio: str | date,
    fim: str | date,
    vencimento: str | None = None,
    tipo: Literal["futuro", "opcao"] | None = None,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def oi_historico(
    *,
    contrato: str,
    inicio: str | date,
    fim: str | date,
    vencimento: str | None = None,
    tipo: Literal["futuro", "opcao"] | None = None,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def oi_historico(
    *,
    contrato: str,
    inicio: str | date,
    fim: str | date,
    vencimento: str | None = None,
    tipo: Literal["futuro", "opcao"] | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    logger.info("b3_oi_historico", contrato=contrato, inicio=str(inicio), fim=str(fim))

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date() if isinstance(inicio, str) else inicio
    fim_dt = datetime.strptime(fim, "%Y-%m-%d").date() if isinstance(fim, str) else fim

    t0 = time.monotonic()
    frames: list[pd.DataFrame] = []
    current = inicio_dt

    while current <= fim_dt:
        if current.weekday() < 5:
            try:
                df_dia = await posicoes_abertas(data=current, contrato=contrato, tipo=tipo)
                if not df_dia.empty:
                    frames.append(df_dia)
                else:
                    logger.debug("b3_oi_historico_empty", data=str(current), contrato=contrato)
            except (httpx.HTTPError, SourceUnavailableError, ParseError) as exc:
                logger.warning(
                    "b3_oi_historico_skip",
                    data=str(current),
                    contrato=contrato,
                    error=str(exc)[:200],
                )
            await asyncio.sleep(1.0)
        current += timedelta(days=1)

    fetch_ms = int((time.monotonic() - t0) * 1000)

    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLUNAS_OI_SAIDA)

    if vencimento is not None:
        vct_upper = vencimento.strip().upper()
        df = df[df["vencimento_codigo"] == vct_upper].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "b3",
            client.BASE_URL_ARQUIVOS,
            "httpx+csv",
            fetch_ms,
            0,
            df,
            parser.PARSER_VERSION_OI,
        )
        return df, meta

    return df
