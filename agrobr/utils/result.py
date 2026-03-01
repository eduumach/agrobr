from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, overload

import structlog

if TYPE_CHECKING:
    import pandas as pd

logger = structlog.get_logger(__name__)


@overload
def finalize_result(
    df: pd.DataFrame,
    meta: Any = ...,
    *,
    as_polars: bool = ...,
    return_meta: Literal[True],
) -> tuple[pd.DataFrame, Any]: ...


@overload
def finalize_result(
    df: pd.DataFrame,
    meta: Any = ...,
    *,
    as_polars: bool = ...,
    return_meta: Literal[False] = ...,
) -> pd.DataFrame: ...


@overload
def finalize_result(
    df: pd.DataFrame,
    meta: Any = ...,
    *,
    as_polars: bool = ...,
    return_meta: bool = ...,
) -> pd.DataFrame | tuple[pd.DataFrame, Any]: ...


def finalize_result(
    df: pd.DataFrame,
    meta: Any = None,
    *,
    as_polars: bool = False,
    return_meta: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, Any]:
    if as_polars:
        try:
            import polars as pl

            result_df = pl.from_pandas(df)
            if return_meta:
                return result_df, meta  # type: ignore[return-value]
            return result_df  # type: ignore[return-value,no-any-return]
        except ImportError:
            logger.warning("polars_not_installed", fallback="pandas")

    if return_meta:
        return df, meta
    return df
