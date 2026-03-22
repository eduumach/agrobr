from __future__ import annotations

from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.utils.geo import check_geopandas, parse_geojson_base
from agrobr.utils.io import read_csv_safe

from .models import (
    COLUNAS_SAIDA,
    COLUNAS_SAIDA_GEO,
    MAX_FEATURES_GEO,
    RENAME_MAP,
)

logger = structlog.get_logger()

PARSER_VERSION = 1

_REQUIRED_COLS_RAW = {"terrai_codigo", "terrai_nome", "uf_sigla", "superficie_perimetro_ha"}


def parse_terras_indigenas_csv(data: bytes) -> pd.DataFrame:
    df = read_csv_safe(
        data, source="funai", parser_version=PARSER_VERSION, label="CSV Terras Indigenas"
    )

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    missing = _REQUIRED_COLS_RAW - set(df.columns)
    if missing:
        raise ParseError(
            source="funai",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    df = df.rename(columns=RENAME_MAP)

    df["area_ha"] = pd.to_numeric(df["area_ha"], errors="coerce")
    df["uf"] = df["uf"].fillna("").str.strip().str.upper()
    df["data_atualizacao"] = pd.to_datetime(df["data_atualizacao"], errors="coerce")

    output_cols = [c for c in COLUNAS_SAIDA if c in df.columns]
    df = df[output_cols].reset_index(drop=True)

    logger.info("funai_terras_indigenas_parse_ok", records=len(df))
    return df


def parse_terras_indigenas_geojson(data: bytes) -> Any:
    gpd = check_geopandas()
    gdf = parse_geojson_base(
        data,
        gpd,
        source="funai",
        parser_version=PARSER_VERSION,
        required_cols=_REQUIRED_COLS_RAW,
        max_features=MAX_FEATURES_GEO,
        output_cols_empty=COLUNAS_SAIDA_GEO,
        truncation_event="funai_terras_indigenas_geo_truncated",
    )
    if gdf.empty:
        return gdf

    gdf = gdf.rename(columns=RENAME_MAP)
    gdf["area_ha"] = pd.to_numeric(gdf["area_ha"], errors="coerce")
    gdf["uf"] = gdf["uf"].fillna("").str.strip().str.upper()
    gdf["data_atualizacao"] = pd.to_datetime(gdf["data_atualizacao"], errors="coerce")

    output_cols = [c for c in COLUNAS_SAIDA_GEO if c in gdf.columns]
    return gdf[output_cols].reset_index(drop=True)
