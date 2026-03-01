from __future__ import annotations

import re
from urllib.parse import quote

import httpx
import structlog

from agrobr.constants import MIN_WFS_SIZE, URLS, Fonte
from agrobr.exceptions import SourceUnavailableError
from agrobr.http.retry import retry_on_status
from agrobr.http.settings import get_timeout
from agrobr.http.user_agents import UserAgentRotator

from .models import (
    DETER_COLUNAS_WFS_AMZ,
    DETER_COLUNAS_WFS_CERRADO,
    DETER_COLUNAS_WFS_GEO_AMZ,
    DETER_COLUNAS_WFS_GEO_CERRADO,
    DETER_LAYERS,
    DETER_WORKSPACES,
    MAX_FEATURES_GEO,
    PRODES_COLUNAS_WFS,
    PRODES_COLUNAS_WFS_GEO,
    PRODES_LAYERS,
    PRODES_WORKSPACES,
)

logger = structlog.get_logger()

_UF_RE = re.compile(r"^[A-Z]{2}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

GEOSERVER_BASE = URLS[Fonte.DESMATAMENTO]["geoserver"]

TIMEOUT = get_timeout(read=120.0)

MAX_FEATURES_PER_REQUEST = 50000


def _build_wfs_url(
    workspace: str,
    layer: str,
    property_names: list[str],
    cql_filter: str | None = None,
    max_features: int = MAX_FEATURES_PER_REQUEST,
    output_format: str = "csv",
) -> str:
    props = ",".join(property_names)
    url = (
        f"{GEOSERVER_BASE}/{workspace}/ows"
        f"?service=WFS&version=1.0.0&request=GetFeature"
        f"&typeName={workspace}:{layer}"
        f"&outputFormat={quote(output_format)}"
        f"&propertyName={props}"
        f"&maxFeatures={max_features}"
    )
    if cql_filter:
        url += f"&CQL_FILTER={quote(cql_filter)}"
    return url


async def _fetch_url(url: str) -> bytes:
    async with httpx.AsyncClient(
        timeout=TIMEOUT, headers=UserAgentRotator.get_bot_headers(), follow_redirects=True
    ) as client:
        logger.debug("desmatamento_request", url=url)
        response = await retry_on_status(
            lambda: client.get(url),
            source="desmatamento",
        )

        if response.status_code == 404:
            raise SourceUnavailableError(source="desmatamento", url=url, last_error="HTTP 404")

        response.raise_for_status()

        content = response.content
        if len(content) < MIN_WFS_SIZE:
            raise SourceUnavailableError(
                source="desmatamento",
                url=url,
                last_error=(
                    f"WFS response too small ({len(content)} bytes), expected WFS feature data"
                ),
            )
        return content


def _build_state_cql(uf: str) -> str:
    uf_upper = uf.strip().upper()
    if not _UF_RE.match(uf_upper):
        raise ValueError(f"UF invalida: {uf!r}")
    estado = _uf_to_estado(uf_upper)
    if estado:
        return f"(state='{uf_upper}' OR state='{estado}')"
    return f"state='{uf_upper}'"


async def _fetch_prodes_raw(
    bioma: str,
    ano: int | None = None,
    uf: str | None = None,
    *,
    output_format: str = "csv",
    include_geometry: bool = False,
) -> tuple[bytes, str]:
    workspace = PRODES_WORKSPACES.get(bioma)
    layer = PRODES_LAYERS.get(bioma)
    if not workspace or not layer:
        raise SourceUnavailableError(
            source="desmatamento",
            url="",
            last_error=f"Bioma PRODES nao suportado: {bioma}",
        )

    if include_geometry:
        cols = PRODES_COLUNAS_WFS_GEO
        max_features = MAX_FEATURES_GEO
    else:
        cols = PRODES_COLUNAS_WFS
        max_features = MAX_FEATURES_PER_REQUEST

    filters: list[str] = []
    if ano is not None:
        filters.append(f"year={ano}")
    if uf is not None:
        filters.append(_build_state_cql(uf))

    cql = " AND ".join(filters) if filters else None
    url = _build_wfs_url(
        workspace, layer, cols, cql, max_features=max_features, output_format=output_format
    )
    content = await _fetch_url(url)
    return content, url


async def fetch_prodes(
    bioma: str,
    ano: int | None = None,
    uf: str | None = None,
) -> tuple[bytes, str]:
    content, url = await _fetch_prodes_raw(
        bioma, ano, uf, output_format="csv", include_geometry=False
    )
    logger.info("desmatamento_prodes_csv", url=url, size=len(content), bioma=bioma)
    return content, url


async def fetch_prodes_geo(
    bioma: str,
    ano: int | None = None,
    uf: str | None = None,
) -> tuple[bytes, str]:
    content, url = await _fetch_prodes_raw(
        bioma, ano, uf, output_format="application/json", include_geometry=True
    )
    logger.info("desmatamento_prodes_geojson", url=url, size=len(content), bioma=bioma)
    return content, url


async def _fetch_deter_raw(
    bioma: str,
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    *,
    output_format: str = "csv",
    include_geometry: bool = False,
) -> tuple[bytes, str]:
    workspace = DETER_WORKSPACES.get(bioma)
    layer = DETER_LAYERS.get(bioma)
    if not workspace or not layer:
        raise SourceUnavailableError(
            source="desmatamento",
            url="",
            last_error=f"Bioma DETER nao suportado: {bioma}",
        )

    if include_geometry:
        cols = DETER_COLUNAS_WFS_GEO_AMZ if bioma == "Amazônia" else DETER_COLUNAS_WFS_GEO_CERRADO
        max_features = MAX_FEATURES_GEO
    else:
        cols = DETER_COLUNAS_WFS_AMZ if bioma == "Amazônia" else DETER_COLUNAS_WFS_CERRADO
        max_features = MAX_FEATURES_PER_REQUEST

    filters: list[str] = []
    if uf is not None:
        uf_upper = uf.strip().upper()
        if not _UF_RE.match(uf_upper):
            raise ValueError(f"UF invalida: {uf!r}")
        filters.append(f"uf='{uf_upper}'")
    if data_inicio is not None:
        if not _DATE_RE.match(data_inicio):
            raise ValueError(f"data_inicio invalida (esperado YYYY-MM-DD): {data_inicio!r}")
        filters.append(f"view_date>='{data_inicio}'")
    if data_fim is not None:
        if not _DATE_RE.match(data_fim):
            raise ValueError(f"data_fim invalida (esperado YYYY-MM-DD): {data_fim!r}")
        filters.append(f"view_date<='{data_fim}'")

    cql = " AND ".join(filters) if filters else None
    url = _build_wfs_url(
        workspace, layer, cols, cql, max_features=max_features, output_format=output_format
    )
    content = await _fetch_url(url)
    return content, url


async def fetch_deter(
    bioma: str,
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> tuple[bytes, str]:
    content, url = await _fetch_deter_raw(
        bioma, uf, data_inicio, data_fim, output_format="csv", include_geometry=False
    )
    logger.info("desmatamento_deter_csv", url=url, size=len(content), bioma=bioma)
    return content, url


async def fetch_deter_geo(
    bioma: str,
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> tuple[bytes, str]:
    content, url = await _fetch_deter_raw(
        bioma, uf, data_inicio, data_fim, output_format="application/json", include_geometry=True
    )
    logger.info("desmatamento_deter_geojson", url=url, size=len(content), bioma=bioma)
    return content, url


_UF_TO_ESTADO: dict[str, str] = {
    v: k
    for k, v in {
        "ACRE": "AC",
        "ALAGOAS": "AL",
        "AMAPÁ": "AP",
        "AMAZONAS": "AM",
        "BAHIA": "BA",
        "CEARÁ": "CE",
        "DISTRITO FEDERAL": "DF",
        "ESPÍRITO SANTO": "ES",
        "GOIÁS": "GO",
        "MARANHÃO": "MA",
        "MATO GROSSO": "MT",
        "MATO GROSSO DO SUL": "MS",
        "MINAS GERAIS": "MG",
        "PARÁ": "PA",
        "PARAÍBA": "PB",
        "PARANÁ": "PR",
        "PERNAMBUCO": "PE",
        "PIAUÍ": "PI",
        "RIO DE JANEIRO": "RJ",
        "RIO GRANDE DO NORTE": "RN",
        "RIO GRANDE DO SUL": "RS",
        "RONDÔNIA": "RO",
        "RORAIMA": "RR",
        "SANTA CATARINA": "SC",
        "SÃO PAULO": "SP",
        "SERGIPE": "SE",
        "TOCANTINS": "TO",
    }.items()
}


def _uf_to_estado(uf: str) -> str | None:
    return _UF_TO_ESTADO.get(uf.upper())
