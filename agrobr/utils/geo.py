from __future__ import annotations

from typing import Any

import httpx
import structlog

from agrobr.constants import MIN_WFS_SIZE
from agrobr.exceptions import SourceUnavailableError
from agrobr.http.retry import retry_on_status
from agrobr.http.user_agents import UserAgentRotator

logger = structlog.get_logger()


def check_geopandas() -> Any:
    try:
        import geopandas

        return geopandas
    except ImportError:
        raise ImportError(
            "geopandas is required for geo functions. Install with: pip install agrobr[geo]"
        ) from None


def validate_bbox(
    bbox: tuple[float, float, float, float] | None,
) -> tuple[float, float, float, float] | None:
    if bbox is None:
        return None
    if len(bbox) != 4:
        raise ValueError(
            f"BBOX deve ter 4 valores (minlon, minlat, maxlon, maxlat), recebeu {len(bbox)}"
        )
    minlon, minlat, maxlon, maxlat = bbox
    if minlon >= maxlon:
        raise ValueError(f"BBOX minlon ({minlon}) deve ser menor que maxlon ({maxlon})")
    if minlat >= maxlat:
        raise ValueError(f"BBOX minlat ({minlat}) deve ser menor que maxlat ({maxlat})")
    return bbox


async def fetch_wfs(
    url: str,
    *,
    source: str,
    timeout: httpx.Timeout,
    base_delay: float | None = None,
) -> bytes:
    async with httpx.AsyncClient(
        timeout=timeout, headers=UserAgentRotator.get_bot_headers(), follow_redirects=True
    ) as client:
        logger.debug(f"{source}_request", url=url)
        response = await retry_on_status(
            lambda: client.get(url),
            source=source,
            base_delay=base_delay,
        )

        if response.status_code == 404:
            raise SourceUnavailableError(source=source, url=url, last_error="HTTP 404")

        response.raise_for_status()

        content = response.content
        if len(content) < MIN_WFS_SIZE:
            raise SourceUnavailableError(
                source=source,
                url=url,
                last_error=(
                    f"WFS response too small ({len(content)} bytes), expected WFS feature data"
                ),
            )
        return content
