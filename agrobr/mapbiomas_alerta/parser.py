from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.utils.geo import check_geopandas

from .models import COLUNAS_SAIDA, COLUNAS_SAIDA_GEO, RENAME_MAP

logger = structlog.get_logger()

PARSER_VERSION = 2

_REQUIRED_FIELDS = {"alertCode", "areaHa", "detectedAt"}


def _flatten_sources(sources: Any) -> str:
    if not sources or not isinstance(sources, list):
        return ""
    names = [s.get("name", "") for s in sources if isinstance(s, dict)]
    return ", ".join(n for n in names if n)


def _normalize_records(
    records: list[dict[str, object]],
) -> tuple[pd.DataFrame, list[Any]]:
    if not records:
        return pd.DataFrame(columns=COLUNAS_SAIDA), []

    rows: list[dict[str, object]] = []
    geometries: list[Any] = []
    for rec in records:
        row = dict(rec)
        raw_coords = row.pop("coordenates", None)
        coords = raw_coords if isinstance(raw_coords, dict) else {}
        row["lat"] = coords.get("latitude")
        row["lon"] = coords.get("longitude")

        raw_sources = row.pop("sources", None)
        row["fonte"] = _flatten_sources(raw_sources)

        geometries.append(row.pop("geometryWkt", None))
        rows.append(row)

    df = pd.DataFrame(rows)

    missing = _REQUIRED_FIELDS - set(df.columns)
    if missing:
        raise ParseError(
            source="mapbiomas_alerta",
            parser_version=PARSER_VERSION,
            reason=f"Campos obrigatorios ausentes: {missing}",
        )

    df = df.rename(columns=RENAME_MAP)
    df["data_deteccao"] = pd.to_datetime(df["data_deteccao"], errors="coerce")
    df["data_publicacao"] = pd.to_datetime(df["data_publicacao"], errors="coerce")
    df["area_ha"] = pd.to_numeric(df["area_ha"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    return df, geometries


def parse_alertas(records: list[dict[str, object]]) -> pd.DataFrame:
    df, _ = _normalize_records(records)
    if df.empty:
        return df
    output_cols = [c for c in COLUNAS_SAIDA if c in df.columns]
    df = df[output_cols].reset_index(drop=True)
    logger.info("mapbiomas_alerta_parse_ok", records=len(df))
    return df


def parse_alertas_geo(records: list[dict[str, object]]) -> Any:
    gpd = check_geopandas()
    df, wkt_strings = _normalize_records(records)
    if df.empty:
        empty = gpd.GeoDataFrame(columns=COLUNAS_SAIDA_GEO)
        empty = empty.set_geometry("geometry")
        return empty

    from shapely import wkt
    from shapely.errors import GEOSException

    geoms: list[Any] = []
    for wkt_str in wkt_strings:
        geom = None
        if wkt_str:
            try:
                geom = wkt.loads(wkt_str)
            except (GEOSException, ValueError):
                logger.warning("mapbiomas_alerta_invalid_wkt")
        geoms.append(geom)

    gdf = gpd.GeoDataFrame(df, geometry=geoms, crs="EPSG:4326")
    null_geom = gdf.geometry.isna().sum()
    if null_geom:
        logger.warning("mapbiomas_alerta_null_geometry", null_count=int(null_geom), total=len(gdf))

    output_cols = [c for c in COLUNAS_SAIDA_GEO if c in gdf.columns]
    return gdf[output_cols].reset_index(drop=True)
