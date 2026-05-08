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


async def fetch_quilombolas(
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    url = build_wfs_url(
        WFS_BASE,
        NAMESPACE,
        LAYER,
        WFS_VERSION,
        PROPERTY_NAMES,
        max_features=MAX_FEATURES_TABULAR,
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="incra", timeout=TIMEOUT)
    logger.info("incra_quilombolas_csv", source="incra", size=len(content))
    return content, url


async def fetch_quilombolas_geo(
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
    content = await fetch_wfs(url, source="incra", timeout=TIMEOUT)
    logger.info("incra_quilombolas_geojson", source="incra", size=len(content))
    return content, url
