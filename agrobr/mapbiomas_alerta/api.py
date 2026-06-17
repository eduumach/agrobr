from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.geo import validate_bbox
from agrobr.utils.result import build_source_meta, finalize_result

from . import client, parser

if TYPE_CHECKING:
    import geopandas as gpd

logger = structlog.get_logger()


def _prepare_bbox(
    bbox: tuple[float, float, float, float] | None,
) -> list[float] | None:
    if not bbox:
        return None
    xmin, ymin, xmax, ymax = bbox
    return [ymin, xmin, ymax, xmax]


@overload
async def alertas(
    *,
    token: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def alertas(
    *,
    token: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def alertas(
    *,
    token: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    bbox = validate_bbox(bbox)
    resolved_token = client._get_token(token)
    bounding_box = _prepare_bbox(bbox)

    logger.info("mapbiomas_alertas", bbox=bbox, sources=sources)

    t0 = time.monotonic()
    records, source_url = await client.fetch_alertas(
        token=resolved_token,
        start_date=start_date,
        end_date=end_date,
        sources=sources,
        bounding_box=bounding_box,
        limit=limit,
    )
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_alertas(records)
    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta(
        "mapbiomas_alerta",
        source_url,
        "httpx+graphql",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["mapbiomas_alerta_graphql"],
        selected_source="mapbiomas_alerta_graphql",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def alertas_geo(
    *,
    token: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def alertas_geo(
    *,
    token: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def alertas_geo(
    *,
    token: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    bbox = validate_bbox(bbox)
    resolved_token = client._get_token(token)
    bounding_box = _prepare_bbox(bbox)

    logger.info("mapbiomas_alertas_geo", bbox=bbox, sources=sources)

    t0 = time.monotonic()
    records, source_url = await client.fetch_alertas(
        token=resolved_token,
        start_date=start_date,
        end_date=end_date,
        sources=sources,
        bounding_box=bounding_box,
        limit=limit,
    )
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_alertas_geo(records)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        meta = build_source_meta(
            "mapbiomas_alerta",
            source_url,
            "httpx+graphql+wkt",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["mapbiomas_alerta_graphql_geo"],
            selected_source="mapbiomas_alerta_graphql_geo",
        )
        return gdf, meta

    return gdf


async def alertas_geo_stream(
    *,
    token: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    max_pages: int = 50,
) -> AsyncGenerator[gpd.GeoDataFrame, None]:
    """Itera sobre os alertas geoespaciais do MapBiomas em batches de baixo consumo de memoria.

    Cada yield e um GeoDataFrame parcial com ate ``limit`` alertas (uma pagina
    GraphQL). Evita acumular todas as geometrias WKT em memoria antes de processar.
    Async-only: sem suporte em agrobr.sync.
    """
    bbox = validate_bbox(bbox)
    resolved_token = client._get_token(token)
    bounding_box = _prepare_bbox(bbox)

    logger.info("mapbiomas_alertas_geo_stream", bbox=bbox, sources=sources)

    seen: set[str] = set()
    async for collection, _url in client.stream_alertas(
        token=resolved_token,
        start_date=start_date,
        end_date=end_date,
        sources=sources,
        bounding_box=bounding_box,
        limit=limit,
        max_pages=max_pages,
    ):
        gdf = parser.parse_alertas_geo(collection)
        if gdf.empty:
            continue
        if "alert_code" in gdf.columns:
            gdf = gdf[~gdf["alert_code"].isin(seen)]
            seen.update(gdf["alert_code"].tolist())
        if not gdf.empty:
            yield gdf


async def alerta_info() -> dict[str, Any]:
    (date_range, _), (publication, _) = await asyncio.gather(
        client.fetch_alert_date_range(),
        client.fetch_last_publication(),
    )
    return {"date_range": date_range, "last_publication": publication}
