from __future__ import annotations

import json
from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.utils.geo import check_geopandas
from agrobr.utils.io import read_csv_safe

from .models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    MAX_FEATURES_GEO,
    RENAME_MAP,
)

logger = structlog.get_logger()

PARSER_VERSION = 1

_REQUIRED_COLS_RAW = {"cd_quilomb", "no_comunidade", "sg_uf", "nu_area_ha"}


def parse_quilombolas_csv(data: bytes) -> pd.DataFrame:
    df = read_csv_safe(data, source="incra", parser_version=PARSER_VERSION, label="CSV quilombolas")

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    missing = _REQUIRED_COLS_RAW - set(df.columns)
    if missing:
        raise ParseError(
            source="incra",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    df = df.rename(columns=RENAME_MAP)

    df["area_ha"] = pd.to_numeric(df["area_ha"], errors="coerce")
    df["familias"] = pd.to_numeric(df["familias"], errors="coerce").astype("Int64")
    df["data_publicacao"] = pd.to_datetime(df["data_publicacao"], errors="coerce")
    df["data_titulo"] = pd.to_datetime(df["data_titulo"], errors="coerce")

    output_cols = [c for c in COLUNAS_SAIDA if c in df.columns]
    df = df[output_cols].reset_index(drop=True)

    logger.info("incra_quilombolas_parse_ok", records=len(df))
    return df


def parse_quilombolas_geojson(data: bytes) -> Any:
    gpd = check_geopandas()

    try:
        geojson = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ParseError(
            source="incra",
            parser_version=PARSER_VERSION,
            reason=f"Erro ao ler GeoJSON quilombolas: {e}",
        ) from e

    features = geojson.get("features", [])
    if not features:
        empty_gdf = gpd.GeoDataFrame(columns=COLUNAS_SAIDA_GEO)
        empty_gdf = empty_gdf.set_geometry("geometry")
        return empty_gdf

    if len(features) >= MAX_FEATURES_GEO:
        logger.warning(
            "incra_quilombolas_geo_truncated",
            features=len(features),
            max_features=MAX_FEATURES_GEO,
        )

    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

    missing = _REQUIRED_COLS_RAW - set(gdf.columns)
    if missing:
        raise ParseError(
            source="incra",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    gdf = gdf.rename(columns=RENAME_MAP)

    gdf["area_ha"] = pd.to_numeric(gdf["area_ha"], errors="coerce")
    gdf["familias"] = pd.to_numeric(gdf["familias"], errors="coerce").astype("Int64")
    gdf["data_publicacao"] = pd.to_datetime(gdf["data_publicacao"], errors="coerce")
    gdf["data_titulo"] = pd.to_datetime(gdf["data_titulo"], errors="coerce")

    output_cols = [c for c in COLUNAS_SAIDA_GEO if c in gdf.columns]
    gdf = gdf[output_cols].reset_index(drop=True)

    logger.info("incra_quilombolas_geojson_parse_ok", records=len(gdf))
    return gdf
