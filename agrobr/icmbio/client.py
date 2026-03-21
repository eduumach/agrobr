from __future__ import annotations

import re
from urllib.parse import quote

import structlog

from agrobr.http.settings import get_timeout
from agrobr.utils.geo import fetch_wfs

from .models import (
    LAYER,
    MAX_FEATURES_GEO,
    MAX_FEATURES_TABULAR,
    NAMESPACE,
    PROPERTY_NAMES,
    PROPERTY_NAMES_GEO,
    WFS_BASE,
    WFS_VERSION,
)

logger = structlog.get_logger()

_UF_RE = re.compile(r"^[A-Z]{2}$")

TIMEOUT = get_timeout(read=120.0)


def _build_wfs_url(
    property_names: list[str],
    *,
    cql_filter: str | None = None,
    max_features: int = MAX_FEATURES_TABULAR,
    output_format: str = "csv",
    bbox: tuple[float, float, float, float] | None = None,
) -> str:
    props = ",".join(property_names)
    url = (
        f"{WFS_BASE}"
        f"?service=WFS&version={WFS_VERSION}&request=GetFeature"
        f"&typeName={NAMESPACE}:{LAYER}"
        f"&outputFormat={quote(output_format)}"
        f"&propertyName={props}"
        f"&maxFeatures={max_features}"
    )
    if cql_filter:
        url += f"&CQL_FILTER={quote(cql_filter)}"
    if bbox is not None:
        minlon, minlat, maxlon, maxlat = bbox
        url += f"&BBOX={minlon},{minlat},{maxlon},{maxlat},EPSG:4674"
    return url


def _build_cql_filters(
    *,
    uf: str | None = None,
    grupo: str | None = None,
    bioma: str | None = None,
) -> str | None:
    filters: list[str] = []
    if uf is not None:
        uf_upper = uf.strip().upper()
        if not _UF_RE.match(uf_upper):
            raise ValueError(f"UF invalida: {uf!r}")
        filters.append(f"ufabrang LIKE '%{uf_upper}%'")
    if grupo is not None:
        grupo_upper = grupo.strip().upper()
        filters.append(f"grupouc='{grupo_upper}'")
    if bioma is not None:
        filters.append(f"biomaibge='{bioma}'")
    return " AND ".join(filters) if filters else None


async def fetch_ucs(
    *,
    uf: str | None = None,
    grupo: str | None = None,
    bioma: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    cql = _build_cql_filters(uf=uf, grupo=grupo, bioma=bioma)
    url = _build_wfs_url(
        PROPERTY_NAMES,
        cql_filter=cql,
        max_features=MAX_FEATURES_TABULAR,
        output_format="csv",
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="icmbio", timeout=TIMEOUT)
    logger.info("icmbio_ucs_csv", source="icmbio", size=len(content))
    return content, url


async def fetch_ucs_geo(
    *,
    uf: str | None = None,
    grupo: str | None = None,
    bioma: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    cql = _build_cql_filters(uf=uf, grupo=grupo, bioma=bioma)
    url = _build_wfs_url(
        PROPERTY_NAMES_GEO,
        cql_filter=cql,
        max_features=MAX_FEATURES_GEO,
        output_format="application/json",
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="icmbio", timeout=TIMEOUT)
    logger.info("icmbio_ucs_geojson", source="icmbio", size=len(content))
    return content, url
