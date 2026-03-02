from __future__ import annotations

import io
from typing import Any

import pandas as pd

from agrobr.exceptions import ParseError


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
        df = pd.read_csv(io.BytesIO(data), encoding="latin-1", **kwargs)
        return df
    except Exception as e:
        raise ParseError(
            source=source,
            parser_version=parser_version,
            reason=f"Erro ao ler {label}: {e}",
        ) from e
