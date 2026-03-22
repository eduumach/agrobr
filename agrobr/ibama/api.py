from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.geo import validate_bbox
from agrobr.utils.result import build_source_meta, finalize_result
from agrobr.utils.validation import validate_uf

from . import client, parser

if TYPE_CHECKING:
    import geopandas as gpd

logger = structlog.get_logger()


@overload
async def embargos(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def embargos(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def embargos(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    uf = validate_uf(uf)
    bbox = validate_bbox(bbox)
    logger.info("ibama_embargos", uf=uf, bbox=bbox)

    t0 = time.monotonic()
    pages, source_url = await client.fetch_embargos(uf=uf, bbox=bbox)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_embargos_csv(pages)
    parse_ms = int((time.monotonic() - t1) * 1000)

    df = df.drop_duplicates(subset=["numero_tad"]).reset_index(drop=True)

    meta = build_source_meta(
        "ibama",
        source_url,
        "httpx+wfs+csv",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["ibama_geoserver"],
        selected_source="ibama_geoserver",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def embargos_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def embargos_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def embargos_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    uf = validate_uf(uf)
    bbox = validate_bbox(bbox)
    logger.info("ibama_embargos_geo", uf=uf, bbox=bbox)

    t0 = time.monotonic()
    geojson_bytes, source_url = await client.fetch_embargos_geo(bbox=bbox)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_embargos_geojson(geojson_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if uf is not None and not gdf.empty:
        gdf = gdf[gdf["uf"] == uf].reset_index(drop=True)

    if return_meta:
        meta = build_source_meta(
            "ibama",
            source_url,
            "httpx+wfs+geojson",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["ibama_geoserver_geo"],
            selected_source="ibama_geoserver_geo",
        )
        return gdf, meta

    return gdf
