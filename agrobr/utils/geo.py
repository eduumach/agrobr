from __future__ import annotations

import json
import re
from typing import Any, Literal
from urllib.parse import quote

import httpx
import structlog

from agrobr.constants import MIN_WFS_SIZE
from agrobr.exceptions import ParseError, SourceUnavailableError
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


def build_wfs_url(
    base: str,
    namespace: str,
    layer: str,
    version: str,
    property_names: list[str],
    *,
    max_features: int,
    output_format: str = "csv",
    cql_filter: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    bbox_crs: str = "EPSG:4674",
    start_index: int | None = None,
    result_type: str | None = None,
) -> str:
    props = ",".join(property_names)
    is_v2 = version.startswith("2.")
    type_key = "typeNames" if is_v2 else "typeName"
    count_key = "count" if is_v2 else "maxFeatures"

    url = (
        f"{base}"
        f"?service=WFS&version={version}&request=GetFeature"
        f"&{type_key}={namespace}:{layer}"
        f"&outputFormat={quote(output_format)}"
        f"&propertyName={props}"
        f"&{count_key}={max_features}"
    )
    if start_index is not None:
        url += f"&startIndex={start_index}"
    if result_type is not None:
        url += f"&resultType={result_type}"
    if cql_filter:
        url += f"&CQL_FILTER={quote(cql_filter)}"
    if bbox is not None:
        minlon, minlat, maxlon, maxlat = bbox
        url += f"&BBOX={minlon},{minlat},{maxlon},{maxlat},{bbox_crs}"
    return url


async def fetch_wfs(
    url: str,
    *,
    source: str,
    timeout: httpx.Timeout,
    base_delay: float | None = None,
    client: httpx.AsyncClient | None = None,
) -> bytes:
    async def _do_fetch(http: httpx.AsyncClient) -> bytes:
        logger.debug(f"{source}_request", url=url)
        response = await retry_on_status(
            lambda: http.get(url),
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

    if client is not None:
        return await _do_fetch(client)

    async with httpx.AsyncClient(
        timeout=timeout, headers=UserAgentRotator.get_bot_headers(), follow_redirects=True
    ) as auto_client:
        return await _do_fetch(auto_client)


def parse_geojson_base(
    data: bytes,
    gpd: Any,
    *,
    source: str,
    parser_version: int,
    required_cols: set[str],
    max_features: int,
    output_cols_empty: list[str],
    truncation_event: str,
    on_empty: Literal["empty", "raise"] = "empty",
    warn_null_geom: bool = False,
    crs: str = "EPSG:4326",
) -> Any:
    try:
        geojson = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ParseError(
            source=source,
            parser_version=parser_version,
            reason=f"Erro ao ler GeoJSON {source}: {e}",
        ) from e

    features = geojson.get("features", [])
    if not features:
        if on_empty == "raise":
            raise ParseError(
                source=source,
                parser_version=parser_version,
                reason="GeoJSON sem features",
            )
        empty = gpd.GeoDataFrame(columns=output_cols_empty)
        empty = empty.set_geometry("geometry")
        return empty

    if len(features) >= max_features:
        logger.warning(
            truncation_event,
            features=len(features),
            max_features=max_features,
        )

    if warn_null_geom:
        null_geom_count = sum(1 for f in features if f.get("geometry") is None)
        if null_geom_count > 0:
            logger.warning(
                f"{source}_null_geometry",
                null_count=null_geom_count,
                total=len(features),
            )

    gdf = gpd.GeoDataFrame.from_features(features, crs=crs)

    missing = required_cols - set(gdf.columns)
    if missing:
        raise ParseError(
            source=source,
            parser_version=parser_version,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    return gdf


def parse_wfs_hits(content: bytes, *, source: str) -> int:
    text = content.decode("utf-8", errors="replace")
    match = re.search(r'numberMatched="(\d+)"', text)
    if match:
        return int(match.group(1))
    match = re.search(r"numberMatched=(\d+)", text)
    if match:
        return int(match.group(1))
    raise ParseError(
        source=source,
        parser_version=1,
        reason=f"Nao encontrou numberMatched na resposta hits: {text[:200]}",
    )
