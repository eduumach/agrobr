from __future__ import annotations

import re
import time
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

_UF_RE = re.compile(r"^[A-Z]{2}$")


def _validate_uf(uf: str | None) -> str | None:
    if uf is None:
        return None
    uf_upper = uf.strip().upper()
    if not _UF_RE.match(uf_upper):
        raise ValueError(f"UF invalida: {uf!r}")
    return uf_upper


@overload
async def quilombolas(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def quilombolas(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def quilombolas(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    uf = _validate_uf(uf)
    bbox = validate_bbox(bbox)
    logger.info("incra_quilombolas", uf=uf, fase=fase, bbox=bbox)

    t0 = time.monotonic()
    csv_bytes, source_url = await client.fetch_quilombolas(uf=uf, fase=fase, bbox=bbox)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_quilombolas_csv(csv_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta(
        "incra",
        source_url,
        "httpx+wfs+csv",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["incra_wfs"],
        selected_source="incra_wfs",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def quilombolas_geo(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def quilombolas_geo(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def quilombolas_geo(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    uf = _validate_uf(uf)
    bbox = validate_bbox(bbox)
    logger.info("incra_quilombolas_geo", uf=uf, fase=fase, bbox=bbox)

    t0 = time.monotonic()
    geojson_bytes, source_url = await client.fetch_quilombolas_geo(uf=uf, fase=fase, bbox=bbox)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_quilombolas_geojson(geojson_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        meta = build_source_meta(
            "incra",
            source_url,
            "httpx+wfs+geojson",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["incra_wfs_geo"],
            selected_source="incra_wfs_geo",
        )
        return gdf, meta

    return gdf
