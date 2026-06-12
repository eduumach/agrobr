from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.utils.geo import check_geopandas
from agrobr.utils.io import read_csv_safe

from .models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    CSV_COLUMN_MAP,
    GEOM_COLUMN_CSV,
)

logger = structlog.get_logger()

PARSER_VERSION = 2


def _read_embargos(csv_bytes: bytes, columns: list[str]) -> pd.DataFrame:
    return read_csv_safe(
        csv_bytes,
        source="ibama",
        parser_version=PARSER_VERSION,
        sep=";",
        usecols=columns,
        dtype=str,
    )


def _normalize(
    df: pd.DataFrame,
    *,
    uf: str | None,
    bbox: tuple[float, float, float, float] | None,
) -> pd.DataFrame:
    df = df.rename(columns=CSV_COLUMN_MAP)

    df["data_embargo"] = pd.to_datetime(
        df["data_embargo"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    df["data_desembargo"] = pd.to_datetime(
        df["data_desembargo"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    df["area_embargada_ha"] = pd.to_numeric(
        df["area_embargada_ha"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["cancelado"] = df["cancelado"].eq("S")
    df["uf"] = df["uf"].fillna("").str.strip().str.upper()
    df["municipio"] = df["municipio"].fillna("").str.strip()

    if uf is not None:
        df = df[df["uf"] == uf]
    if bbox is not None:
        min_lon, min_lat, max_lon, max_lat = bbox
        df = df[
            df["longitude"].between(min_lon, max_lon) & df["latitude"].between(min_lat, max_lat)
        ]
    return df


def parse_embargos_csv(
    csv_bytes: bytes,
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> pd.DataFrame:
    df = _read_embargos(csv_bytes, list(CSV_COLUMN_MAP))
    df = _normalize(df, uf=uf, bbox=bbox)
    df = df[COLUNAS_SAIDA].reset_index(drop=True)
    logger.info("ibama_embargos_parse_ok", records=len(df))
    return df


def parse_embargos_geo(
    csv_bytes: bytes,
    *,
    uf: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> Any:
    """Filtra antes de carregar WKT: sem `uf`/`bbox`, parseia as geometrias do
    Brasil inteiro — dezenas de milhares de polígonos, lento e pesado."""
    gpd = check_geopandas()
    from shapely import wkt

    if uf is None and bbox is None:
        logger.warning(
            "ibama_embargos_geo_sem_filtro",
            hint="Sem uf/bbox o parse de WKT cobre o Brasil inteiro (lento)",
        )

    df = _read_embargos(csv_bytes, [*CSV_COLUMN_MAP, GEOM_COLUMN_CSV])
    df = _normalize(df, uf=uf, bbox=bbox)
    df = df[df[GEOM_COLUMN_CSV].notna()].reset_index(drop=True)

    if df.empty:
        return gpd.GeoDataFrame(columns=COLUNAS_SAIDA_GEO, geometry="geometry", crs="EPSG:4326")

    def _load_wkt(raw: str) -> Any:
        try:
            return wkt.loads(raw)
        except Exception:
            return None

    geoms = df[GEOM_COLUMN_CSV].map(_load_wkt)
    invalid = int(geoms.isna().sum())
    if invalid:
        logger.warning("ibama_embargos_geo_wkt_invalido", descartados=invalid)

    mask = geoms.notna()
    gdf = gpd.GeoDataFrame(
        df.loc[mask, COLUNAS_SAIDA].reset_index(drop=True),
        geometry=geoms[mask].reset_index(drop=True),
        crs="EPSG:4326",
    )
    logger.info("ibama_embargos_geo_parse_ok", records=len(gdf))
    return gdf
