from __future__ import annotations

import io

import pandas as pd

from agrobr.exceptions import ParseError

from .models import (
    AUTORIZACOES_COLS,
    FORMULADOS_COLS_DROP,
    FORMULADOS_PRODUCT_COLS,
    FORMULADOS_RENAME,
    TECNICOS_COLS,
    TECNICOS_COLS_DROP,
    TECNICOS_RENAME,
)

PARSER_VERSION = 1

_REQUIRED_FORMULADOS = {"NR_REGISTRO", "MARCA_COMERCIAL", "INGREDIENTE_ATIVO", "CULTURA"}
_REQUIRED_TECNICOS = {"NR_REGISTRO", "MARCA_COMERCIAL", "INGREDIENTE_ATIVO"}

_EN_DASH_UTF8 = "\u2013".encode()


def _fix_encoding(raw: bytes) -> io.BytesIO:
    return io.BytesIO(raw.replace(b"\x96", _EN_DASH_UTF8))


def _strip_all_str_cols(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


def parse_formulados_csv(data: bytes) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not data.strip():
        raise ParseError(
            source="defensivos",
            parser_version=PARSER_VERSION,
            reason="CSV formulados vazio",
        )

    df = pd.read_csv(
        _fix_encoding(data),
        sep=";",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        encoding_errors="replace",
    )

    missing = _REQUIRED_FORMULADOS - set(df.columns)
    if missing:
        raise ParseError(
            source="defensivos",
            parser_version=PARSER_VERSION,
            reason=f"Colunas faltando no CSV formulados: {sorted(missing)}",
        )

    drop_cols = [c for c in FORMULADOS_COLS_DROP if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    rename_map = {k: v for k, v in FORMULADOS_RENAME.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    df = _strip_all_str_cols(df)
    df = df.replace("", pd.NA)

    product_cols = [c for c in FORMULADOS_PRODUCT_COLS if c in df.columns]
    product_df = df[product_cols].drop_duplicates(subset="nr_registro", keep="first")
    product_df = product_df.reset_index(drop=True)

    auth_cols = [c for c in AUTORIZACOES_COLS if c in df.columns]
    auth_df = df[auth_cols].reset_index(drop=True)

    return product_df, auth_df


def parse_tecnicos_csv(data: bytes) -> pd.DataFrame:
    if not data.strip():
        raise ParseError(
            source="defensivos",
            parser_version=PARSER_VERSION,
            reason="CSV tecnicos vazio",
        )

    df = pd.read_csv(
        _fix_encoding(data),
        sep=";",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        encoding_errors="replace",
    )

    missing = _REQUIRED_TECNICOS - set(df.columns)
    if missing:
        raise ParseError(
            source="defensivos",
            parser_version=PARSER_VERSION,
            reason=f"Colunas faltando no CSV tecnicos: {sorted(missing)}",
        )

    drop_cols = [c for c in TECNICOS_COLS_DROP if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    rename_map = {k: v for k, v in TECNICOS_RENAME.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    df = _strip_all_str_cols(df)
    df = df.replace("", pd.NA)

    out_cols = [c for c in TECNICOS_COLS if c in df.columns]
    return df[out_cols].reset_index(drop=True)
