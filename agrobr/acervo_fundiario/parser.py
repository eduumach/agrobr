from __future__ import annotations

from typing import Any

import pandas as pd
import structlog
from lxml import etree

from agrobr.exceptions import ParseError
from agrobr.utils.geo import check_geopandas

from .models import (
    ASSENTAMENTOS_COLUNAS_SAIDA,
    ASSENTAMENTOS_COLUNAS_SAIDA_GEO,
    ASSENTAMENTOS_DATE_COLS,
    ASSENTAMENTOS_NUMERIC_COLS,
    ASSENTAMENTOS_PROPERTY_NAMES,
    ASSENTAMENTOS_RENAME_MAP,
    ASSENTAMENTOS_REQUIRED_COLS,
    MAX_FEATURES_ASSENTAMENTOS,
    MAX_FEATURES_SIGEF,
    MAX_FEATURES_SNCI,
    NS_GML,
    NS_MS,
    SIGEF_COLUNAS_SAIDA,
    SIGEF_COLUNAS_SAIDA_GEO,
    SIGEF_DATE_COLS,
    SIGEF_PROPERTY_NAMES,
    SIGEF_RENAME_MAP,
    SIGEF_REQUIRED_COLS,
    SNCI_COLUNAS_SAIDA,
    SNCI_COLUNAS_SAIDA_GEO,
    SNCI_DATE_COLS,
    SNCI_NUMERIC_COLS,
    SNCI_PROPERTY_NAMES,
    SNCI_RENAME_MAP,
    SNCI_REQUIRED_COLS,
)

logger = structlog.get_logger()

PARSER_VERSION = 1


def _extract_gml2_features(
    data: bytes,
    property_names: list[str],
) -> list[dict[str, str | None]]:
    root = etree.fromstring(data)  # noqa: S320
    records: list[dict[str, str | None]] = []
    for member in root.iter(f"{{{NS_GML}}}featureMember"):
        feature = member[0]
        record: dict[str, str | None] = {}
        for prop in property_names:
            el = feature.find(f"{{{NS_MS}}}{prop}")
            if el is not None:
                record[prop] = el.text
        records.append(record)
    return records


def _apply_types(
    df: pd.DataFrame,
    rename_map: dict[str, str],
    numeric_cols: frozenset[str],
    date_cols: list[str],
    date_format: str,
    colunas_saida: list[str],
) -> pd.DataFrame:
    df = df.rename(columns=rename_map)

    renamed_numeric = {rename_map.get(c, c) for c in numeric_cols}
    for col in renamed_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    renamed_dates = [rename_map.get(c, c) for c in date_cols]
    for col in renamed_dates:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.split(" ").str[0]
            df[col] = pd.to_datetime(df[col], format=date_format, errors="coerce")

    output_cols = [c for c in colunas_saida if c in df.columns]
    return df[output_cols].reset_index(drop=True)


def _parse_tabular(
    data: bytes,
    *,
    property_names: list[str],
    required_cols: frozenset[str],
    rename_map: dict[str, str],
    numeric_cols: frozenset[str],
    date_cols: list[str],
    date_format: str,
    colunas_saida: list[str],
    max_features: int,
    label: str,
) -> pd.DataFrame:
    records = _extract_gml2_features(data, property_names)

    if not records:
        return pd.DataFrame(columns=colunas_saida)

    if len(records) >= max_features:
        logger.warning(
            "acervo_fundiario_truncated",
            records=len(records),
            max_features=max_features,
            tipo=label,
        )

    df = pd.DataFrame(records)

    present = set(df.columns)
    missing = required_cols - present
    if missing:
        raise ParseError(
            source="acervo_fundiario",
            parser_version=PARSER_VERSION,
            reason=f"Colunas obrigatorias ausentes em {label}: {missing}",
        )

    df = _apply_types(df, rename_map, numeric_cols, date_cols, date_format, colunas_saida)
    logger.info(f"acervo_fundiario_{label}_parse_ok", records=len(df))
    return df


def _parse_gml_coords(coord_text: str) -> list[tuple[float, float]]:
    pairs = coord_text.strip().split(" ")
    coords = []
    for pair in pairs:
        parts = pair.split(",")
        if len(parts) >= 2:
            coords.append((float(parts[0]), float(parts[1])))
    return coords


def _extract_geometry(feature_elem: Any) -> Any:
    from shapely.geometry import MultiPolygon, Polygon

    geom_el = feature_elem.find(f"{{{NS_MS}}}msGeometry")
    if geom_el is None:
        return None

    polygon_els = geom_el.findall(f".//{{{NS_GML}}}Polygon")
    if not polygon_els:
        return None

    polygons = []
    for poly_el in polygon_els:
        outer_el = poly_el.find(f".//{{{NS_GML}}}outerBoundaryIs//{{{NS_GML}}}coordinates")
        if outer_el is None or outer_el.text is None:
            continue
        exterior = _parse_gml_coords(outer_el.text)
        if len(exterior) < 3:
            continue

        holes = []
        for inner_el in poly_el.findall(f".//{{{NS_GML}}}innerBoundaryIs//{{{NS_GML}}}coordinates"):
            if inner_el.text:
                hole = _parse_gml_coords(inner_el.text)
                if len(hole) >= 3:
                    holes.append(hole)

        polygons.append(Polygon(exterior, holes) if holes else Polygon(exterior))

    if not polygons:
        return None
    if len(polygons) == 1:
        return polygons[0]
    return MultiPolygon(polygons)


