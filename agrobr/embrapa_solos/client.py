from __future__ import annotations

import structlog

from agrobr.http.settings import get_timeout
from agrobr.utils.geo import build_wfs_url, fetch_wfs, fetch_wfs_paginated

from .models import (
    MAPA_LAYER,
    MAPA_MAX_FEATURES_GEO,
    MAPA_NAMESPACE,
    MAPA_PAGE_SIZE,
    MAPA_PROPERTY_NAMES,
    MAPA_PROPERTY_NAMES_GEO,
    PERFIS_LAYER,
    PERFIS_MAX_FEATURES_GEO,
    PERFIS_NAMESPACE,
    PERFIS_PAGE_SIZE,
    PERFIS_PROPERTY_NAMES,
    PERFIS_PROPERTY_NAMES_GEO,
    WFS_BASE,
    WFS_VERSION,
)

logger = structlog.get_logger()

TIMEOUT = get_timeout(read=180.0)


async def fetch_perfis(
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[list[bytes], str]:
    return await fetch_wfs_paginated(
        WFS_BASE,
        PERFIS_NAMESPACE,
        PERFIS_LAYER,
        WFS_VERSION,
        PERFIS_PROPERTY_NAMES,
        PERFIS_PAGE_SIZE,
        source="embrapa_solos",
        timeout=TIMEOUT,
        bbox=bbox,
    )


async def fetch_perfis_geo(
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    url = build_wfs_url(
        WFS_BASE,
        PERFIS_NAMESPACE,
        PERFIS_LAYER,
        WFS_VERSION,
        PERFIS_PROPERTY_NAMES_GEO,
        max_features=PERFIS_MAX_FEATURES_GEO,
        output_format="application/json",
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="embrapa_solos", timeout=TIMEOUT)
    logger.info("embrapa_solos_perfis_geojson", size=len(content))
    return content, url


async def fetch_mapa_solos(
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[list[bytes], str]:
    return await fetch_wfs_paginated(
        WFS_BASE,
        MAPA_NAMESPACE,
        MAPA_LAYER,
        WFS_VERSION,
        MAPA_PROPERTY_NAMES,
        MAPA_PAGE_SIZE,
        source="embrapa_solos",
        timeout=TIMEOUT,
        bbox=bbox,
    )


async def fetch_mapa_solos_geo(
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    url = build_wfs_url(
        WFS_BASE,
        MAPA_NAMESPACE,
        MAPA_LAYER,
        WFS_VERSION,
        MAPA_PROPERTY_NAMES_GEO,
        max_features=MAPA_MAX_FEATURES_GEO,
        output_format="application/json",
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="embrapa_solos", timeout=TIMEOUT)
    logger.info("embrapa_solos_mapa_geojson", size=len(content))
    return content, url
