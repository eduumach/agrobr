from __future__ import annotations

import structlog

from agrobr.http.settings import get_timeout
from agrobr.utils.geo import build_wfs_url, fetch_wfs

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

TIMEOUT = get_timeout(read=120.0)


def _build_cql(
    uf: str | None = None,
    fase: str | None = None,
) -> str | None:
    filters: list[str] = []
    if uf is not None:
        filters.append(f"uf_sigla='{uf}'")
    if fase is not None:
        filters.append(f"fase_ti='{fase}'")
    return " AND ".join(filters) if filters else None


async def fetch_terras_indigenas(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    cql = _build_cql(uf, fase)
    url = build_wfs_url(
        WFS_BASE,
        NAMESPACE,
        LAYER,
        WFS_VERSION,
        PROPERTY_NAMES,
        max_features=MAX_FEATURES_TABULAR,
        cql_filter=cql,
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="funai", timeout=TIMEOUT)
    logger.info("funai_terras_indigenas_csv", source="funai", size=len(content))
    return content, url


async def fetch_terras_indigenas_geo(
    *,
    uf: str | None = None,
    fase: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    cql = _build_cql(uf, fase)
    url = build_wfs_url(
        WFS_BASE,
        NAMESPACE,
        LAYER,
        WFS_VERSION,
        PROPERTY_NAMES_GEO,
        max_features=MAX_FEATURES_GEO,
        output_format="application/json",
        cql_filter=cql,
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="funai", timeout=TIMEOUT)
    logger.info("funai_terras_indigenas_geojson", source="funai", size=len(content))
    return content, url
