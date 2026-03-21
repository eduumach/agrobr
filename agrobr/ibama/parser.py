from __future__ import annotations

import json
from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.utils.geo import check_geopandas
from agrobr.utils.io import read_csv_safe

from .models import COLUNAS_SAIDA, COLUNAS_SAIDA_GEO, MAX_FEATURES_GEO, RENAME_MAP

logger = structlog.get_logger()

PARSER_VERSION = 1

_REQUIRED_COLS_RAW = {"numero_tad", "data_tad", "sig_uf", "qtd_area_desmatada"}


def parse_embargos_csv(pages: list[bytes]) -> pd.DataFrame:
    if not pages:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    dfs: list[pd.DataFrame] = []
    for i, data in enumerate(pages):
        df = read_csv_safe(
            data, source="ibama", parser_version=PARSER_VERSION, label=f"CSV pagina {i}"
        )
        if not df.empty:
            dfs.append(df)

    if not dfs:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    df = pd.concat(dfs, ignore_index=True)

    missing = _REQUIRED_COLS_RAW - set(df.columns)
    if missing:
        raise ParseError(
            source="ibama",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    df = df.rename(columns=RENAME_MAP)

    df["data_embargo"] = pd.to_datetime(df["data_embargo"], errors="coerce")
    df["area_desmatada_ha"] = pd.to_numeric(df["area_desmatada_ha"], errors="coerce")
    df["uf"] = df["uf"].fillna("").str.strip().str.upper()
    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].fillna("").str.strip()

    output_cols = [c for c in COLUNAS_SAIDA if c in df.columns]
    df = df[output_cols].reset_index(drop=True)

    logger.info("ibama_embargos_parse_ok", records=len(df))
    return df


def parse_embargos_geojson(data: bytes) -> Any:
    gpd = check_geopandas()

    try:
        geojson = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ParseError(
            source="ibama",
            parser_version=PARSER_VERSION,
            reason=f"Erro ao ler GeoJSON Embargos IBAMA: {e}",
        ) from e

    features = geojson.get("features", [])
    if not features:
        empty = gpd.GeoDataFrame(columns=COLUNAS_SAIDA_GEO)
        empty = empty.set_geometry("geometry")
        return empty

    if len(features) >= MAX_FEATURES_GEO:
        logger.warning(
            "ibama_embargos_geo_truncated",
            features=len(features),
            max_features=MAX_FEATURES_GEO,
        )

    null_geom_count = sum(1 for f in features if f.get("geometry") is None)
    if null_geom_count > 0:
        logger.warning(
            "ibama_embargos_null_geometry",
            null_count=null_geom_count,
            total=len(features),
        )

    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

    missing = _REQUIRED_COLS_RAW - set(gdf.columns)
    if missing:
        raise ParseError(
            source="ibama",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    gdf = gdf.rename(columns=RENAME_MAP)

    gdf["data_embargo"] = pd.to_datetime(gdf["data_embargo"], errors="coerce")
    gdf["area_desmatada_ha"] = pd.to_numeric(gdf["area_desmatada_ha"], errors="coerce")
    gdf["uf"] = gdf["uf"].fillna("").str.strip().str.upper()
    if "municipio" in gdf.columns:
        gdf["municipio"] = gdf["municipio"].fillna("").str.strip()

    output_cols = [c for c in COLUNAS_SAIDA_GEO if c in gdf.columns]
    gdf = gdf[output_cols].reset_index(drop=True)

    logger.info("ibama_embargos_geojson_parse_ok", records=len(gdf))
    return gdf
