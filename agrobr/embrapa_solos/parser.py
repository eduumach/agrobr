from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.utils.geo import check_geopandas, parse_geojson_base
from agrobr.utils.io import concat_csv_pages

from .models import (
    _REQUIRED_MAPA,
    _REQUIRED_PERFIS,
    MAPA_COLUNAS_SAIDA,
    MAPA_COLUNAS_SAIDA_GEO,
    MAPA_MAX_FEATURES_GEO,
    MAPA_RENAME_MAP,
    PERFIS_COLUNAS_SAIDA,
    PERFIS_COLUNAS_SAIDA_GEO,
    PERFIS_MAX_FEATURES_GEO,
    PERFIS_NUMERIC_COLS,
    PERFIS_RENAME_MAP,
)

logger = structlog.get_logger()

PARSER_VERSION = 1


def parse_perfis_csv(pages: list[bytes]) -> pd.DataFrame:
    df = concat_csv_pages(
        pages,
        source="embrapa_solos",
        parser_version=PARSER_VERSION,
        empty_columns=PERFIS_COLUNAS_SAIDA,
    )
    if df.empty:
        return df

    missing = _REQUIRED_PERFIS - set(df.columns)
    if missing:
        raise ParseError(
            source="embrapa_solos",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatórias ausentes (perfis): {missing}",
        )

    df = df.rename(columns=PERFIS_RENAME_MAP)

    for col in PERFIS_NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "uf" in df.columns:
        df["uf"] = df["uf"].fillna("").str.strip().str.upper()

    cols = [c for c in PERFIS_COLUNAS_SAIDA if c in df.columns]
    df = df[cols].reset_index(drop=True)

    logger.info("embrapa_solos_perfis_parse_ok", records=len(df))
    return df


def parse_perfis_geojson(data: bytes) -> Any:
    gpd = check_geopandas()
    gdf = parse_geojson_base(
        data,
        gpd,
        source="embrapa_solos",
        parser_version=PARSER_VERSION,
        required_cols=_REQUIRED_PERFIS,
        max_features=PERFIS_MAX_FEATURES_GEO,
        output_cols_empty=PERFIS_COLUNAS_SAIDA_GEO,
        truncation_event="embrapa_solos_perfis_geo_truncated",
    )
    if gdf.empty:
        return gdf

    gdf = gdf.rename(columns=PERFIS_RENAME_MAP)
    for col in PERFIS_NUMERIC_COLS:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors="coerce")
    if "uf" in gdf.columns:
        gdf["uf"] = gdf["uf"].fillna("").str.strip().str.upper()

    cols = [c for c in PERFIS_COLUNAS_SAIDA_GEO if c in gdf.columns]
    return gdf[cols].reset_index(drop=True)


def parse_mapa_csv(pages: list[bytes]) -> pd.DataFrame:
    df = concat_csv_pages(
        pages,
        source="embrapa_solos",
        parser_version=PARSER_VERSION,
        empty_columns=MAPA_COLUNAS_SAIDA,
    )
    if df.empty:
        return df

    missing = _REQUIRED_MAPA - set(df.columns)
    if missing:
        raise ParseError(
            source="embrapa_solos",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatórias ausentes (mapa): {missing}",
        )

    df = df.rename(columns=MAPA_RENAME_MAP)

    if "area_km2" in df.columns:
        df["area_km2"] = pd.to_numeric(df["area_km2"], errors="coerce")

    cols = [c for c in MAPA_COLUNAS_SAIDA if c in df.columns]
    df = df[cols].reset_index(drop=True)

    logger.info("embrapa_solos_mapa_parse_ok", records=len(df))
    return df


def parse_mapa_geojson(data: bytes) -> Any:
    gpd = check_geopandas()
    gdf = parse_geojson_base(
        data,
        gpd,
        source="embrapa_solos",
        parser_version=PARSER_VERSION,
        required_cols=_REQUIRED_MAPA,
        max_features=MAPA_MAX_FEATURES_GEO,
        output_cols_empty=MAPA_COLUNAS_SAIDA_GEO,
        truncation_event="embrapa_solos_mapa_geo_truncated",
    )
    if gdf.empty:
        return gdf

    gdf = gdf.rename(columns=MAPA_RENAME_MAP)
    if "area_km2" in gdf.columns:
        gdf["area_km2"] = pd.to_numeric(gdf["area_km2"], errors="coerce")

    cols = [c for c in MAPA_COLUNAS_SAIDA_GEO if c in gdf.columns]
    return gdf[cols].reset_index(drop=True)
