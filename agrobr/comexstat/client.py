"""ComexStat bulk CSV client.

TLS: verify=False is required — SERPRO (balanca.economia.gov.br) does not
send the Sectigo intermediate certificate, breaking chain validation.
Confirmed via ``openssl s_client``.  Tracked upstream, no fix available.
"""

from __future__ import annotations

import httpx
import structlog

from agrobr.constants import MIN_CSV_SIZE, URLS, Fonte
from agrobr.http.retry import retry_on_status
from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator

logger = structlog.get_logger()

BULK_CSV_BASE = URLS[Fonte.COMEXSTAT]["bulk_csv"]

TIMEOUT = get_timeout(read=120.0)


async def download_csv(url: str) -> str:
    logger.debug("comexstat_download_csv", url=url)
    logger.info("comexstat_download_csv", source="comexstat")

    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        headers=UserAgentRotator.get_headers(source="comexstat"),
        follow_redirects=True,
        verify=False,
    ) as client:
        response = await retry_on_status(
            lambda: client.get(url),
            source="comexstat",
        )

        response.raise_for_status()

        content = response.text

        if len(content) < MIN_CSV_SIZE or ";" not in content:
            from agrobr.exceptions import SourceUnavailableError

            raise SourceUnavailableError(
                source="comexstat",
                url=url,
                last_error=(
                    f"CSV response too small or missing delimiter "
                    f"({len(content)} chars, no ';' separator found)"
                ),
            )

        logger.info(
            "comexstat_download_ok",
            source="comexstat",
            size_chars=len(content),
        )
        return content


async def fetch_exportacao_csv(ano: int) -> str:
    url = f"{BULK_CSV_BASE}/EXP_{ano}.csv"
    return await download_csv(url)


async def fetch_importacao_csv(ano: int) -> str:
    url = f"{BULK_CSV_BASE}/IMP_{ano}.csv"
    return await download_csv(url)
