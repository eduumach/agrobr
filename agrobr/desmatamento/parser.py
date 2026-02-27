from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError

from .models import (
    COLUNAS_SAIDA_DETER,
    COLUNAS_SAIDA_DETER_GEO,
    COLUNAS_SAIDA_PRODES,
    MAX_FEATURES_GEO,
    estado_para_uf,
)

logger = structlog.get_logger()

PARSER_VERSION = 1


def parse_prodes_csv(data: bytes, bioma: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(data), encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(data), encoding="latin-1")
    except Exception as e:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason=f"Erro ao ler CSV PRODES: {e}",
        ) from e

    if df.empty:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason="CSV PRODES vazio",
        )

    required = {"year", "area_km", "state"}
    missing = required - set(df.columns)
    if missing:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    df["ano"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["area_km2"] = pd.to_numeric(df["area_km"], errors="coerce")
    df["uf"] = df["state"].fillna("").apply(estado_para_uf)
    df["classe"] = df.get("main_class", pd.Series(dtype=str)).fillna("desmatamento")
    df["satelite"] = df.get("satellite", pd.Series(dtype=str)).fillna("")
    df["sensor"] = df.get("sensor", pd.Series(dtype=str)).fillna("")
    df["bioma"] = bioma

    output_cols = [c for c in COLUNAS_SAIDA_PRODES if c in df.columns]
    df = df[output_cols].copy()
    df = df.reset_index(drop=True)

    logger.info("desmatamento_prodes_parse_ok", records=len(df), bioma=bioma)
    return df


def parse_deter_csv(data: bytes, bioma: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(data), encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(data), encoding="latin-1")
    except Exception as e:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason=f"Erro ao ler CSV DETER: {e}",
        ) from e

    if df.empty:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason="CSV DETER vazio",
        )

    required = {"view_date", "areamunkm", "uf"}
    missing = required - set(df.columns)
    if missing:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    df["data"] = pd.to_datetime(df["view_date"], errors="coerce").dt.date
    df["area_km2"] = pd.to_numeric(df["areamunkm"], errors="coerce")
    df["classe"] = df.get("classname", pd.Series(dtype=str)).fillna("")
    df["uf"] = df["uf"].fillna("").str.upper()
    df["municipio"] = df.get("municipality", pd.Series(dtype=str)).fillna("")
    df["municipio_id"] = pd.to_numeric(
        df.get("mun_geocod", pd.Series(dtype=str)), errors="coerce"
    ).astype("Int64")
    df["satelite"] = df.get("satellite", pd.Series(dtype=str)).fillna("")
    df["sensor"] = df.get("sensor", pd.Series(dtype=str)).fillna("")
    df["bioma"] = bioma

    output_cols = [c for c in COLUNAS_SAIDA_DETER if c in df.columns]
    df = df[output_cols].copy()
    df = df.reset_index(drop=True)

    logger.info("desmatamento_deter_parse_ok", records=len(df), bioma=bioma)
    return df


def _check_geopandas() -> Any:
    try:
        import geopandas

        return geopandas
    except ImportError:
        raise ImportError(
            "geopandas is required for deter_geo(). Install with: pip install agrobr[geo]"
        ) from None


def parse_deter_geojson(data: bytes, bioma: str) -> Any:
    gpd = _check_geopandas()

    try:
        geojson = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason=f"Erro ao ler GeoJSON DETER: {e}",
        ) from e

    features = geojson.get("features", [])
    if not features:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason="GeoJSON DETER vazio",
        )

    if len(features) >= MAX_FEATURES_GEO:
        logger.warning(
            "desmatamento_deter_geo_truncated",
            features=len(features),
            max_features=MAX_FEATURES_GEO,
            bioma=bioma,
        )

    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

    required = {"view_date", "areamunkm", "uf"}
    missing = required - set(gdf.columns)
    if missing:
        raise ParseError(
            source="desmatamento",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes: {missing}",
        )

    gdf["data"] = pd.to_datetime(gdf["view_date"], errors="coerce").dt.date
    gdf["area_km2"] = pd.to_numeric(gdf["areamunkm"], errors="coerce")
    gdf["classe"] = gdf.get("classname", pd.Series(dtype=str)).fillna("")
    gdf["uf"] = gdf["uf"].fillna("").str.upper()
    gdf["municipio"] = gdf.get("municipality", pd.Series(dtype=str)).fillna("")
    gdf["municipio_id"] = pd.to_numeric(
        gdf.get("mun_geocod", pd.Series(dtype=str)), errors="coerce"
    ).astype("Int64")
    gdf["satelite"] = gdf.get("satellite", pd.Series(dtype=str)).fillna("")
    gdf["sensor"] = gdf.get("sensor", pd.Series(dtype=str)).fillna("")
    gdf["bioma"] = bioma

    output_cols = [c for c in COLUNAS_SAIDA_DETER_GEO if c in gdf.columns]
    gdf = gdf[output_cols].copy()
    gdf = gdf.reset_index(drop=True)

    logger.info("desmatamento_deter_geojson_parse_ok", records=len(gdf), bioma=bioma)
    return gdf
