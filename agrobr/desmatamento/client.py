from __future__ import annotations

import re
from collections.abc import AsyncGenerator
from urllib.parse import quote

import structlog

from agrobr.constants import URLS, Fonte
from agrobr.exceptions import SourceUnavailableError
from agrobr.http.settings import get_timeout
from agrobr.utils.geo import fetch_wfs, stream_wfs_paginated

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

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

GEOSERVER_BASE = URLS[Fonte.DESMATAMENTO]["geoserver"]

TIMEOUT = get_timeout(read=120.0)

MAX_FEATURES_PER_REQUEST = 50000

# Streaming (paginacao WFS 2.0.0 via startIndex/count para baixo consumo de memoria)
STREAM_WFS_VERSION = "2.0.0"
STREAM_PAGE_SIZE = 5_000


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


def _build_state_cql(uf: str) -> str:
    uf_upper = uf.strip().upper()
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
    content = await fetch_wfs(url, source="desmatamento", timeout=TIMEOUT)
    return content, url


async def fetch_prodes(
    bioma: str,
    ano: int | None = None,
    uf: str | None = None,
) -> tuple[bytes, str]:
    content, url = await _fetch_prodes_raw(
        bioma, ano, uf, output_format="csv", include_geometry=False
    )
    logger.info("desmatamento_prodes_csv", source="desmatamento", size=len(content), bioma=bioma)
    return content, url


async def fetch_prodes_geo(
    bioma: str,
    ano: int | None = None,
    uf: str | None = None,
) -> tuple[bytes, str]:
    content, url = await _fetch_prodes_raw(
        bioma, ano, uf, output_format="application/json", include_geometry=True
    )
    logger.info(
        "desmatamento_prodes_geojson", source="desmatamento", size=len(content), bioma=bioma
    )
    return content, url


def _resolve_deter_layer(bioma: str) -> tuple[str, str]:
    workspace = DETER_WORKSPACES.get(bioma)
    layer = DETER_LAYERS.get(bioma)
    if not workspace or not layer:
        raise SourceUnavailableError(
            source="desmatamento",
            url="",
            last_error=f"Bioma DETER nao suportado: {bioma}",
        )
    return workspace, layer


def _build_deter_cql(
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> str | None:
    filters: list[str] = []
    if uf is not None:
        filters.append(f"uf='{uf}'")
    if data_inicio is not None:
        if not _DATE_RE.match(data_inicio):
            raise ValueError(f"data_inicio invalida (esperado YYYY-MM-DD): {data_inicio!r}")
        filters.append(f"view_date>='{data_inicio}'")
    if data_fim is not None:
        if not _DATE_RE.match(data_fim):
            raise ValueError(f"data_fim invalida (esperado YYYY-MM-DD): {data_fim!r}")
        filters.append(f"view_date<='{data_fim}'")
    return " AND ".join(filters) if filters else None


async def _fetch_deter_raw(
    bioma: str,
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    *,
    output_format: str = "csv",
    include_geometry: bool = False,
) -> tuple[bytes, str]:
    workspace, layer = _resolve_deter_layer(bioma)

    if include_geometry:
        cols = DETER_COLUNAS_WFS_GEO_AMZ if bioma == "Amazônia" else DETER_COLUNAS_WFS_GEO_CERRADO
        max_features = MAX_FEATURES_GEO
    else:
        cols = DETER_COLUNAS_WFS_AMZ if bioma == "Amazônia" else DETER_COLUNAS_WFS_CERRADO
        max_features = MAX_FEATURES_PER_REQUEST

    cql = _build_deter_cql(uf, data_inicio, data_fim)
    url = _build_wfs_url(
        workspace, layer, cols, cql, max_features=max_features, output_format=output_format
    )
    content = await fetch_wfs(url, source="desmatamento", timeout=TIMEOUT)
    return content, url


async def stream_deter_geo(
    bioma: str,
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    *,
    page_size: int = STREAM_PAGE_SIZE,
) -> AsyncGenerator[tuple[bytes, str], None]:
    """Yields (page_bytes, url) de GeoJSON DETER conforme as paginas WFS sao baixadas.

    Pagina via WFS 2.0.0 (startIndex/count) sem acumular o estado bruto em
    memoria nem esbarrar no teto de ``MAX_FEATURES_GEO``. Async-only.
    """
    workspace, layer = _resolve_deter_layer(bioma)
    cols = DETER_COLUNAS_WFS_GEO_AMZ if bioma == "Amazônia" else DETER_COLUNAS_WFS_GEO_CERRADO
    cql = _build_deter_cql(uf, data_inicio, data_fim)
    base = f"{GEOSERVER_BASE}/{workspace}/ows"

    async for content, url in stream_wfs_paginated(
        base,
        workspace,
        layer,
        STREAM_WFS_VERSION,
        cols,
        page_size,
        source="desmatamento",
        timeout=TIMEOUT,
        cql=cql,
        output_format="application/json",
    ):
        logger.debug("desmatamento_deter_geojson_page", bioma=bioma, size=len(content))
        yield content, url


async def fetch_deter(
    bioma: str,
    uf: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> tuple[bytes, str]:
    content, url = await _fetch_deter_raw(
        bioma, uf, data_inicio, data_fim, output_format="csv", include_geometry=False
    )
    logger.info("desmatamento_deter_csv", source="desmatamento", size=len(content), bioma=bioma)
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
    logger.info("desmatamento_deter_geojson", source="desmatamento", size=len(content), bioma=bioma)
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
