from __future__ import annotations

from functools import partial
from typing import Any
from urllib.parse import quote

import httpx
import structlog

from agrobr.constants import URLS, Fonte
from agrobr.http.retry import retry_on_status
from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator

logger = structlog.get_logger()

FOCUS_BASE = URLS[Fonte.BCB]["focus"]

TIMEOUT = get_timeout(read=30.0)


async def fetch_focus(
    indicador: str,
    *,
    top: int = 1000,
) -> tuple[list[dict[str, Any]], str]:
    safe_indicador = indicador.replace("'", "''")
    endpoint = "ExpectativasMercadoAnuais"
    url = f"{FOCUS_BASE}/{endpoint}"

    all_records: list[dict[str, Any]] = []
    skip = 0

    logger.info("bcb_focus_request", indicador=indicador, top=top)

    filtro = quote(f"Indicador eq '{safe_indicador}'", safe="'")

    async with httpx.AsyncClient(
        timeout=TIMEOUT, headers=UserAgentRotator.get_bot_headers(), follow_redirects=True
    ) as client:
        while True:
            page_url = (
                f"{url}?$format=json&$filter={filtro}&$orderby=Data%20desc&$top={top}&$skip={skip}"
            )

            response = await retry_on_status(
                partial(client.get, page_url),
                source="bcb",
            )

            response.raise_for_status()
            data = response.json()

            records = data.get("value", [])
            if not records:
                break

            all_records.extend(records)
            logger.debug(
                "bcb_focus_page_fetched",
                skip=skip,
                records_in_page=len(records),
                total_so_far=len(all_records),
            )

            if len(records) < top:
                break

            skip += top

    logger.info("bcb_focus_ok", indicador=indicador, total_records=len(all_records))
    return all_records, url
