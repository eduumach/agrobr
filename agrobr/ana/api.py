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


def _build_where(*, uf: str | None = None) -> str:
    if uf:
        return f"UF='{uf}'"
    return "1=1"


async def _fetch_and_parse_tabular(
    layer_key: str,
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    where = _build_where(uf=uf)
    logger.info(f"ana_{layer_key}", uf=uf, bbox=bbox)

    t0 = time.monotonic()
    pages, source_url = await client.fetch_layer(
        layer_key,
        where=where,
        bbox=bbox,
        max_features=max_features,
        f="json",
    )
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_layer_tabular(pages, layer_key=layer_key)
    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta(
        "ana",
        source_url,
        "httpx+arcgis+json",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=[f"ana_{layer_key}"],
        selected_source=f"ana_{layer_key}",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


async def _fetch_and_parse_geo(
    layer_key: str,
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    return_meta: bool = False,
) -> Any:
    where = _build_where(uf=uf)
    logger.info(f"ana_{layer_key}_geo", uf=uf, bbox=bbox)

    t0 = time.monotonic()
    pages, source_url = await client.fetch_layer(
        layer_key,
        where=where,
        bbox=bbox,
        max_features=max_features,
        f="geojson",
    )
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_layer_geojson(pages, layer_key=layer_key)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        meta = build_source_meta(
            "ana",
            source_url,
            "httpx+arcgis+geojson",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=[f"ana_{layer_key}_geo"],
            selected_source=f"ana_{layer_key}_geo",
        )
        return gdf, meta
    return gdf


# ---------------------------------------------------------------------------
# hidrografia (bbox required)
# ---------------------------------------------------------------------------


@overload
async def hidrografia(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def hidrografia(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def hidrografia(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    bbox = validate_bbox(bbox)  # type: ignore[assignment]
    return await _fetch_and_parse_tabular(
        "hidrografia",
        bbox=bbox,
        max_features=max_features,
        as_polars=as_polars,
        return_meta=return_meta,
    )


@overload
async def hidrografia_geo(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def hidrografia_geo(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def hidrografia_geo(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    bbox = validate_bbox(bbox)  # type: ignore[assignment]
    return await _fetch_and_parse_geo(
        "hidrografia",
        bbox=bbox,
        max_features=max_features,
        return_meta=return_meta,
    )


# ---------------------------------------------------------------------------
# pivos_irrigacao (uf optional, bbox optional)
# ---------------------------------------------------------------------------


@overload
async def pivos_irrigacao(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def pivos_irrigacao(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def pivos_irrigacao(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    uf = validate_uf(uf)
    bbox = validate_bbox(bbox)
    return await _fetch_and_parse_tabular(
        "pivos_irrigacao",
        uf=uf,
        bbox=bbox,
        max_features=max_features,
        as_polars=as_polars,
        return_meta=return_meta,
    )


@overload
async def pivos_irrigacao_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def pivos_irrigacao_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def pivos_irrigacao_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    uf = validate_uf(uf)
    bbox = validate_bbox(bbox)
    return await _fetch_and_parse_geo(
        "pivos_irrigacao",
        uf=uf,
        bbox=bbox,
        max_features=max_features,
        return_meta=return_meta,
    )


# ---------------------------------------------------------------------------
# demanda_irrigacao (bbox required)
# ---------------------------------------------------------------------------


@overload
async def demanda_irrigacao(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def demanda_irrigacao(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def demanda_irrigacao(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    bbox = validate_bbox(bbox)  # type: ignore[assignment]
    return await _fetch_and_parse_tabular(
        "demanda_irrigacao",
        bbox=bbox,
        max_features=max_features,
        as_polars=as_polars,
        return_meta=return_meta,
    )


@overload
async def demanda_irrigacao_geo(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def demanda_irrigacao_geo(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def demanda_irrigacao_geo(
    *,
    bbox: tuple[float, float, float, float],
    max_features: int | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    bbox = validate_bbox(bbox)  # type: ignore[assignment]
    return await _fetch_and_parse_geo(
        "demanda_irrigacao",
        bbox=bbox,
        max_features=max_features,
        return_meta=return_meta,
    )


# ---------------------------------------------------------------------------
# disponibilidade_hidrica (uf optional, bbox optional)
# ---------------------------------------------------------------------------


@overload
async def disponibilidade_hidrica(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def disponibilidade_hidrica(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def disponibilidade_hidrica(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    uf = validate_uf(uf)
    bbox = validate_bbox(bbox)
    return await _fetch_and_parse_tabular(
        "disponibilidade_hidrica",
        uf=uf,
        bbox=bbox,
        max_features=max_features,
        as_polars=as_polars,
        return_meta=return_meta,
    )


@overload
async def disponibilidade_hidrica_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def disponibilidade_hidrica_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def disponibilidade_hidrica_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    max_features: int | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    uf = validate_uf(uf)
    bbox = validate_bbox(bbox)
    return await _fetch_and_parse_geo(
        "disponibilidade_hidrica",
        uf=uf,
        bbox=bbox,
        max_features=max_features,
        return_meta=return_meta,
    )
