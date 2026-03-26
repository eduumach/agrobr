from __future__ import annotations

import httpx
import structlog

from agrobr.constants import URLS, Fonte
from agrobr.http.retry import retry_on_status
from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator

logger = structlog.get_logger()

_BASE_URL = URLS[Fonte.RNC]["cultivarweb"]
_REGISTRADAS_URL = f"{_BASE_URL}/cultivares_registradas.php"
_PROTEGIDAS_URL = f"{_BASE_URL}/cultivares_protegidas.php"

TIMEOUT = get_timeout(read=120.0)
MIN_CSV_SIZE = 500_000


async def _fetch_csv(base_url: str, label: str) -> tuple[bytes, str]:
    logger.debug("rnc_fetch", label=label, url=base_url)

    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        headers=UserAgentRotator.get_headers(source="rnc"),
        follow_redirects=True,
    ) as http:
        search_resp = await retry_on_status(
            lambda: http.post(
                base_url,
                data={"postado": "1", "cod_pagina": "1", "validar": "0", "acao": "Pesquisar"},
            ),
            source="rnc",
        )
        search_resp.raise_for_status()

        export_url = f"{base_url}?postado=1&acao=pesquisar"
        response = await retry_on_status(
            lambda: http.post(export_url, data={"exportar": "csv"}),
            source="rnc",
        )
        response.raise_for_status()
        content = response.content

        if len(content) < MIN_CSV_SIZE:
            from agrobr.exceptions import SourceUnavailableError

            raise SourceUnavailableError(
                source="rnc",
                url=export_url,
                last_error=f"CSV {label} too small ({len(content)} bytes)",
            )

    logger.info("rnc_fetch_ok", label=label, size_bytes=len(content))
    return content, export_url


async def fetch_registradas() -> tuple[bytes, str]:
    return await _fetch_csv(_REGISTRADAS_URL, "registradas")


async def fetch_protegidas() -> tuple[bytes, str]:
    return await _fetch_csv(_PROTEGIDAS_URL, "protegidas")
