from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal, overload

import pandas as pd
import structlog

from agrobr.models import MetaInfo
from agrobr.utils.geo import validate_bbox
from agrobr.utils.result import build_source_meta, finalize_result
from agrobr.utils.validation import validate_uf as _validate_uf_optional
from agrobr.utils.warnings import warn_once

from . import client, parser
from .models import TIPOS_SIGEF, TIPOS_SNCI

if TYPE_CHECKING:
    import geopandas as gpd

logger = structlog.get_logger()

_NC_WARNING = (
    "Acervo Fundiario/INCRA: vedado o uso comercial — uso comercial requer "
    "autorizacao. Classificacao: nc. Veja docs/licenses.md."
)


def _validate_uf(uf: str) -> str:
    result = _validate_uf_optional(uf)
    if result is None:
        raise ValueError(f"UF invalida: {uf!r}")
    return result


def _validate_tipo(tipo: str, validos: frozenset[str], label: str) -> str:
    if tipo not in validos:
        raise ValueError(
            f"Tipo invalido para {label}: {tipo!r}. Valores aceitos: {sorted(validos)}"
        )
    return tipo


# ---------------------------------------------------------------------------
# SIGEF
# ---------------------------------------------------------------------------


@overload
async def sigef(
    uf: str,
    *,
    tipo: str = "particular",
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def sigef(
    uf: str,
    *,
    tipo: str = "particular",
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def sigef(
    uf: str,
    *,
    tipo: str = "particular",
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once("acervo_fundiario", _NC_WARNING)
    uf = _validate_uf(uf)
    tipo = _validate_tipo(tipo, TIPOS_SIGEF, "SIGEF")
    bbox = validate_bbox(bbox)
    logger.info("acervo_fundiario_sigef", uf=uf, tipo=tipo, bbox=bbox)

    t0 = time.monotonic()
    gml_bytes, source_url = await client.fetch_sigef(uf, tipo, bbox=bbox)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_sigef_gml(gml_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta(
        "acervo_fundiario",
        source_url,
        "httpx+wfs+gml2",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["acervo_fundiario_wfs"],
        selected_source="acervo_fundiario_wfs",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def sigef_geo(
    uf: str,
    *,
    tipo: str = "particular",
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def sigef_geo(
    uf: str,
    *,
    tipo: str = "particular",
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def sigef_geo(
    uf: str,
    *,
    tipo: str = "particular",
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    warn_once("acervo_fundiario", _NC_WARNING)
    uf = _validate_uf(uf)
    tipo = _validate_tipo(tipo, TIPOS_SIGEF, "SIGEF")
    bbox = validate_bbox(bbox)
    logger.info("acervo_fundiario_sigef_geo", uf=uf, tipo=tipo, bbox=bbox)

    t0 = time.monotonic()
    gml_bytes, source_url = await client.fetch_sigef(uf, tipo, bbox=bbox, geo=True)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_sigef_geo(gml_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        meta = build_source_meta(
            "acervo_fundiario",
            source_url,
            "httpx+wfs+gml2",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["acervo_fundiario_wfs_geo"],
            selected_source="acervo_fundiario_wfs_geo",
        )
        return gdf, meta
    return gdf


# ---------------------------------------------------------------------------
# SNCI
# ---------------------------------------------------------------------------


@overload
async def snci(
    uf: str,
    *,
    tipo: str = "privado",
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def snci(
    uf: str,
    *,
    tipo: str = "privado",
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def snci(
    uf: str,
    *,
    tipo: str = "privado",
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once("acervo_fundiario", _NC_WARNING)
    uf = _validate_uf(uf)
    tipo = _validate_tipo(tipo, TIPOS_SNCI, "SNCI")
    bbox = validate_bbox(bbox)
    logger.info("acervo_fundiario_snci", uf=uf, tipo=tipo, bbox=bbox)

    t0 = time.monotonic()
    gml_bytes, source_url = await client.fetch_snci(uf, tipo, bbox=bbox)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_snci_gml(gml_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta(
        "acervo_fundiario",
        source_url,
        "httpx+wfs+gml2",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["acervo_fundiario_wfs"],
        selected_source="acervo_fundiario_wfs",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def snci_geo(
    uf: str,
    *,
    tipo: str = "privado",
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def snci_geo(
    uf: str,
    *,
    tipo: str = "privado",
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def snci_geo(
    uf: str,
    *,
    tipo: str = "privado",
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    warn_once("acervo_fundiario", _NC_WARNING)
    uf = _validate_uf(uf)
    tipo = _validate_tipo(tipo, TIPOS_SNCI, "SNCI")
    bbox = validate_bbox(bbox)
    logger.info("acervo_fundiario_snci_geo", uf=uf, tipo=tipo, bbox=bbox)

    t0 = time.monotonic()
    gml_bytes, source_url = await client.fetch_snci(uf, tipo, bbox=bbox, geo=True)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_snci_geo(gml_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        meta = build_source_meta(
            "acervo_fundiario",
            source_url,
            "httpx+wfs+gml2",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["acervo_fundiario_wfs_geo"],
            selected_source="acervo_fundiario_wfs_geo",
        )
        return gdf, meta
    return gdf


# ---------------------------------------------------------------------------
# Assentamentos
# ---------------------------------------------------------------------------


@overload
async def assentamentos(
    uf: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
async def assentamentos(
    uf: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, MetaInfo]: ...


async def assentamentos(
    uf: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    as_polars: bool = False,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> pd.DataFrame | tuple[pd.DataFrame, MetaInfo]:
    warn_once("acervo_fundiario", _NC_WARNING)
    uf = _validate_uf(uf)
    bbox = validate_bbox(bbox)
    logger.info("acervo_fundiario_assentamentos", uf=uf, bbox=bbox)

    t0 = time.monotonic()
    gml_bytes, source_url = await client.fetch_assentamentos(uf, bbox=bbox)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    df = parser.parse_assentamentos_gml(gml_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    meta = build_source_meta(
        "acervo_fundiario",
        source_url,
        "httpx+wfs+gml2",
        fetch_ms,
        parse_ms,
        df,
        parser.PARSER_VERSION,
        attempted_sources=["acervo_fundiario_wfs"],
        selected_source="acervo_fundiario_wfs",
    )
    return finalize_result(df, meta, as_polars=as_polars, return_meta=return_meta)


@overload
async def assentamentos_geo(
    uf: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[False] = False,
) -> gpd.GeoDataFrame: ...


@overload
async def assentamentos_geo(
    uf: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: Literal[True],
) -> tuple[gpd.GeoDataFrame, MetaInfo]: ...


async def assentamentos_geo(
    uf: str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    return_meta: bool = False,
    **kwargs: Any,  # noqa: ARG001
) -> Any:
    warn_once("acervo_fundiario", _NC_WARNING)
    uf = _validate_uf(uf)
    bbox = validate_bbox(bbox)
    logger.info("acervo_fundiario_assentamentos_geo", uf=uf, bbox=bbox)

    t0 = time.monotonic()
    gml_bytes, source_url = await client.fetch_assentamentos(uf, bbox=bbox, geo=True)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    gdf = parser.parse_assentamentos_geo(gml_bytes)
    parse_ms = int((time.monotonic() - t1) * 1000)

    if return_meta:
        meta = build_source_meta(
            "acervo_fundiario",
            source_url,
            "httpx+wfs+gml2",
            fetch_ms,
            parse_ms,
            gdf,
            parser.PARSER_VERSION,
            attempted_sources=["acervo_fundiario_wfs_geo"],
            selected_source="acervo_fundiario_wfs_geo",
        )
        return gdf, meta
    return gdf
