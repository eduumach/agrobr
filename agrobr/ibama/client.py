from __future__ import annotations

import math

import httpx
import structlog

from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator
from agrobr.utils.geo import build_wfs_url, fetch_wfs, parse_wfs_hits

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

_THROTTLE_AFTER_PAGE = 5
_THROTTLE_DELAY = 2.0


def _build_cql(uf: str | None = None) -> str | None:
    if uf is None:
        return None
    return f"sig_uf='{uf}'"


async def fetch_hits(cql_filter: str | None = None) -> int:
    url = build_wfs_url(
        WFS_BASE,
        NAMESPACE,
        LAYER,
        WFS_VERSION,
        PROPERTY_NAMES,
        max_features=PAGE_SIZE,
        cql_filter=cql_filter,
        result_type="hits",
    )
    content = await fetch_wfs(url, source="ibama", timeout=TIMEOUT)
    return parse_wfs_hits(content, source="ibama")


async def fetch_embargos(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[list[bytes], str]:
    cql = _build_cql(uf)
    total = await fetch_hits(cql)
    logger.info("ibama_hits", total=total, uf=uf, cql_filter=cql)

    if total == 0:
        url = build_wfs_url(
            WFS_BASE,
            NAMESPACE,
            LAYER,
            WFS_VERSION,
            PROPERTY_NAMES,
            max_features=PAGE_SIZE,
            cql_filter=cql,
            bbox=bbox,
        )
        return [], url

    n_pages = math.ceil(total / PAGE_SIZE)
    pages: list[bytes] = []
    first_url = ""

    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        headers=UserAgentRotator.get_bot_headers(),
        follow_redirects=True,
    ) as http:
        for i in range(n_pages):
            start_index = i * PAGE_SIZE
            url = build_wfs_url(
                WFS_BASE,
                NAMESPACE,
                LAYER,
                WFS_VERSION,
                PROPERTY_NAMES,
                max_features=PAGE_SIZE,
                cql_filter=cql,
                start_index=start_index,
                bbox=bbox,
            )
            if i == 0:
                first_url = url
            delay = _THROTTLE_DELAY if i >= _THROTTLE_AFTER_PAGE else None
            content = await fetch_wfs(
                url,
                source="ibama",
                timeout=TIMEOUT,
                base_delay=delay,
                client=http,
            )
            pages.append(content)
            logger.debug(
                "ibama_page",
                page=i + 1,
                total_pages=n_pages,
                size=len(content),
            )

    return pages, first_url


async def fetch_embargos_geo(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[bytes, str]:
    cql = _build_cql(uf)
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
    content = await fetch_wfs(url, source="ibama", timeout=TIMEOUT)
    logger.info("ibama_embargos_geojson", source="ibama", size=len(content))
    return content, url
