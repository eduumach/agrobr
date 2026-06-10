from __future__ import annotations

import io
from typing import Any, Literal

import pandas as pd
import structlog

from agrobr.exceptions import ParseError

_ExcelEngine = Literal["xlrd", "openpyxl", "odf", "pyxlsb", "calamine"]

logger = structlog.get_logger()


def _extract_bytes(data: bytes | io.BytesIO) -> bytes:
    if isinstance(data, io.BytesIO):
        return data.getvalue()
    return data


def open_excel_safe(
    data: bytes | io.BytesIO,
    *,
    source: str,
    parser_version: int = 1,
    engine: _ExcelEngine | None = None,
) -> pd.ExcelFile:
    raw = _extract_bytes(data)
    try:
        return pd.ExcelFile(io.BytesIO(raw), engine=engine)
    except Exception as primary_err:
        if engine == "xlrd":
            raise ParseError(
                source=source,
                parser_version=parser_version,
                reason=f"Erro ao abrir Excel (xlrd): {primary_err}",
            ) from primary_err

        logger.warning(
            "xlsx_calamine_fallback",
            source=source,
            primary_error=str(primary_err),
        )
        try:
            return pd.ExcelFile(io.BytesIO(raw), engine="calamine")
        except Exception as fallback_err:
            raise ParseError(
                source=source,
                parser_version=parser_version,
                reason=f"Erro ao abrir Excel (primary: {primary_err}, calamine: {fallback_err})",
            ) from fallback_err


def read_excel_safe(
    data: bytes | io.BytesIO,
    *,
    source: str,
    parser_version: int = 1,
    label: str = "Excel",
    **kwargs: Any,
) -> pd.DataFrame:
    raw = _extract_bytes(data)
    try:
        df: pd.DataFrame = pd.read_excel(io.BytesIO(raw), **kwargs)
        return df
    except Exception as primary_err:
        if kwargs.get("engine") == "xlrd":
            raise ParseError(
                source=source,
                parser_version=parser_version,
                reason=f"Erro ao ler {label} (xlrd): {primary_err}",
            ) from primary_err

        logger.warning(
            "xlsx_calamine_fallback",
            source=source,
            label=label,
            primary_error=str(primary_err),
        )
        calamine_kwargs = {**kwargs, "engine": "calamine"}
        try:
            df = pd.read_excel(io.BytesIO(raw), **calamine_kwargs)
            return df
        except Exception as fallback_err:
            raise ParseError(
                source=source,
                parser_version=parser_version,
                reason=f"Erro ao ler {label} (primary: {primary_err}, calamine: {fallback_err})",
            ) from fallback_err


def read_csv_safe(
    data: bytes,
    *,
    source: str,
    parser_version: int = 1,
    label: str = "CSV",
    **kwargs: Any,
) -> pd.DataFrame:
    try:
        df: pd.DataFrame = pd.read_csv(io.BytesIO(data), encoding="utf-8", **kwargs)
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(io.BytesIO(data), encoding="latin-1", **kwargs)
            return df
        except Exception as e:
            raise ParseError(
                source=source,
                parser_version=parser_version,
                reason=f"Erro ao ler {label} (latin-1): {e}",
            ) from e
    except Exception as e:
        raise ParseError(
            source=source,
            parser_version=parser_version,
            reason=f"Erro ao ler {label}: {e}",
        ) from e


def concat_csv_pages(
    pages: list[bytes],
    *,
    source: str,
    parser_version: int,
    empty_columns: list[str],
) -> pd.DataFrame:
    if not pages:
        return pd.DataFrame(columns=empty_columns)

    dfs: list[pd.DataFrame] = []
    for i, data in enumerate(pages):
        df = read_csv_safe(
            data, source=source, parser_version=parser_version, label=f"CSV pagina {i}"
        )
        if not df.empty:
            dfs.append(df)

    if not dfs:
        return pd.DataFrame(columns=empty_columns)

    return pd.concat(dfs, ignore_index=True)
