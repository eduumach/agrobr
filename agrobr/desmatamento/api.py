from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.result import build_source_meta

from . import client, parser

if TYPE_CHECKING:
    import geopandas as gpd

logger = structlog.get_logger()


@overload
async def prodes(
    *,
    bioma: str = "Cerrado",
    ano: int | None = None,
    uf: str | None = None,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def prodes(
    *,
    bioma: str = "Cerrado",
    ano: int | None = None,
    uf: str | None = None,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def prodes(
    *,
    bioma: str = "Cerrado",
    ano: int | None = None,
    uf: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    logger.info("desmatamento_prodes", bioma=bioma, ano=ano, uf=uf)

    t0 = time.monotonic()
    csv_bytes, source_url = await client.fetch_prodes(bioma, ano=ano, uf=uf)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_prodes_csv(csv_bytes, bioma)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if uf is not None:
        uf_upper = uf.strip().upper()
        df = df[df["uf"] == uf_upper].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "desmatamento",
            source_url,
            "httpx+wfs+csv",
            fetch_ms,
            parse_ms,
            df,
            parser.PARSER_VERSION,
            attempted_sources=["terrabrasilis_prodes"],
            selected_source="terrabrasilis_prodes",
        )
        return df, meta

    return df


@overload
async def prodes_geo(
    *,
    bioma: str = "Cerrado",
    ano: int | None = None,
    uf: str | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def prodes_geo(
    *,
    bioma: str = "Cerrado",
    ano: int | None = None,
    uf: str | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def prodes_geo(
    *,
    bioma: str = "Cerrado",
    ano: int | None = None,
    uf: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    logger.info("desmatamento_prodes_geo", bioma=bioma, ano=ano, uf=uf)

    t0 = time.monotonic()
    geojson_bytes, source_url = await client.fetch_prodes_geo(bioma, ano=ano, uf=uf)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_prodes_geojson(geojson_bytes, bioma)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if uf is not None:
        uf_upper = uf.strip().upper()
        gdf = gdf[gdf["uf"] == uf_upper].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "desmatamento",
            source_url,
            "httpx+wfs+geojson",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["terrabrasilis_prodes_geo"],
            selected_source="terrabrasilis_prodes_geo",
        )
        return gdf, meta

    return gdf


@overload
async def deter(
    *,
    bioma: str = "Amazônia",
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    classe: str | None = None,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def deter(
    *,
    bioma: str = "Amazônia",
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    classe: str | None = None,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def deter(
    *,
    bioma: str = "Amazônia",
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    classe: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    logger.info(
        "desmatamento_deter",
        bioma=bioma,
        uf=uf,
        data_inicio=data_inicio,
        data_fim=data_fim,
        classe=classe,
    )

    t0 = time.monotonic()
    csv_bytes, source_url = await client.fetch_deter(
        bioma, uf=uf, data_inicio=data_inicio, data_fim=data_fim
    )
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_deter_csv(csv_bytes, bioma)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if classe is not None:
        df = df[df["classe"] == classe].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "desmatamento",
            source_url,
            "httpx+wfs+csv",
            fetch_ms,
            parse_ms,
            df,
            parser.PARSER_VERSION,
            attempted_sources=["terrabrasilis_deter"],
            selected_source="terrabrasilis_deter",
        )
        return df, meta

    return df


@overload
async def deter_geo(
    *,
    bioma: str = "Amazônia",
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    classe: str | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def deter_geo(
    *,
    bioma: str = "Amazônia",
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    classe: str | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def deter_geo(
    *,
    bioma: str = "Amazônia",
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    classe: str | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    logger.info(
        "desmatamento_deter_geo",
        bioma=bioma,
        uf=uf,
        data_inicio=data_inicio,
        data_fim=data_fim,
        classe=classe,
    )

    t0 = time.monotonic()
    geojson_bytes, source_url = await client.fetch_deter_geo(
        bioma, uf=uf, data_inicio=data_inicio, data_fim=data_fim
    )
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_deter_geojson(geojson_bytes, bioma)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if classe is not None:
        gdf = gdf[gdf["classe"] == classe].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "desmatamento",
            source_url,
            "httpx+wfs+geojson",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["terrabrasilis_deter_geo"],
            selected_source="terrabrasilis_deter_geo",
        )
        return gdf, meta

    return gdf
