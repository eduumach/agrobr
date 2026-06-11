"""SICAR WFS client.

TLS: verify=False is required — geoserver.car.gov.br ships the Sectigo Root R46
inside the chain (self-signed leaf at position 2). Clients whose truststore
does not include that root (ex.: certifi pre-2024, uv-managed Python on macOS)
fail with ``CERTIFICATE_VERIFY_FAILED: self-signed certificate in certificate
chain``. Data is public, no credentials trafficked, payload validated downstream
(``utils/geo.fetch_wfs`` rejects HTML/ServiceException/short bodies; parser
enforces ``required_cols``). SECLEVEL=1 kept for the GeoServer cipher set.
"""

from __future__ import annotations

import asyncio
import math
import ssl
from collections.abc import AsyncGenerator
from urllib.parse import quote

import httpx
import structlog

from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator
from agrobr.utils.geo import fetch_wfs, parse_wfs_hits
from agrobr.utils.warnings import warn_once

from .models import (
    MAX_FEATURES_GEO,
    PAGE_SIZE,
    PROPERTY_NAMES,
    PROPERTY_NAMES_GEO,
    WFS_BASE,
    WFS_VERSION,
    layer_name,
)

logger = structlog.get_logger()

TIMEOUT = get_timeout(read=180.0)

THROTTLE_AFTER_PAGE = 5
THROTTLE_DELAY = 2.0

GEO_BATCH_SIZE = 1

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE
_ssl_ctx.set_ciphers("DEFAULT:@SECLEVEL=1")

_SSL_WARNING = (
    "SICAR (geoserver.car.gov.br) usa verify=False: o servidor envia o root "
    "CA Sectigo R46 dentro da cadeia, quebrando a validacao em truststores "
    "sem esse root. Dado e publico e payload e validado downstream."
)


def make_session() -> httpx.AsyncClient:
    """Cria `AsyncClient` com config padrao SICAR (TLS verify off + UA + redirects)."""
    warn_once("sicar_ssl_verify_off", _SSL_WARNING)
    return httpx.AsyncClient(
        timeout=TIMEOUT,
        headers=UserAgentRotator.get_bot_headers(),
        follow_redirects=True,
        verify=_ssl_ctx,
    )


def _build_wfs_url(
    uf: str,
    *,
    cql_filter: str | None = None,
    count: int | None = PAGE_SIZE,
    start_index: int = 0,
    result_type: str | None = None,
    output_format: str = "csv",
    property_names: list[str] | None = None,
) -> str:
    props = ",".join(property_names or PROPERTY_NAMES)
    layer = layer_name(uf)

    url = (
        f"{WFS_BASE}"
        f"?service=WFS&version={WFS_VERSION}&request=GetFeature"
        f"&typeNames=sicar:{layer}"
        f"&outputFormat={output_format}"
        f"&propertyName={props}"
    )
    if count is not None:
        url += f"&count={count}"
    url += f"&startIndex={start_index}"
    if result_type:
        url += f"&resultType={result_type}"
    if cql_filter:
        url += f"&CQL_FILTER={quote(cql_filter)}"
    return url


async def fetch_hits(
    uf: str,
    cql_filter: str | None = None,
    *,
    client: httpx.AsyncClient | None = None,
) -> int:
    url = _build_wfs_url(uf, cql_filter=cql_filter, result_type="hits")
    content = await fetch_wfs(url, source="sicar", timeout=TIMEOUT, client=client)
    return parse_wfs_hits(content, source="sicar")