def _parse_geo(
    data: bytes,
    *,
    property_names: list[str],
    rename_map: dict[str, str],
    numeric_cols: frozenset[str],
    date_cols: list[str],
    date_format: str,
    colunas_saida_geo: list[str],
    label: str,
) -> Any:
    gpd = check_geopandas()
    root = etree.fromstring(data)  # noqa: S320

    records: list[dict[str, Any]] = []
    for member in root.iter(f"{{{NS_GML}}}featureMember"):
        feature = member[0]
        record: dict[str, Any] = {}
        for prop in property_names:
            el = feature.find(f"{{{NS_MS}}}{prop}")
            if el is not None:
                record[prop] = el.text
        record["geometry"] = _extract_geometry(feature)
        records.append(record)

    if not records:
        return gpd.GeoDataFrame(columns=colunas_saida_geo)

    df = pd.DataFrame(records)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    gdf = _apply_types(gdf, rename_map, numeric_cols, date_cols, date_format, colunas_saida_geo)
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")
    logger.info(f"acervo_fundiario_{label}_geo_parse_ok", records=len(gdf))
    return gdf


# ---------------------------------------------------------------------------
# Public parsers — tabular
# ---------------------------------------------------------------------------


def parse_sigef_gml(data: bytes) -> pd.DataFrame:
    return _parse_tabular(
        data,
        property_names=SIGEF_PROPERTY_NAMES,
        required_cols=SIGEF_REQUIRED_COLS,
        rename_map=SIGEF_RENAME_MAP,
        numeric_cols=frozenset(),
        date_cols=SIGEF_DATE_COLS,
        date_format="%Y-%m-%d",
        colunas_saida=SIGEF_COLUNAS_SAIDA,
        max_features=MAX_FEATURES_SIGEF,
        label="sigef",
    )


def parse_snci_gml(data: bytes) -> pd.DataFrame:
    return _parse_tabular(
        data,
        property_names=SNCI_PROPERTY_NAMES,
        required_cols=SNCI_REQUIRED_COLS,
        rename_map=SNCI_RENAME_MAP,
        numeric_cols=SNCI_NUMERIC_COLS,
        date_cols=SNCI_DATE_COLS,
        date_format="%Y-%m-%d",
        colunas_saida=SNCI_COLUNAS_SAIDA,
        max_features=MAX_FEATURES_SNCI,
        label="snci",
    )


def parse_assentamentos_gml(data: bytes) -> pd.DataFrame:
    return _parse_tabular(
        data,
        property_names=ASSENTAMENTOS_PROPERTY_NAMES,
        required_cols=ASSENTAMENTOS_REQUIRED_COLS,
        rename_map=ASSENTAMENTOS_RENAME_MAP,
        numeric_cols=ASSENTAMENTOS_NUMERIC_COLS,
        date_cols=ASSENTAMENTOS_DATE_COLS,
        date_format="%d/%m/%Y",
        colunas_saida=ASSENTAMENTOS_COLUNAS_SAIDA,
        max_features=MAX_FEATURES_ASSENTAMENTOS,
        label="assentamentos",
    )


# ---------------------------------------------------------------------------
# Public parsers — geo
# ---------------------------------------------------------------------------


def parse_sigef_geo(data: bytes) -> Any:
    return _parse_geo(
        data,
        property_names=SIGEF_PROPERTY_NAMES,
        rename_map=SIGEF_RENAME_MAP,
        numeric_cols=frozenset(),
        date_cols=SIGEF_DATE_COLS,
        date_format="%Y-%m-%d",
        colunas_saida_geo=SIGEF_COLUNAS_SAIDA_GEO,
        label="sigef",
    )


def parse_snci_geo(data: bytes) -> Any:
    return _parse_geo(
        data,
        property_names=SNCI_PROPERTY_NAMES,
        rename_map=SNCI_RENAME_MAP,
        numeric_cols=SNCI_NUMERIC_COLS,
        date_cols=SNCI_DATE_COLS,
        date_format="%Y-%m-%d",
        colunas_saida_geo=SNCI_COLUNAS_SAIDA_GEO,
        label="snci",
    )


def parse_assentamentos_geo(data: bytes) -> Any:
    return _parse_geo(
        data,
        property_names=ASSENTAMENTOS_PROPERTY_NAMES,
        rename_map=ASSENTAMENTOS_RENAME_MAP,
        numeric_cols=ASSENTAMENTOS_NUMERIC_COLS,
        date_cols=ASSENTAMENTOS_DATE_COLS,
        date_format="%d/%m/%Y",
        colunas_saida_geo=ASSENTAMENTOS_COLUNAS_SAIDA_GEO,
        label="assentamentos",
    )
