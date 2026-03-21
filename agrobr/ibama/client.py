from __future__ import annotations

import math
import re
from urllib.parse import quote

import structlog

from agrobr.exceptions import ParseError
from agrobr.http.settings import get_timeout
from agrobr.utils.geo import fetch_wfs

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

_UF_RE = re.compile(r"^[A-Z]{2}$")

TIMEOUT = get_timeout(read=180.0)

_THROTTLE_AFTER_PAGE = 5
_THROTTLE_DELAY = 2.0


def _build_wfs_url(
    property_names: list[str],
    *,
    cql_filter: str | None = None,
    count: int = PAGE_SIZE,
    start_index: int = 0,
    result_type: str | None = None,
    output_format: str = "csv",
    bbox: tuple[float, float, float, float] | None = None,
) -> str:
    props = ",".join(property_names)
    url = (
        f"{WFS_BASE}"
        f"?service=WFS&version={WFS_VERSION}&request=GetFeature"
        f"&typeNames={NAMESPACE}:{LAYER}"
        f"&outputFormat={quote(output_format)}"
        f"&propertyName={props}"
        f"&count={count}"
        f"&startIndex={start_index}"
    )
    if result_type:
        url += f"&resultType={result_type}"
    if cql_filter:
        url += f"&CQL_FILTER={quote(cql_filter)}"
    if bbox is not None:
        minlon, minlat, maxlon, maxlat = bbox
        url += f"&BBOX={minlon},{minlat},{maxlon},{maxlat},EPSG:4674"
    return url


def _build_cql(uf: str | None = None) -> str | None:
    if uf is None:
        return None
    uf_upper = uf.strip().upper()
    if not _UF_RE.match(uf_upper):
        raise ValueError(f"UF invalida: {uf!r}")
    return f"sig_uf='{uf_upper}'"


async def fetch_hits(cql_filter: str | None = None) -> int:
    url = _build_wfs_url(PROPERTY_NAMES, cql_filter=cql_filter, result_type="hits")
    content = await fetch_wfs(url, source="ibama", timeout=TIMEOUT)

    text = content.decode("utf-8", errors="replace")
    match = re.search(r'numberMatched="(\d+)"', text)
    if match:
        return int(match.group(1))

    match = re.search(r"numberMatched=(\d+)", text)
    if match:
        return int(match.group(1))

    raise ParseError(
        source="ibama",
        parser_version=1,
        reason=f"Nao encontrou numberMatched na resposta hits: {text[:200]}",
    )


async def fetch_embargos(
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[list[bytes], str]:
    cql = _build_cql(uf)
    total = await fetch_hits(cql)
    logger.info("ibama_hits", total=total, uf=uf, cql_filter=cql)

    if total == 0:
        url = _build_wfs_url(PROPERTY_NAMES, cql_filter=cql, bbox=bbox)
        return [], url

    n_pages = math.ceil(total / PAGE_SIZE)
    pages: list[bytes] = []
    first_url = ""

    for i in range(n_pages):
        start_index = i * PAGE_SIZE
        url = _build_wfs_url(
            PROPERTY_NAMES,
            cql_filter=cql,
            count=PAGE_SIZE,
            start_index=start_index,
            bbox=bbox,
        )
        if i == 0:
            first_url = url
        delay = _THROTTLE_DELAY if i >= _THROTTLE_AFTER_PAGE else None
        content = await fetch_wfs(url, source="ibama", timeout=TIMEOUT, base_delay=delay)
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
    url = _build_wfs_url(
        PROPERTY_NAMES_GEO,
        cql_filter=cql,
        count=MAX_FEATURES_GEO,
        output_format="application/json",
        bbox=bbox,
    )
    content = await fetch_wfs(url, source="ibama", timeout=TIMEOUT)
    logger.info("ibama_embargos_geojson", source="ibama", size=len(content))
    return content, url
