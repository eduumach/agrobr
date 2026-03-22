from __future__ import annotations

from typing import Any

import pandas as pd

from agrobr.utils.geo import parse_arcgis_geojson, parse_arcgis_tabular

from .models import LAYERS

PARSER_VERSION = 1

_NUMERIC_COLS = frozenset(
    {
        "comprimento_m",
        "area_m2",
        "nivel_otto",
        "area_ha",
        "ano_mapeamento",
        "lat",
        "lon",
        "demanda_m3_s",
        "demanda_m3_ano",
        "q95_l_s",
        "qmlt_l_s",
    }
)


def parse_layer_tabular(pages: list[bytes], *, layer_key: str) -> pd.DataFrame:
    return parse_arcgis_tabular(
        pages,
        source="ana",
        layer_config=LAYERS[layer_key],
        parser_version=PARSER_VERSION,
        numeric_cols=_NUMERIC_COLS,
    )


def parse_layer_geojson(pages: list[bytes], *, layer_key: str) -> Any:
    return parse_arcgis_geojson(
        pages,
        source="ana",
        layer_config=LAYERS[layer_key],
        parser_version=PARSER_VERSION,
        numeric_cols=_NUMERIC_COLS,
    )
