from __future__ import annotations

from functools import partial

import httpx
import structlog
from bs4 import BeautifulSoup

from agrobr.constants import MIN_XLSX_SIZE, URLS, Fonte
from agrobr.exceptions import SourceUnavailableError
from agrobr.http.retry import retry_on_status
from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator

from .models import BASE_URL

_CONAB_BASE = URLS[Fonte.CONAB]["base"]

logger = structlog.get_logger()

TIMEOUT = get_timeout(read=60.0)

PAGE_SIZE = 20


def _extract_week_links(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    results: list[tuple[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        text = a.get_text(strip=True)
        if "acompanhamento-das-lavouras" in href and "Acompanhamento" in text and href not in seen:
            seen.add(href)
            full = href if href.startswith("http") else f"{_CONAB_BASE}{href}"
            results.append((text, full))
    return results


def _extract_plantio_link(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        if "plantio" in href.lower() and "colheita" in href.lower():
            return href if href.startswith("http") else f"{_CONAB_BASE}{href}"
    return None


async def list_semanas(max_pages: int = 4) -> list[tuple[str, str]]:
    all_weeks: list[tuple[str, str]] = []
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        headers=UserAgentRotator.get_headers(source="conab_progresso"),
        follow_redirects=True,
    ) as client:
        for page in range(max_pages):
            offset = page * PAGE_SIZE
            url = f"{BASE_URL}?b_start:int={offset}" if offset else BASE_URL
            logger.debug("conab_progresso_list", url=url, page=page)
            response = await retry_on_status(partial(client.get, url), source="conab")
            if response.status_code != 200:
                break
            weeks = _extract_week_links(response.text)
            if not weeks:
                break
            all_weeks.extend(weeks)
    return all_weeks


async def fetch_xlsx_semanal(week_url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        headers=UserAgentRotator.get_headers(source="conab_progresso"),
        follow_redirects=True,
    ) as client:
        logger.debug("conab_progresso_week", url=week_url)
        resp = await retry_on_status(lambda: client.get(week_url), source="conab")
        if resp.status_code != 200:
            raise SourceUnavailableError(
                source="conab_progresso",
                url=week_url,
                last_error=f"HTTP {resp.status_code}",
            )

        xlsx_url = _extract_plantio_link(resp.text)
        if xlsx_url is None:
            raise SourceUnavailableError(
                source="conab_progresso",
                url=week_url,
                last_error="Link plantio/colheita nao encontrado na pagina semanal",
            )

        logger.debug("conab_progresso_xlsx", url=xlsx_url)
        xlsx_resp = await retry_on_status(lambda: client.get(xlsx_url), source="conab")
        if xlsx_resp.status_code != 200:
            raise SourceUnavailableError(
                source="conab_progresso",
                url=xlsx_url,
                last_error=f"HTTP {xlsx_resp.status_code}",
            )

        ct = xlsx_resp.headers.get("content-type", "")
        if "spreadsheet" not in ct and "excel" not in ct and len(xlsx_resp.content) < MIN_XLSX_SIZE:
            raise SourceUnavailableError(
                source="conab_progresso",
                url=xlsx_url,
                last_error=f"Content-Type inesperado: {ct}",
            )

        logger.info(
            "conab_progresso_xlsx_ok", source="conab_progresso", size=len(xlsx_resp.content)
        )
        return xlsx_resp.content, xlsx_url


async def fetch_latest() -> tuple[bytes, str, str]:
    weeks = await list_semanas(max_pages=1)
    if not weeks:
        raise SourceUnavailableError(
            source="conab_progresso",
            url=BASE_URL,
            last_error="Nenhuma semana encontrada na listagem",
        )

    desc, week_url = weeks[0]
    xlsx_bytes, xlsx_url = await fetch_xlsx_semanal(week_url)
    return xlsx_bytes, xlsx_url, desc