async def fetch_imoveis(uf: str, cql_filter: str | None = None) -> tuple[list[bytes], str]:
    async with make_session() as http:
        total = await fetch_hits(uf, cql_filter, client=http)
        logger.info("sicar_hits", uf=uf, total=total, cql_filter=cql_filter)

        if total == 0:
            url = _build_wfs_url(uf, cql_filter=cql_filter)
            return [], url

        n_pages = math.ceil(total / PAGE_SIZE)
        pages: list[bytes] = []
        base_url = _build_wfs_url(uf, cql_filter=cql_filter)

        for i in range(n_pages):
            start_index = i * PAGE_SIZE
            url = _build_wfs_url(
                uf,
                cql_filter=cql_filter,
                count=PAGE_SIZE,
                start_index=start_index,
            )
            content = await fetch_wfs(
                url,
                source="sicar",
                timeout=TIMEOUT,
                client=http,
            )
            pages.append(content)
            logger.debug(
                "sicar_page",
                uf=uf,
                page=i + 1,
                total_pages=n_pages,
                size=len(content),
            )
            if i >= THROTTLE_AFTER_PAGE:
                await asyncio.sleep(THROTTLE_DELAY)

    return pages, base_url


async def stream_imoveis_geo(
    uf: str,
    cql_filter: str | None = None,
    max_features: int | None = MAX_FEATURES_GEO,
) -> AsyncGenerator[tuple[list[bytes], str], None]:
    """Yields (batch_pages, source_url) conforme as paginas sao baixadas.

    Quando max_features e None, cada yield corresponde a um batch paralelo de
    GEO_BATCH_SIZE paginas. Isso evita acumular todo o estado bruto em memoria.
    """
    if max_features is not None and max_features <= PAGE_SIZE:
        url = _build_wfs_url(
            uf,
            cql_filter=cql_filter,
            count=max_features,
            output_format="application/json",
            property_names=PROPERTY_NAMES_GEO,
        )
        async with make_session() as http:
            content = await fetch_wfs(url, source="sicar", timeout=TIMEOUT, client=http)
        logger.info("sicar_imoveis_geojson", source="sicar", size=len(content), uf=uf)
        yield [content], url
        return

    async with make_session() as http:
        total = await fetch_hits(uf, cql_filter, client=http)
        logger.info("sicar_geo_hits", uf=uf, total=total, cql_filter=cql_filter)

        limit = min(total, max_features) if max_features is not None else total

        base_url = _build_wfs_url(
            uf,
            cql_filter=cql_filter,
            output_format="application/json",
            property_names=PROPERTY_NAMES_GEO,
        )

        if limit == 0:
            yield [], base_url
            return

        n_pages = math.ceil(limit / PAGE_SIZE)

        async def fetch_page(i: int) -> bytes:
            count = min(PAGE_SIZE, limit - i * PAGE_SIZE)
            url = _build_wfs_url(
                uf,
                cql_filter=cql_filter,
                count=count,
                start_index=i * PAGE_SIZE,
                output_format="application/json",
                property_names=PROPERTY_NAMES_GEO,
            )
            content = await fetch_wfs(
                url,
                source="sicar",
                timeout=TIMEOUT,
                client=http,
            )
            logger.debug(
                "sicar_geo_page",
                uf=uf,
                page=i + 1,
                total_pages=n_pages,
                size=len(content),
            )
            if i >= THROTTLE_AFTER_PAGE:
                await asyncio.sleep(THROTTLE_DELAY)
            return content

        if max_features is None:
            for start in range(0, n_pages, GEO_BATCH_SIZE):
                batch = range(start, min(start + GEO_BATCH_SIZE, n_pages))
                pages = list(await asyncio.gather(*(fetch_page(i) for i in batch)))
                yield pages, base_url
        else:
            pages = [await fetch_page(i) for i in range(n_pages)]
            yield pages, base_url

    logger.info("sicar_imoveis_geojson", source="sicar", pages=n_pages, uf=uf)


async def fetch_imoveis_geo(
    uf: str,
    cql_filter: str | None = None,
    max_features: int | None = MAX_FEATURES_GEO,
) -> tuple[list[bytes], str]:
    """Acumula todas as paginas em memoria. Use stream_imoveis_geo para baixo consumo."""
    all_pages: list[bytes] = []
    source_url = ""
    async for batch, url in stream_imoveis_geo(uf, cql_filter, max_features):
        all_pages.extend(batch)
        source_url = url
    return all_pages, source_url
