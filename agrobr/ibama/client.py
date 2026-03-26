from __future__ import annotations

import structlog

from agrobr.http.settings import get_timeout
from agrobr.utils.geo import build_wfs_url, fetch_wfs, fetch_wfs_paginated

from .models import (
    LAYER,
    MAX_FEATURES_GEO,
    NAMESPACE,
    PAGE_SIZE,
    PROPERTY_NAMES,
    PROPERTY_NAMES_GEO,
    WFS_BASE,
    WFS_VERSION,
)

logger = structlog.get_logger()

TIMEOUT = get_timeout(read=180.0)


def _build_cql(uf: str | None = None) -> str | None:
    if uf is None:
        return None
    return f"sig_uf='{uf}'"


async def fetch_embargos(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[list[bytes], str]:
    return await fetch_wfs_paginated(
        WFS_BASE,
        NAMESPACE,
        LAYER,
        WFS_VERSION,
        PROPERTY_NAMES,
        PAGE_SIZE,
        source="ibama",
        timeout=TIMEOUT,
        cql=_build_cql(uf),
        bbox=bbox,
    )


async def fetch_embargos_geo(
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    url = build_wfs_url(
        WFS_BASE,
        NAMESPACE,
        LAYER,
        WFS_VERSION,
        PROPERTY_NAMES_GEO,
        max_features=MAX_FEATURES_GEO,
        output_format="application/json",
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="ibama", timeout=TIMEOUT)
    logger.info("ibama_embargos_geojson", source="ibama", size=len(content))
    return content, url
