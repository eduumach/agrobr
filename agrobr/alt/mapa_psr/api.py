from __future__ import annotations

import time

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta
from agrobr.utils.validation import validate_year_uf

from . import client, parser
from .models import (
    ANO_INICIO_PSR,
    COLUNAS_APOLICES,
    COLUNAS_SINISTROS,
    _resolve_periodos,
    get_csv_url,
)

logger = structlog.get_logger()


async def sinistros(
    cultura: str | None = None,
    uf: str | None = None,
    ano: int | None = None,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
    municipio: str | None = None,
    evento: str | None = None,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    validate_year_uf(uf=uf, ano=ano, ano_inicio=ano_inicio, ano_fim=ano_fim, ano_min=ANO_INICIO_PSR)

    effective_inicio, effective_fim = _resolve_range(ano, ano_inicio, ano_fim)
    periodos = _resolve_periodos(effective_inicio, effective_fim)

    t0 = time.monotonic()
    contents = await client.fetch_periodos(periodos)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    dfs: list[pd.DataFrame] = []
    for content in contents:
        df = parser.parse_sinistros(
            content,
            cultura=cultura,
            uf=uf,
            ano=ano,
            municipio=municipio,
            evento=evento,
        )
        dfs.append(df)

    if not dfs:
        df_out = pd.DataFrame(columns=COLUNAS_SINISTROS)
    else:
        df_out = pd.concat(dfs, ignore_index=True)

    if effective_inicio and "ano_apolice" in df_out.columns:
        df_out = df_out[df_out["ano_apolice"] >= effective_inicio].copy()
    if effective_fim and "ano_apolice" in df_out.columns:
        df_out = df_out[df_out["ano_apolice"] <= effective_fim].copy()

    df_out = df_out.sort_values("ano_apolice").reset_index(drop=True)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        source_url = get_csv_url(periodos[0]) if periodos else ""
        meta = build_source_meta(
            "mapa_psr",
            source_url,
            "httpx",
            fetch_ms,
            parse_ms,
            df_out,
            parser.PARSER_VERSION,
        )
        return df_out, meta

    return df_out


async def apolices(
    cultura: str | None = None,
    uf: str | None = None,
    ano: int | None = None,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
    municipio: str | None = None,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    validate_year_uf(uf=uf, ano=ano, ano_inicio=ano_inicio, ano_fim=ano_fim, ano_min=ANO_INICIO_PSR)

    effective_inicio, effective_fim = _resolve_range(ano, ano_inicio, ano_fim)
    periodos = _resolve_periodos(effective_inicio, effective_fim)

    t0 = time.monotonic()
    contents = await client.fetch_periodos(periodos)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    dfs: list[pd.DataFrame] = []
    for content in contents:
        df = parser.parse_apolices(
            content,
            cultura=cultura,
            uf=uf,
            ano=ano,
            municipio=municipio,
        )
        dfs.append(df)

    if not dfs:
        df_out = pd.DataFrame(columns=COLUNAS_APOLICES)
    else:
        df_out = pd.concat(dfs, ignore_index=True)

    if effective_inicio and "ano_apolice" in df_out.columns:
        df_out = df_out[df_out["ano_apolice"] >= effective_inicio].copy()
    if effective_fim and "ano_apolice" in df_out.columns:
        df_out = df_out[df_out["ano_apolice"] <= effective_fim].copy()

    df_out = df_out.sort_values("ano_apolice").reset_index(drop=True)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        source_url = get_csv_url(periodos[0]) if periodos else ""
        meta = build_source_meta(
            "mapa_psr",
            source_url,
            "httpx",
            fetch_ms,
            parse_ms,
            df_out,
            parser.PARSER_VERSION,
        )
        return df_out, meta

    return df_out


def _resolve_range(
    ano: int | None,
    ano_inicio: int | None,
    ano_fim: int | None,
) -> tuple[int | None, int | None]:
    if ano is not None:
        return ano, ano
    return ano_inicio, ano_fim
